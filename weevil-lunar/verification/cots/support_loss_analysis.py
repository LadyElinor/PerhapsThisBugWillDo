"""Preregistered offline support-loss diagnostics; never actuator I/O.

The frozen allocator remains the acceptance authority, supplemented by an
independent force-only LP and explicit witness checks. Diagnostic row deletions
explain infeasibility only; they cannot admit a candidate.
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from models import cots_rover as rover
from models.cots_support_guard import allocation_reasons

SPEC = Path(__file__).with_name("support_loss_01") / "spec.json"
GROUPS = ("friction", "normal_cap", "yaw_torque", "pitch_torque", "knee_torque")
TOL = 1e-6


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_inputs(path=SPEC):
    spec = json.loads(Path(path).read_text())
    for name, expected in spec["frozen_inputs_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Frozen input changed: {name}")
    report = json.loads((ROOT / "verification/cots/tranche_03/results.json").read_text())
    return spec, report["config"]


def configuration(base, variant):
    """Whitelist variant changes; no route to changing engineering limits."""
    allowed = {"id", "kind", "reach_m", "stride_m", "spread_m", "sway_m", "order"}
    if set(variant) - allowed:
        raise ValueError("Undeclared candidate parameter")
    c = copy.deepcopy(base)
    for key, low, high in (("reach_m", .20, .28), ("stride_m", 0, .06),
                          ("spread_m", 0, .03), ("sway_m", 0, .08)):
        if key in variant:
            value = variant[key]
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"Invalid bounded parameter {key}")
    if "reach_m" in variant:
        c["nominal_radial_reach_m"] = variant["reach_m"]
    if "stride_m" in variant:
        c["screening"]["step_length_m"] = variant["stride_m"]
    order = variant.get("order", [0, 3, 1, 4, 2, 5])
    if (not isinstance(order, (tuple, list)) or len(order) != 6
            or any(type(i) is not int for i in order) or set(order) != set(range(6))):
        raise ValueError("Order must be a permutation of six legs")
    return c, tuple(order)


def smooth(t):
    return t**3 * (10 - 15 * t + 6 * t * t)


def poses(c, variant, subdivisions=4):
    if type(subdivisions) is not int or subdivisions < 4:
        raise ValueError("At least four subdivisions required")
    _, order = configuration(c, variant)
    nominal = rover.nominal_feet(c)
    nominal[:, 0] += variant.get("spread_m", 0) * np.sign(np.array(c["hips_xy_m"])[:, 0])
    length = c["screening"]["step_length_m"]
    advance = length / 5
    directions = np.array([[math.cos(math.radians(a)), math.sin(math.radians(a))]
                           for a in c["leg_azimuth_deg"]])
    for phase, lifted in enumerate(order):
        for sample in range(subdivisions + 1):
            u = sample / subdivisions
            t = smooth(u)
            feet = nominal.copy()
            for rank, i in enumerate(order):
                if rank < phase:
                    feet[i, 0] += length / 2 - (phase - rank - 1 + t) * advance
                elif rank > phase:
                    feet[i, 0] += -length / 2 + (rank - phase - t) * advance
                else:
                    feet[i, 0] += -length / 2 + length * t
                    feet[i, 2] += c["screening"]["step_height_m"] * math.sin(math.pi * t)**2
            current = directions[lifted]
            if u <= .5:
                start = (directions[order[(phase - 1) % 6]] + current) / 2
                offset = start + smooth(2 * u) * (current - start)
            else:
                end = (current + directions[order[(phase + 1) % 6]]) / 2
                offset = current + smooth(2 * u - 1) * (end - current)
            feet[:, :2] += variant.get("sway_m", 0) * offset
            yield phase, sample, lifted, feet, tuple(i for i in range(6) if i != lifted)


def kinematic_screen(c, variant):
    errors = []
    peak_speed = 0.
    min_gap = math.inf
    previous = None
    endpoints = []
    qmin, qmax = np.full(3, np.inf), np.full(3, -np.inf)
    for phase, sample, _, feet, _ in poses(c, variant, 100):
        if sample in (0, 100):
            endpoints.append(feet)
        min_gap = min(min_gap, *(float(np.linalg.norm(feet[i, :2] - feet[j, :2])) - 2*c["foot_radius_m"]
                                for i, j in itertools.combinations(range(6), 2)))
        try:
            q = np.array([rover.ik(c, i, feet[i]) for i in range(6)])
        except ValueError as exc:
            errors.append({"phase": phase, "sample": sample, "reason": str(exc)})
            previous = None
            continue
        qmin = np.minimum(qmin, q.min(axis=0))
        qmax = np.maximum(qmax, q.max(axis=0))
        if previous is not None and previous[0] == phase:
            peak_speed = max(peak_speed, float(np.abs(q - previous[1]).max())*100/c["screening"]["phase_time_s"])
        previous = phase, q
    continuity = max(float(np.abs(endpoints[2*p+1] - endpoints[(2*p+2) % 12]).max()) for p in range(6))
    checks = {"all_joint_targets_valid": not errors,
              "foot_pad_clearance": min_gap >= c["screening"]["foot_clearance_required_m"] - 1e-9,
              "sampled_joint_speed": peak_speed <= c["joint_velocity_limit_rad_s"] + 1e-9,
              "phase_boundary_continuity": continuity <= 1e-9}
    return {"pass": all(checks.values()), "checks": checks, "pose_count": 606,
            "peak_joint_speed_rad_s": peak_speed, "minimum_pad_gap_m": min_gap,
            "maximum_boundary_discontinuity_m": continuity,
            "joint_min_deg": np.degrees(qmin).tolist(), "joint_max_deg": np.degrees(qmax).tolist(),
            "invalid_pose_count": len(errors), "first_invalid_poses": errors[:10]}


def load_cases(c):
    dx, dy = c["com_uncertainty_xy_m"]
    g = c["earth_gravity_m_s2"]
    angle = math.radians(5.)
    gravities = [("flat", 0., None, np.array([0., 0., -g]))]
    for h in range(0, 360, 45):
        a = math.radians(h)
        gravities.append((f"slope5_heading{h}", 5., h,
                          g*np.array([math.sin(angle)*math.cos(a), math.sin(angle)*math.sin(a), -math.cos(angle)])))
    for sx, sy in itertools.product((-1, 1), repeat=2):
        com = np.array(c["com_m"]) + [sx*dx, sy*dy, 0]
        for gid, slope, heading, gravity in gravities:
            yield sx, sy, gid, slope, heading, com, gravity


def edge_margin(feet, active, com, gravity):
    projection = com[:2] + (feet[active[0], 2] - com[2])/gravity[2]*gravity[:2]
    hull = ConvexHull(feet[list(active), :2])
    distances = -(hull.equations[:, :2] @ projection + hull.equations[:, 2])
    limiting = int(np.argmin(distances))
    return float(distances[limiting]), sorted(active[int(i)]+1 for i in hull.simplices[limiting]), projection.tolist()


class WrenchLP:
    """Independent force-only encoding; no shared utilization variable.

    Deletion diagnostics retain equilibrium and nonnegative normal forces.
    Feasible diagnostic witnesses are checked against every retained row.
    """
    def __init__(self, c, feet, active, com, gravity):
        self.c, self.feet, self.active = c, feet, active
        self.com, self.gravity = com, gravity
        n = len(active)
        self.aeq = np.zeros((6, 3*n))
        for j, i in enumerate(active):
            self.aeq[:3, 3*j:3*j+3] = np.eye(3)
            r = feet[i] - com
            # Cross products constructed directly, separate from rover.skew().
            self.aeq[3:, 3*j:3*j+3] = np.column_stack([np.cross(r, axis) for axis in np.eye(3)])
        g = gravity*c["screening"]["load_factor"]
        self.beq = np.r_[-c["gross_mass_kg"]*g, [0., 0., 0.]]
        self.bounds = [(None, None), (None, None), (0., None)]*n
        self.rows: dict[str, list[Any]] = {k: [] for k in GROUPS}
        self.jts, self.gbs = [], []
        for j, i in enumerate(active):
            q = rover.ik(c, i, feet[i])
            jt = rover.jacobian(c, i, q).T
            gb = rover.gravity_torque_bound(c, i, q, g)
            self.jts.append(jt)
            self.gbs.append(gb)
            for sx, sy in itertools.product((-1, 1), repeat=2):
                self.add("friction", j, [sx, sy, -c["screening"]["friction_coefficient_assumption"]], 0)
            self.add("normal_cap", j, [0., 0., 1.], c["screening"]["normal_force_limit_n"])
            for axis, name in enumerate(GROUPS[2:]):
                for sign in (-1, 1):
                    self.add(name, j, sign*jt[axis], c["actuator"]["design_torque_limit_nm"] - gb[axis])

    def add(self, group, j, coefficients, rhs):
        row = np.zeros(self.aeq.shape[1])
        row[3*j:3*j+3] = coefficients
        self.rows[group].append((row, rhs))

    def matrices(self, groups):
        rows = [row for group in groups for row in self.rows[group]]
        if not rows:
            return None, None
        return np.array([row for row, _ in rows]), np.array([rhs for _, rhs in rows])

    def validate(self, forces, groups):
        x = np.asarray(forces).reshape(-1)
        if x.shape != (self.aeq.shape[1],) or not np.isfinite(x).all():
            raise ValueError("Invalid force witness")
        a, b = self.matrices(groups)
        if (np.linalg.norm((self.aeq @ x - self.beq)[:3]) > TOL
                or np.linalg.norm((self.aeq @ x - self.beq)[3:]) > TOL
                or np.min(x[2::3]) < -TOL
                or (a is not None and np.max(a @ x - b) > TOL)):
            raise ValueError("Force witness violates constraints")

    def solve(self, groups=GROUPS):
        a, b = self.matrices(groups)
        r = linprog(np.zeros(self.aeq.shape[1]), A_ub=a, b_ub=b,
                    A_eq=self.aeq, b_eq=self.beq, bounds=self.bounds, method="highs")
        if r.success:
            self.validate(r.x, groups)
            return True
        if r.status != 2:
            raise RuntimeError(f"Indeterminate diagnostic solver status {r.status}: {r.message}")
        return False

    def conflict(self):
        retained = list(GROUPS)
        if self.solve(retained):
            return []
        for group in GROUPS:
            trial = [g for g in retained if g != group]
            if not self.solve(trial):
                retained = trial
        return retained or ["unilateral_wrench_geometry"]

    def verify_original(self, result):
        if not result["feasible"]:
            return
        f = np.asarray(result["forces_n"])
        self.validate(f, GROUPS)
        torques = np.array([np.abs(jt @ force) + gb for jt, gb, force in zip(self.jts, self.gbs, f)])
        if not np.allclose(torques, result["torque_bounds_nm"], rtol=0, atol=1e-8):
            raise ValueError("Reported joint torques disagree with force witness")
        cop = np.array([self.c["foot_pivot_height_m"]*np.linalg.norm(x[:2])/x[2] if x[2] > 1e-8 else 0. for x in f])
        expected = {"max_torque_nm": torques.max(), "max_normal_n": f[:, 2].max(),
                    "max_cop_offset_m": cop.max()}
        for key, value in expected.items():
            if not math.isfinite(result[key]) or abs(result[key] - value) > 1e-8:
                raise ValueError(f"Misreported witness metric {key}")


def case_result(c, feet, active, com, gravity, *, diagnose=False):
    result = rover.allocate(c, feet, active, com, gravity, c["screening"]["load_factor"])
    lp = WrenchLP(c, feet, active, com, gravity)
    if lp.solve() != result["feasible"]:
        raise ValueError("Independent/original LP feasibility disagreement")
    lp.verify_original(result)
    margin, edge, projection = edge_margin(feet, active, com, gravity)
    if abs(margin - result["support_margin_m"]) > 1e-9:
        raise ValueError("Independent/original support margin disagreement")
    reasons = allocation_reasons(c, result)
    # Frozen guard returns early on LP failure. Retain this independent concurrent gate.
    if margin < c["screening"]["support_margin_required_m"] - 1e-9 and "support_margin_m" not in reasons:
        reasons.append("support_margin_m")
    return {"accepted": not reasons, "reasons": reasons, "margin_m": margin,
            "limiting_edge_1based": edge, "gravity_projection_xy_m": projection,
            "conflict": lp.conflict() if diagnose and not result["feasible"] else [], "allocation": result}


def controls(base):
    feet = rover.nominal_feet(base)
    active = tuple(range(6))
    com = np.array(base["com_m"])
    flat = np.array([0., 0., -base["earth_gravity_m_s2"]])
    tests = {"nominal_six_contact_positive": not allocation_reasons(base, rover.allocate(
        base, feet, active, com, flat, base["screening"]["load_factor"]))}
    for label, key, value in (("normal_cap", "normal_force_limit_n", 100.),
                               ("friction", "friction_coefficient_assumption", 0.)):
        c = copy.deepcopy(base)
        c["screening"][key] = value
        gravity = list(load_cases(c))[1][-1] if label == "friction" else flat
        lp = WrenchLP(c, feet, active, com, gravity)
        tests[f"synthetic_{label}_negative"] = not lp.solve() and label in lp.conflict()
    c = copy.deepcopy(base)
    c["actuator"]["design_torque_limit_nm"] = .01
    tests["synthetic_torque_negative"] = not WrenchLP(c, feet, active, com, flat).solve()
    outside = com + [2., 0., 0.]
    lp = WrenchLP(base, feet, active, outside, flat)
    tests["synthetic_geometry_negative"] = lp.conflict() == ["unilateral_wrench_geometry"]
    if not all(tests.values()):
        raise ValueError(f"Control failure: {tests}")
    return tests
