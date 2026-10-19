"""Necessary-condition bound for the preregistered family; no hardware release.

Choose swing leg 1, additional loss leg 2, positive y COM uncertainty, and the
+5-degree-y gravity vector. Leg 3 is the sole positive-y support. Longitudinal
stride/spread/order cannot change y moment balance. At nominal radial reach r,
its y is a+d, a=.26+sqrt(3)/2*r, common sway d. All opposite-side supports have
y <= -a+d. With total normal W and gravity-projected COM Y, equilibrium implies
N3 >= W*(Y+a-d)/(2*a). Here d<=.08 and r>=.20. Since Y-.08<0, that lower bound
is minimized at r=.20,d=.08. It still exceeds the unchanged 300 N cap.
This proves rejection within this precisely bounded, common-sway family,
not impossibility of an arbitrary redesign or a dynamic result.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import support_loss_analysis as study


def run():
    spec, c = study.frozen_inputs()
    # Explicit premises: if the baseline changes, do not silently reuse this proof.
    assert c["hips_xy_m"] == [[.24,.26],[0,.26],[-.24,.26],[-.24,-.26],[0,-.26],[.24,-.26]]
    assert c["leg_azimuth_deg"] == [60,90,120,-120,-90,-60]
    assert c["com_m"] == [0.,0.,.31]
    assert c["com_uncertainty_xy_m"] == [.04,.03]
    assert c["foot_pivot_height_m"] == .055
    theta = math.radians(5.)
    weight = c["gross_mass_kg"]*c["screening"]["load_factor"]*c["earth_gravity_m_s2"]*math.cos(theta)
    projected_y = c["com_uncertainty_xy_m"][1] + (c["com_m"][2] - c["foot_pivot_height_m"])*math.tan(theta)
    a = .26 + math.sqrt(3)/2*.20
    required = weight*(projected_y+a-.08)/(2*a)
    assert projected_y < .08
    assert required > c["screening"]["normal_force_limit_n"]
    # Verify actual registered trajectories satisfy the geometric premises.
    checks = {}
    for variant in spec["candidates"]:
        vc, order = study.configuration(c, variant)
        assert vc["nominal_radial_reach_m"] >= .20
        assert variant.get("sway_m", 0.) <= .08
        minimum = math.inf
        max_lever = 0.
        invalid = 0
        for phase, sample, swing, feet, active in study.poses(vc, variant, 100):
            for i in range(6):
                try:
                    q = study.rover.ik(vc, i, feet[i])
                    ps = study.rover.points(vc, i, q)
                    max_lever = max(max_lever, float(np.linalg.norm(ps[3]-ps[:3], axis=1).max()) + .04)
                except ValueError:
                    invalid += 1
            if swing != 0:
                continue
            assert 2 in active and all(abs(feet[i,2]-.055) < 1e-12 for i in active)
            d = feet[2,1] - (.26 + math.sqrt(3)/2*vc["nominal_radial_reach_m"])
            assert d <= .08 + 1e-12
            upper_opposite = max(feet[i,1] for i in (3,4,5))
            case_bound = weight*(projected_y-upper_opposite)/(feet[2,1]-upper_opposite)
            minimum = min(minimum, float(case_bound))
        assert minimum >= required - 1e-9
        checks[variant["id"]] = {"minimum_required_leg3_normal_n_at_registered_samples": minimum,
            "exceeds_300n_cap": minimum > c["screening"]["normal_force_limit_n"],
            "maximum_shaft_load_arm_with_original_40mm_allowance_m": max_lever,
            "original_400mm_shaft_arm_bound_satisfied": max_lever <= c["structure"]["shaft_load_eccentricity_m"] + 1e-9,
            "invalid_joint_targets": invalid}
    return {"derivation": __doc__, "total_normal_n": weight, "adversarial_projected_y_m": projected_y,
            "family_minimum_required_normal_n": required, "normal_cap_n": c["screening"]["normal_force_limit_n"],
            "verdict": "CLOSED_PROOFLIKE_UNDER_DECLARED_FAMILY_PREMISES",
            "variants": checks, "source_sha256": study.sha256(__file__), "spec_sha256": study.sha256(study.SPEC),
            "hardware_motion_allowed": False, "fabrication_released": False, "dynamic_recovery_proven": False,
            "scope": "This analytical bound was derived after baseline diagnosis, not a preregistered independent holdout. Shaft-arm audit preserves an existing engineering limit; it is not a CAD interface check."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Refusing existing output")
    args.output.write_text(json.dumps(run(), indent=2, allow_nan=False)+"\n")
