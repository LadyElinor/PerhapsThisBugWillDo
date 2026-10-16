"""Run preregistered COTS robustness tests, retaining negative results.

A completed experiment is not a passing hardware design. Exit success means the
experiment and controls completed; individual hypotheses have explicit verdicts.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from models.cots_rover import allocate, gait_samples, load_config

SPEC = Path(__file__).with_name("tranche_02") / "spec.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_spec(path: Path = SPEC) -> dict[str, Any]:
    spec = json.loads(path.read_text())
    for name, expected in spec["frozen_inputs_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Frozen input changed: {name}. Define a new experiment instead of silently refitting.")
    return spec


def profile_config(baseline, profile):
    c = copy.deepcopy(baseline)
    if "gross_mass_kg" in profile:
        c["gross_mass_kg"] = profile["gross_mass_kg"]
    if "friction" in profile:
        c["screening"]["friction_coefficient_assumption"] = profile["friction"]
    c["actuator"]["design_torque_limit_nm"] *= profile.get("torque_scale", 1)
    c["com_m"][2] += profile.get("com_z_increment_m", 0)
    for k in c["leg_mass_proxies"]:
        c["leg_mass_proxies"][k] *= profile.get("leg_mass_scale", 1)
    return c


def loads(c, slope_deg):
    dx, dy = c["com_uncertainty_xy_m"]
    coms = [np.array(c["com_m"]) + [x, y, 0] for x, y in itertools.product((-dx, dx), (-dy, dy))]
    g = c["earth_gravity_m_s2"]
    a = math.radians(slope_deg)
    gravity = [np.array([0.0, 0.0, -g])]
    gravity += [
        g * np.array([math.sin(a) * math.cos(h), math.sin(a) * math.sin(h), -math.cos(a)])
        for h in np.linspace(0, 2 * math.pi, 8, endpoint=False)
    ]
    return itertools.product(coms, gravity)


def screen(c, samples, slope_deg, remove_one=False):
    counts = {"cases": 0, "infeasible_wrench": 0, "margin_below_requirement": 0, "cop_outside_pad": 0, "accepted": 0}
    minimum_margin = math.inf
    worst_torque = 0.0
    worst_normal = 0.0
    worst_residual = 0.0
    failed_examples = []
    failure_by_lost_leg = {str(i + 1): 0 for i in range(6)} if remove_one else {}
    for pose, feet, active in samples:
        supports = (
            [(tuple(i for i in active if i != lost), lost) for lost in active] if remove_one else [(active, None)]
        )
        for support, lost in supports:
            for com, gravity in loads(c, slope_deg):
                counts["cases"] += 1
                out = allocate(c, feet, support, com, gravity, c["screening"]["load_factor"])
                reasons = []
                margin = out["support_margin_m"]
                minimum_margin = min(minimum_margin, margin)
                if margin < c["screening"]["support_margin_required_m"] - 1e-9:
                    counts["margin_below_requirement"] += 1
                    reasons.append("support_margin")
                if not out["feasible"]:
                    counts["infeasible_wrench"] += 1
                    reasons.append("wrench_infeasible")
                else:
                    worst_torque = max(worst_torque, out["max_torque_nm"])
                    worst_normal = max(worst_normal, out["max_normal_n"])
                    worst_residual = max(worst_residual, out["force_residual_n"], out["moment_residual_nm"])
                    if out["max_cop_offset_m"] > c["foot_radius_m"] - c["screening"]["foot_cop_edge_reserve_m"] + 1e-9:
                        counts["cop_outside_pad"] += 1
                        reasons.append("cop")
                if not reasons:
                    counts["accepted"] += 1
                elif lost is not None:
                    failure_by_lost_leg[str(lost + 1)] += 1
                if reasons and len(failed_examples) < 12:
                    failed_examples.append(
                        {
                            "pose": pose,
                            "lost_leg_1based": None if lost is None else lost + 1,
                            "active_legs_1based": [x + 1 for x in support],
                            "com_m": com.tolist(),
                            "gravity_m_s2": gravity.tolist(),
                            "reasons": reasons,
                            "support_margin_m": margin,
                        }
                    )
    if worst_residual > 1e-6:
        raise ValueError("Contact solver returned an invalid equilibrium")
    return {
        "verdict": "RETAIN" if counts["accepted"] == counts["cases"] else "CLOSED_UNDER_TESTED_SPECIFICATION",
        **counts,
        "rejection_count": counts["cases"] - counts["accepted"],
        "minimum_support_margin_m": minimum_margin,
        "largest_feasible_torque_bound_nm": worst_torque,
        "largest_feasible_normal_n": worst_normal,
        "maximum_equilibrium_residual": worst_residual,
        "failure_by_lost_leg": failure_by_lost_leg,
        "failure_examples": failed_examples,
    }


def controls(c):
    _, feet, active = next(gait_samples(c))
    outside = allocate(c, feet, active, np.array([2.0, 0.0, 0.3]), np.array([0.0, 0.0, -9.80665]))
    d = copy.deepcopy(c)
    d["screening"]["friction_coefficient_assumption"] = 0
    frictionless = allocate(d, feet, active, np.array(c["com_m"]), np.array([1.0, 0.0, -9.80665]))
    result = {
        "outside_support_rejected": not outside["feasible"],
        "frictionless_slope_rejected": not frictionless["feasible"],
    }
    if not all(result.values()):
        raise ValueError(f"Negative controls failed: {result}")
    return result


def run(spec_path: Path, output: Path):
    spec = frozen_spec(spec_path)
    baseline = load_config()
    report = {
        "experiment_id": spec["id"],
        "baseline_commit": spec["baseline_commit"],
        "spec_sha256": sha256(spec_path),
        "runner_sha256": sha256(Path(__file__)),
        "controls": controls(baseline),
        "profiles": {},
        "hardware_validated": False,
    }
    subdivisions = spec["common"]["gait_subdivisions"]
    for profile in spec["profiles"]:
        c = profile_config(baseline, profile)
        result = screen(c, gait_samples(c, subdivisions), profile["slope_deg"])
        report["profiles"][profile["id"]] = {"parameters": profile, **result}
        print(profile["id"], result["verdict"], f"{result['accepted']}/{result['cases']}", flush=True)
    dense = spec["dense_interpolation"]
    unseen = [
        (name, feet, active)
        for name, feet, active in gait_samples(baseline, dense["subdivisions"])
        if int(name.split("sample")[1]) % 2 == 1
    ]
    report["dense_interpolation"] = screen(baseline, unseen, dense["slope_deg"])
    print("dense_interpolation", report["dense_interpolation"]["verdict"], flush=True)
    report["support_loss"] = screen(
        baseline, gait_samples(baseline, subdivisions), spec["contact_loss"]["slope_deg"], True
    )
    print("support_loss", report["support_loss"]["verdict"], flush=True)
    report["interpretation"] = [
        "Profile rejection means that the universal claim fails on at least one sampled case; it is not a physical failure rate.",
        "Largest feasible torque/normal omit infeasible cases; they must not be used to size a rejected profile.",
        "Support loss examines instantaneous static equilibrium, not contact-loss dynamics or a recovery controller.",
        "Dense new sample positions were fixed before scoring; no parameters were fitted and no physical holdout measurements exist.",
        "All values remain conditional on geometry, idealized contacts, gravity proxies and the friction pyramid.",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=SPEC)
    parser.add_argument("--output", type=Path, default=SPEC.with_name("robustness.json"))
    args = parser.parse_args()
    run(args.spec, args.output)
