"""Offline support admission and latched fault observation. NO actuator I/O.

A static contingency pass is necessary, not sufficient for dynamic recovery.
The monitor's permit is only for an offline simulation. Hardware release is
always false: no caller-supplied flag can certify the physical catch or E-stop.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Any

import numpy as np

from models.cots_rover import allocate, gait_samples


def allocation_reasons(c: dict[str, Any], result: dict[str, Any]) -> list[str]:
    """Independently enforce the constraints outside the LP success flag."""
    if result.get("feasible") is not True:
        return ["wrench_infeasible"]
    reasons = []
    checks = {
        "support_margin_m": (c["screening"]["support_margin_required_m"], math.inf),
        "max_cop_offset_m": (0, c["foot_radius_m"] - c["screening"]["foot_cop_edge_reserve_m"]),
        "max_torque_nm": (0, c["actuator"]["design_torque_limit_nm"]),
        "max_normal_n": (0, c["screening"]["normal_force_limit_n"]),
        "force_residual_n": (0, 1e-6),
        "moment_residual_nm": (0, 1e-6),
    }
    for key, (low, high) in checks.items():
        value = result.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            reasons.append("invalid_" + key)
        elif value < low - 1e-9 or value > high + 1e-9:
            reasons.append(key)
    return reasons


def phase_preflight(c: dict[str, Any], phase: int, subdivisions: int = 4, slope_deg: float = 5.0):
    """Check one complete generated phase and each extra supporting-foot loss.

    No arbitrary partial sample list or caller-declared 'safe' boolean is accepted.
    This sampled necessary-condition check never authorizes hardware operation.
    """
    if type(phase) is not int or phase not in range(6):
        raise ValueError("Phase must be an integer in 0..5")
    if type(subdivisions) is not int or subdivisions < 4:
        raise ValueError("At least four subdivisions are required")
    if isinstance(slope_deg, bool) or not math.isfinite(slope_deg) or not 0 <= slope_deg <= 5:
        raise ValueError("Commissioning slope must be finite and in 0..5 degrees")
    dx, dy = c["com_uncertainty_xy_m"]
    coms = [np.array(c["com_m"]) + [x, y, 0] for x, y in itertools.product((-dx, dx), (-dy, dy))]
    angle = math.radians(slope_deg)
    g = c["earth_gravity_m_s2"]
    gravities = [np.array([0.0, 0.0, -g])]
    gravities += [
        g * np.array([math.sin(angle) * math.cos(h), math.sin(angle) * math.sin(h), -math.cos(angle)])
        for h in np.linspace(0, 2 * math.pi, 8, endpoint=False)
    ]
    counts = {"nominal_cases": 0, "nominal_rejected": 0, "loss_cases": 0, "loss_rejected": 0}
    first_failure = None
    poses = 0
    for name, feet, active in gait_samples(c, subdivisions):
        if not name.startswith(f"phase{phase}_"):
            continue
        poses += 1
        for lost in (None, *active):
            supports = active if lost is None else tuple(i for i in active if i != lost)
            family = "nominal" if lost is None else "loss"
            for com, gravity in itertools.product(coms, gravities):
                counts[family + "_cases"] += 1
                result = allocate(c, feet, supports, com, gravity, c["screening"]["load_factor"])
                reasons = allocation_reasons(c, result)
                if reasons:
                    counts[family + "_rejected"] += 1
                    if first_failure is None:
                        first_failure = {
                            "pose": name,
                            "lost_leg_1based": None if lost is None else lost + 1,
                            "com_m": com.tolist(),
                            "gravity_m_s2": gravity.tolist(),
                            "reasons": reasons,
                        }
    if poses != subdivisions + 1 or counts["nominal_cases"] != poses * 36 or counts["loss_cases"] != poses * 180:
        raise ValueError("Incomplete preflight: missing poses or load cases")
    return {
        "phase": phase,
        **counts,
        "nominal_static_pass": counts["nominal_rejected"] == 0,
        "single_loss_static_contingency_pass": counts["nominal_rejected"] == counts["loss_rejected"] == 0,
        "hardware_motion_allowed": False,
        "dynamic_recovery_proven": False,
        "first_failure": first_failure,
    }


@dataclass(frozen=True)
class Snapshot:
    now_s: float
    contacts: tuple[bool, ...]
    motor_age_ms: tuple[float, ...]
    contact_age_ms: tuple[float, ...]
    heartbeat_age_ms: float
    feedback_valid: bool


class SupportMonitor:
    """Stateful synthetic/test monitor. It neither releases nor commands hardware.

    Expected contact changes must be declared before the foot leaves the ground.
    Faults remain latched when feedback returns. Rearm requires an explicit call
    while the external restraint is confirmed and all six contacts are valid.
    Confirmation is a test input, not evidence that the real restraint is safe.
    """

    def __init__(self):
        self.state = "DISARMED"
        self.swing_leg: int | None = None
        self.last_time: float | None = None
        self.reason = "not_armed"

    def _validate(self, s: Snapshot) -> str | None:
        if type(s.feedback_valid) is not bool or not s.feedback_valid:
            return "invalid_feedback"
        if not isinstance(s.contacts, tuple) or len(s.contacts) != 6 or any(type(x) is not bool for x in s.contacts):
            return "invalid_contact_states"
        if not isinstance(s.motor_age_ms, tuple) or not isinstance(s.contact_age_ms, tuple):
            return "invalid_feedback_channels"
        if len(s.motor_age_ms) != 18 or len(s.contact_age_ms) != 6:
            return "missing_feedback_channels"
        values = (s.now_s, s.heartbeat_age_ms, *s.motor_age_ms, *s.contact_age_ms)
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in values):
            return "invalid_timing"
        if self.last_time is not None and s.now_s <= self.last_time:
            return "clock_not_increasing"
        self.last_time = s.now_s
        if max(s.motor_age_ms) >= 40 or max(s.contact_age_ms) >= 40:
            return "stale_feedback"
        if s.heartbeat_age_ms >= 100:
            return "heartbeat_timeout"
        return None

    def _fault(self, reason: str):
        self.state = "FAULT_LATCHED"
        self.reason = reason
        return self.output()

    def output(self):
        return {
            "state": self.state,
            "reason": self.reason,
            "offline_sequence_permitted": self.state in ("READY", "SWING"),
            "hardware_motion_allowed": False,
            "automatic_recovery_allowed": False,
            "advance_inhibited": self.state not in ("READY", "SWING"),
            "response": "EXTERNAL_RESTRAINT_REQUIRED" if self.state == "FAULT_LATCHED" else "OFFLINE_ONLY",
        }

    def arm(self, s: Snapshot, *, restraint_confirmed: bool = False):
        error = self._validate(s)
        if error:
            return self._fault(error)
        if restraint_confirmed is not True or not all(s.contacts):
            return self._fault("rearm_requires_restraint_and_six_contacts")
        if self.state in ("READY", "SWING"):
            return self._fault("cannot_rearm_active_sequence")
        self.state, self.swing_leg, self.reason = "READY", None, "six_contacts_confirmed"
        return self.output()

    def observe(self, s: Snapshot, *, swing_leg: int | None = None):
        if self.state == "FAULT_LATCHED":
            self._validate(s)  # Keep clock history while preserving the original fault.
            return self.output()  # Healthy packets never clear a latched fault.
        error = self._validate(s)
        if error:
            return self._fault(error)
        if self.state == "DISARMED":
            return self.output()
        if swing_leg is not None and (type(swing_leg) is not int or swing_leg not in range(6)):
            return self._fault("invalid_swing_leg")
        # Enforce previous expected supports before accepting a changed plan.
        if any(not s.contacts[i] for i in range(6) if i != self.swing_leg):
            return self._fault("support_contact_lost")
        if swing_leg != self.swing_leg:
            if self.swing_leg is not None and swing_leg is not None:
                return self._fault("swing_switch_without_six_contact_transfer")
            if not all(s.contacts):
                return self._fault("transfer_requires_six_contacts")
        self.swing_leg = swing_leg
        self.state = "READY" if swing_leg is None else "SWING"
        self.reason = "expected_supports_present"
        return self.output()
