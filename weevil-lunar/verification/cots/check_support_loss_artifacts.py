"""Check complete ledgers and compare reruns without requiring bit-identical floats."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path

import numpy as np

import run_support_loss_01 as runner
import support_loss_analysis as study


def compare(a, b, path="root"):
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            raise ValueError(f"Different keys at {path}")
        for key in a:
            compare(a[key], b[key], f"{path}.{key}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise ValueError(f"Different lengths at {path}")
        for i, (left, right) in enumerate(zip(a, b)):
            compare(left, right, f"{path}[{i}]")
    elif type(a) is float or type(b) is float:
        if not np.isclose(a, b, rtol=1e-9, atol=1e-9):
            raise ValueError(f"Different numeric result at {path}: {a}, {b}")
    elif a != b:
        raise ValueError(f"Different result at {path}: {a}, {b}")


def run(directory, compare_committed=False):
    r = json.loads((directory / "results.json").read_text())
    spec, base = study.frozen_inputs()
    if r.get("complete") is not True or not all(r["controls"].values()):
        raise ValueError("Incomplete experiment or failed controls")
    if r["spec_sha256"] != study.sha256(study.SPEC):
        raise ValueError("Specification hash mismatch")
    for filename, expected in r["source_sha256"].items():
        if study.sha256(study.SPEC.parent.parent / filename) != expected:
            raise ValueError("Runner source hash mismatch")
    for key, filename in (("raw_cases_sha256", "cases.csv.gz"), ("poses_sha256", "poses.json")):
        if study.sha256(directory / filename) != r[key]:
            raise ValueError(f"Artifact hash mismatch: {filename}")
    for key in ("hardware_motion_allowed", "fabrication_released", "dynamic_recovery_proven", "automatic_recovery_allowed"):
        if r[key] is not False:
            raise ValueError("Invalid hardware release")
    if r["independent_encoding_disagreements"] != 0:
        raise ValueError("Encoding disagreement")
    if [v["parameters"] for v in r["variants"]] != spec["candidates"]:
        raise ValueError("Candidate registry mismatch")
    rows = {v["id"]: {} for v in r["variants"]}
    with gzip.open(directory / "cases.csv.gz", "rt") as f:
        for row in csv.DictReader(f):
            keyparts = row["scenario"].split("|")
            key = (*map(int, keyparts[:5]), keyparts[5])
            name = row["variant"]
            if key in rows[name] or row["accepted"] not in ("0", "1") or row["lp_feasible"] not in ("0", "1"):
                raise ValueError("Duplicate or malformed row")
            for field in ("phase", "sample", "swing_leg_1based", "com_sign_x", "com_sign_y", "accepted", "lp_feasible"):
                row[field] = int(row[field])
            for field in ("margin_m", "slope_deg", *runner.FIELDS[-4:]):
                if row[field] != "":
                    row[field] = float(row[field])
                    if not np.isfinite(row[field]):
                        raise ValueError("Nonfinite metric")
            for field in ("lost_leg_1based", "heading_deg"):
                if row[field] != "":
                    row[field] = int(row[field])
            if bool(row["accepted"]) != (not row["reasons"]):
                raise ValueError("Contradictory acceptance label")
            if (row["swing_leg_1based"]-1, row["sample"], -1 if row["lost_leg_1based"] == "" else row["lost_leg_1based"]-1,
                row["com_sign_x"], row["com_sign_y"]) != key[:5]:
                raise ValueError("Scenario/metadata mismatch")
            rows[name][key] = row
    baseline_rows = rows["baseline"]
    poses = json.loads((directory / "poses.json").read_text())
    for v in r["variants"]:
        name = v["id"]
        if v["static_cases_executed"] == 0:
            if rows[name] or v["kinematics"]["pass"] or v["static_cases_unexecuted"] != 6480:
                raise ValueError("Incorrect unexecuted status")
            continue
        summary = runner.summarize(rows[name], None if name == "baseline" else baseline_rows)
        for key, expected in summary.items():
            compare(expected, v[key], f"{name}.{key}")
        c, _ = study.configuration(base, v["parameters"])
        compare(c, v["effective_config"], name+".config")
        generated = list(study.poses(c, v["parameters"]))
        if len(poses[name]) != len(generated):
            raise ValueError("Incomplete poses")
        for saved, (phase, sample, swing, feet, active) in zip(poses[name], generated):
            if (saved["phase"], saved["sample"], saved["swing_leg_1based"]) != (phase, sample, swing+1):
                raise ValueError("Pose identity mismatch")
            np.testing.assert_allclose(saved["feet_m"], feet, atol=1e-12, rtol=0)
            assert saved["active_legs_1based"] == [i+1 for i in active]
    certfile = directory / "planar_certificates.json.gz"
    with gzip.open(certfile, "rt") as f:
        certificates = json.load(f)
    if certificates["disagreements"] or len(certificates["certificates"]) != 5400:
        raise ValueError("Incomplete or inconsistent planar certificates")
    if certificates["comparison_results_sha256"] != study.sha256(directory / "results.json"):
        raise ValueError("Certificate input hash mismatch")
    if certificates["source_sha256"] != study.sha256(study.SPEC.parent.parent / "explain_support_loss.py"):
        raise ValueError("Certificate source hash mismatch")
    family = json.loads((directory / "family_bound.json").read_text())
    if family["source_sha256"] != study.sha256(study.SPEC.parent.parent / "check_support_family_bound.py"):
        raise ValueError("Family bound source hash mismatch")
    if family["family_minimum_required_normal_n"] <= family["normal_cap_n"]:
        raise ValueError("Family bound does not reject")
    if compare_committed:
        old = json.loads(study.SPEC.with_name("results.json").read_text())
        # Versions, hashes and detailed force-utilization witnesses may vary by solver build.
        # Decisions, dimensions, minimal group conflicts, paired transitions and kinematics must not.
        for left, right in zip(r["variants"], old["variants"]):
            for key in ("id", "parameters", "effective_config", "status", "kinematics", "static_cases_executed",
                        "static_cases_unexecuted", "complete_sampled_static_pass", "counts", "phases",
                        "loss_breakdowns", "paired_loss_outcomes", "minimum_loss_margin_m"):
                if key in left or key in right:
                    compare(left.get(key), right.get(key), f"rerun.{left['id']}.{key}")
    print(f"PASS: {sum(map(len, rows.values()))} case rows; complete paired coverage and diagnostic integrity")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--compare-committed", action="store_true")
    args = parser.parse_args()
    run(args.results_dir, args.compare_committed)
