"""Additive offline witness/contact audit. No actuator I/O or release authority.

The original model and guard remain frozen. Success summaries from an imported
solver cannot substitute for a force witness. Contact evidence here is synthetic
input; this module does not validate a physical sensor or recovery mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from models import cots_rover as rover

TOL = 1e-6


def support_indices(active):
    if (not isinstance(active, (tuple, list)) or not 3 <= len(active) <= 6
            or any(type(i) is not int or i not in range(6) for i in active)
            or len(set(active)) != len(active)):
        raise ValueError("Invalid support identities")
    return tuple(active)


def audit_allocation(c, feet, active, com, gravity, result):
    """Recompute constraints from forces, not the solver's claimed maxima.

Shares the frozen kinematics/gravity model; independent of LP row assembly.
Infeasibility is denied, never reinterpreted as a physical failure probability.
"""
    active = support_indices(active)
    feet, com, gravity = (np.asarray(x, dtype=float) for x in (feet, com, gravity))
    if (feet.shape != (6, 3) or com.shape != (3,) or gravity.shape != (3,)
            or not all(np.isfinite(x).all() for x in (feet, com, gravity)) or gravity[2] >= 0):
        raise ValueError("Invalid witness geometry or gravity")
    if not isinstance(result, dict) or result.get("feasible") is not True:
        return {"accepted": False, "reasons": ["wrench_infeasible"], "hardware_motion_allowed": False}
    reasons = []
    claimed_active = result.get("active")
    if (not isinstance(claimed_active, (list, tuple))
            or any(type(i) is not int for i in claimed_active) or tuple(claimed_active) != active):
        reasons.append("witness_support_identities")
    try:
        forces = np.asarray(result["forces_n"], dtype=float)
    except (KeyError, ValueError, TypeError):
        forces = np.empty((0, 3))
    if forces.shape != (len(active), 3) or not np.isfinite(forces).all():
        return {"accepted": False, "reasons": reasons + ["invalid_force_witness"], "hardware_motion_allowed": False}
    g = gravity * c["screening"]["load_factor"]
    force_residual = float(np.linalg.norm(forces.sum(axis=0) + c["gross_mass_kg"] * g))
    moment_residual = float(np.linalg.norm(np.cross(feet[list(active)] - com, forces).sum(axis=0)))
    mu = c["screening"]["friction_coefficient_assumption"]
    cap = c["screening"]["normal_force_limit_n"]
    limit = c["actuator"]["design_torque_limit_nm"]
    if np.min(forces[:, 2]) < -TOL:
        reasons.append("unilateral_normal")
    if np.max(np.abs(forces[:, 0]) + np.abs(forces[:, 1]) - mu * forces[:, 2]) > TOL:
        reasons.append("friction_pyramid")
    torques = []
    for i, f in zip(active, forces):
        q = rover.ik(c, i, feet[i])
        torques.append(np.abs(rover.jacobian(c, i, q).T @ f) + rover.gravity_torque_bound(c, i, q, g))
    torque = np.asarray(torques)
    cop = np.zeros(len(active))
    for j, f in enumerate(forces):
        if f[2] > 1e-8:
            cop[j] = c["foot_pivot_height_m"] * np.linalg.norm(f[:2]) / f[2]
        elif np.linalg.norm(f[:2]) > TOL:
            reasons.append("cop_without_normal_support")
    metrics = {
        "force_residual_n": force_residual,
        "moment_residual_nm": moment_residual,
        "max_torque_nm": float(torque.max()),
        "max_normal_n": float(forces[:, 2].max()),
        "max_cop_offset_m": float(cop.max()),
        "support_margin_m": rover.support_margin(feet[list(active)], com, gravity),
    }
    upper = {"force_residual_n": TOL, "moment_residual_nm": TOL, "max_torque_nm": limit,
             "max_normal_n": cap, "max_cop_offset_m": c["foot_radius_m"] - c["screening"]["foot_cop_edge_reserve_m"]}
    for key, maximum in upper.items():
        if metrics[key] > maximum + (1e-9 if "residual" not in key else 0.):
            reasons.append(key)
    if metrics["support_margin_m"] < c["screening"]["support_margin_required_m"] - 1e-9:
        reasons.append("support_margin_m")
    for key, actual in metrics.items():
        supplied = result.get(key)
        if (type(supplied) not in (int, float) or not math.isfinite(supplied)
                or not math.isfinite(actual) or abs(supplied - actual) > 1e-8):
            reasons.append("misreported_" + key)
    reported_torque = np.asarray(result.get("torque_bounds_nm", []), dtype=float)
    if (reported_torque.shape != torque.shape or not np.isfinite(reported_torque).all()
            or not np.allclose(reported_torque, torque, atol=1e-8, rtol=0)):
        reasons.append("misreported_torque_bounds")
    peak = result.get("peak_utilization")
    actual_peak = max(metrics["max_torque_nm"] / limit, metrics["max_normal_n"] / cap)
    if (type(peak) not in (int, float) or not math.isfinite(peak) or peak > 1 + 1e-9
            or peak < actual_peak - 1e-8):
        reasons.append("misreported_peak_utilization")
    return {"accepted": not reasons, "reasons": sorted(set(reasons)), "metrics": metrics,
            "hardware_motion_allowed": False, "dynamic_recovery_proven": False}


@dataclass(frozen=True)
class ContactEvidence:
    touching: bool
    load_confirmed: bool
    slipping: bool
    age_ms: float


def assess_support_evidence(c, planned_active, observations):
    """A planned touchdown is insufficient; require fresh, corroborated inputs.

All inputs are supplied test evidence. A true load_confirmed bit is not a
validated physical detector. The result can only constrain offline analysis.
"""
    active = support_indices(planned_active)
    if not isinstance(observations, (tuple, list)) or len(observations) != 6:
        raise ValueError("Six contact evidence records required")
    reasons, usable = [], []
    for i, o in enumerate(observations):
        if (not isinstance(o, ContactEvidence)
                or any(type(v) is not bool for v in (o.touching, o.load_confirmed, o.slipping))
                or type(o.age_ms) not in (int, float) or not math.isfinite(o.age_ms) or o.age_ms < 0):
            raise ValueError("Malformed contact evidence")
        faults = []
        if not o.touching: faults.append("no_contact")
        if not o.load_confirmed: faults.append("load_unconfirmed")
        if o.slipping: faults.append("suspected_slip")
        if o.age_ms >= c["control"]["motor_feedback_stale_ms"]: faults.append("stale_contact")
        if i in active:
            reasons.extend(f"leg{i+1}:{reason}" for reason in faults)
            if not faults: usable.append(i)
    return {"evidence_sufficient_for_offline_analysis": not reasons, "usable_supports": usable,
            "reasons": reasons, "hardware_motion_allowed": False, "automatic_recovery_allowed": False}
