"""Run the frozen support-loss comparison into a NEW output directory."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import io
import json
import platform
from pathlib import Path

import numpy as np
import scipy

import support_loss_analysis as study

FIELDS = ("variant", "scenario", "phase", "sample", "swing_leg_1based", "lost_leg_1based",
          "com_sign_x", "com_sign_y", "slope_deg", "heading_deg", "accepted", "lp_feasible",
          "reasons", "margin_m", "edge_legs_1based", "conflict_groups",
          "peak_utilization", "max_torque_nm", "max_normal_n", "max_cop_offset_m")


def check_coverage(rows):
    expected = {(swing, sample, lost, sx, sy, gid)
                for swing in range(6) for sample in range(5)
                for lost in (-1, *[i for i in range(6) if i != swing])
                for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1))
                for gid in ("flat", *[f"slope5_heading{h}" for h in range(0, 360, 45)])}
    if len(rows) != 6480 or set(rows) != expected:
        raise ValueError("Incomplete or duplicated scenario coverage")


def summarize(rows, base_rows=None):
    check_coverage(rows)
    groups = {k: defaultdict(lambda: Counter(cases=0, rejected=0)) for k in
              ("phase", "lost_leg", "swing_lost_pair", "sample", "com_corner", "gravity", "reason", "conflict")}
    counts = Counter(nominal_cases=0, nominal_rejected=0, loss_cases=0, loss_rejected=0)
    phase = {str(p): Counter(nominal_cases=0, nominal_rejected=0, loss_cases=0, loss_rejected=0) for p in range(6)}
    paired = Counter(rescued=0, regressed=0, both_reject=0, both_pass=0)
    min_margin = float("inf")
    witness = {}
    for key, row in rows.items():
        loss = key[2] != -1
        family = "loss" if loss else "nominal"
        rejected = int(not row["accepted"])
        counts[family + "_cases"] += 1
        counts[family + "_rejected"] += rejected
        phase[str(row["phase"])][family + "_cases"] += 1
        phase[str(row["phase"])][family + "_rejected"] += rejected
        if not loss:
            continue
        min_margin = min(min_margin, row["margin_m"])
        dimensions = {"phase": str(row["phase"]), "lost_leg": str(key[2]+1),
                      "swing_lost_pair": f"{key[0]+1},{key[2]+1}", "sample": str(key[1]),
                      "com_corner": f"{key[3]},{key[4]}", "gravity": key[5]}
        for dimension, value in dimensions.items():
            groups[dimension][value].update(cases=1, rejected=rejected)
        for reason in row["reasons"].split(";") if row["reasons"] else []:
            groups["reason"][reason].update(cases=1, rejected=rejected)
        if row["conflict_groups"]:
            groups["conflict"][row["conflict_groups"]].update(cases=1, rejected=rejected)
            witness.setdefault(row["conflict_groups"], row)
        if base_rows is not None:
            before, after = base_rows[key]["accepted"], row["accepted"]
            label = ("both_pass" if after else "regressed") if before else ("rescued" if after else "both_reject")
            paired[label] += 1
    return {"counts": dict(counts), "phases": phase, "loss_breakdowns": groups,
            "paired_loss_outcomes": dict(paired) if base_rows is not None else None,
            "minimum_loss_margin_m": min_margin, "first_conflict_examples": witness,
            "complete_sampled_static_pass": counts["nominal_rejected"] == counts["loss_rejected"] == 0}


def run(output):
    if output.exists():
        raise ValueError("Refusing existing output directory; preserve earlier results")
    spec, base = study.frozen_inputs()
    controls = study.controls(base)
    # Exact default-generator parity before scoring or modifying a configuration.
    original = list(study.rover.gait_samples(base, 4))
    for old, new in zip(original, study.poses(base, {"id": "baseline"})):
        if old[2] != new[4] or not np.allclose(old[1], new[3], rtol=0, atol=1e-14):
            raise ValueError("Default generator parity failure")
    output.mkdir(parents=True)
    report = {"experiment_id": spec["id"], "spec_sha256": study.sha256(study.SPEC),
              "frozen_inputs_sha256": spec["frozen_inputs_sha256"],
              "source_sha256": {p.name: study.sha256(p) for p in (Path(__file__), Path(study.__file__))},
              "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
              "controls": controls, "variants": [], "experiments_unexecuted": spec["unexecuted_scope"],
              "hardware_motion_allowed": False, "fabrication_released": False,
              "dynamic_recovery_proven": False, "automatic_recovery_allowed": False,
              "independent_encoding_disagreements": 0}
    baseline_rows = None
    poses_record = {}
    csv_path = output / "cases.csv.gz"
    with csv_path.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        with io.TextIOWrapper(gz, newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            for variant in spec["candidates"]:
                name = variant["id"]
                c, order = study.configuration(base, variant)
                kin = study.kinematic_screen(c, variant)
                result = {"id": name, "parameters": variant, "effective_config": c,
                          "swing_order_1based": [i+1 for i in order], "kinematics": kin,
                          "hardware_motion_allowed": False, "dynamic_recovery_proven": False}
                if not kin["pass"]:
                    result.update(status="KINEMATICALLY_REJECTED_STATICS_UNEXECUTED", static_cases_executed=0,
                                  static_cases_unexecuted=6480, complete_sampled_static_pass=False)
                    report["variants"].append(result)
                    print(name, result["status"], kin["checks"], flush=True)
                    continue
                rows = {}
                poses_record[name] = []
                for phase, sample, swing, feet, active in study.poses(c, variant):
                    poses_record[name].append({"phase": phase, "sample": sample, "swing_leg_1based": swing+1,
                                               "feet_m": feet.tolist(), "active_legs_1based": [i+1 for i in active]})
                    for lost in (-1, *active):
                        supports = active if lost == -1 else tuple(i for i in active if i != lost)
                        for sx, sy, gid, slope, heading, com, gravity in study.load_cases(c):
                            key = (swing, sample, lost, sx, sy, gid)
                            if key in rows:
                                raise ValueError("Duplicate scenario")
                            out = study.case_result(c, feet, supports, com, gravity, diagnose=True)
                            allocation = out["allocation"]
                            row = {"variant": name, "scenario": "|".join(map(str, key)),
                                   "phase": phase, "sample": sample, "swing_leg_1based": swing+1,
                                   "lost_leg_1based": "" if lost == -1 else lost+1,
                                   "com_sign_x": sx, "com_sign_y": sy, "slope_deg": slope,
                                   "heading_deg": "" if heading is None else heading,
                                   "accepted": int(out["accepted"]), "lp_feasible": int(allocation["feasible"]),
                                   "reasons": ";".join(out["reasons"]), "margin_m": out["margin_m"],
                                   "edge_legs_1based": ";".join(map(str, out["limiting_edge_1based"])),
                                   "conflict_groups": ";".join(out["conflict"])}
                            row.update({k: allocation.get(k, "") for k in FIELDS[-4:]})
                            rows[key] = row
                            writer.writerow(row)
                    if sample == 4:
                        print(name, "phase", phase, "complete", flush=True)
                result.update(summarize(rows, baseline_rows))
                result["static_cases_executed"], result["static_cases_unexecuted"] = len(rows), 0
                if name == "baseline":
                    expected = [542, 540, 368, 383, 544, 548]
                    if ([result["phases"][str(p)]["loss_rejected"] for p in range(6)] != expected
                            or result["counts"]["nominal_rejected"] != 0):
                        raise ValueError("Frozen baseline reproduction failure")
                    baseline_rows = rows
                    report["controls"]["frozen_baseline_exact_counts"] = True
                elif baseline_rows is None:
                    raise ValueError("Baseline must execute before variants")
                if variant.get("kind") == "negative_control":
                    if result["complete_sampled_static_pass"]:
                        raise ValueError("Negative zero-stride control unexpectedly passed")
                    report["controls"]["zero_stride_negative"] = True
                    result["status"] = "NEGATIVE_CONTROL_REJECTED"
                else:
                    result["status"] = "SAMPLED_STATIC_PASS_ONLY" if result["complete_sampled_static_pass"] else "CLOSED_UNDER_TESTED_SPECIFICATION"
                report["variants"].append(result)
                # A checkpoint is explicitly incomplete; a crash cannot masquerade as a final report.
                (output / "checkpoint.json").write_text(json.dumps({**report, "complete": False}, indent=2, allow_nan=False) + "\n")
                print(name, result["counts"], flush=True)
    if len(report["variants"]) != len(spec["candidates"]) or not all(report["controls"].values()):
        raise ValueError("Incomplete experiment or failed controls")
    report["complete"] = True
    report["raw_cases_sha256"] = study.sha256(csv_path)
    (output / "poses.json").write_text(json.dumps(poses_record, indent=2, allow_nan=False) + "\n")
    report["poses_sha256"] = study.sha256(output / "poses.json")
    (output / "results.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (output / "checkpoint.json").unlink()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
