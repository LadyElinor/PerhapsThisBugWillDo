"""COTS prototype geometry and conservative static sizing. No motor I/O or soil prediction.

Ground reactions satisfy force AND moment balance. The friction coefficient is a
screening assumption, not a measured regolith parameter. All lengths are metres.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, QhullError

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "design/cots_v1/config.json"


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    c = json.loads(path.read_text())
    for key in ("gross_mass_kg", "coxa_m", "femur_m", "tibia_m", "foot_radius_m"):
        if not math.isfinite(c[key]) or c[key] <= 0:
            raise ValueError(f"Invalid {key}")
    if len(c["hips_xy_m"]) != 6 or len(c["leg_azimuth_deg"]) != 6:
        raise ValueError("Six explicitly positioned legs are required")

    def finite_numbers(value):
        if isinstance(value, dict):
            return all(finite_numbers(v) for v in value.values())
        if isinstance(value, list):
            return all(finite_numbers(v) for v in value)
        return not isinstance(value, (int, float)) or math.isfinite(value)

    if not finite_numbers(c):
        raise ValueError("Nonfinite configuration number")
    if c["screening"]["friction_coefficient_assumption"] < 0:
        raise ValueError("Negative friction")
    return c


def rotz(a: float) -> np.ndarray:
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def hip(c: dict[str, Any], leg: int) -> np.ndarray:
    return np.array([*c["hips_xy_m"][leg], c["hip_height_m"]], dtype=float)


def nominal_feet(c: dict[str, Any]) -> np.ndarray:
    return np.array(
        [
            hip(c, i)
            + rotz(math.radians(a))
            @ np.array([c["nominal_radial_reach_m"], 0, c["foot_pivot_height_m"] - c["hip_height_m"]])
            for i, a in enumerate(c["leg_azimuth_deg"])
        ]
    )


def ik(c: dict[str, Any], leg: int, target: np.ndarray, enforce_limits: bool = True) -> np.ndarray:
    p = rotz(-math.radians(c["leg_azimuth_deg"][leg])) @ (np.asarray(target, dtype=float) - hip(c, leg))
    if not np.isfinite(p).all():
        raise ValueError("Nonfinite foot target")
    q0 = math.atan2(p[1], p[0])
    r, down = math.hypot(p[0], p[1]) - c["coxa_m"], -p[2]
    a, b = c["femur_m"], c["tibia_m"]
    cosine = (r * r + down * down - a * a - b * b) / (2 * a * b)
    if not -1 - 1e-12 <= cosine <= 1 + 1e-12:
        raise ValueError("Foot target outside link reach")
    q2 = math.acos(float(np.clip(cosine, -1, 1)))
    q1 = math.atan2(down, r) - math.atan2(b * math.sin(q2), a + b * math.cos(q2))
    q = np.array([q0, q1, q2])
    limits = np.radians(c["joint_limits_deg"])
    if enforce_limits and (np.any(q < limits[:, 0] - 1e-10) or np.any(q > limits[:, 1] + 1e-10)):
        raise ValueError("Foot target violates joint limits")
    return q


def points(c: dict[str, Any], leg: int, q: np.ndarray) -> np.ndarray:
    angle = math.radians(c["leg_azimuth_deg"][leg]) + q[0]
    radial = np.array([math.cos(angle), math.sin(angle), 0])
    z = np.array([0.0, 0.0, 1.0])
    h = hip(c, leg)
    p = h + c["coxa_m"] * radial
    k = p + c["femur_m"] * (math.cos(q[1]) * radial - math.sin(q[1]) * z)
    f = k + c["tibia_m"] * (math.cos(q[1] + q[2]) * radial - math.sin(q[1] + q[2]) * z)
    return np.array([h, p, k, f])


def axes(c: dict[str, Any], leg: int, q: np.ndarray) -> np.ndarray:
    a = math.radians(c["leg_azimuth_deg"][leg]) + q[0]
    tangent = np.array([-math.sin(a), math.cos(a), 0])
    return np.array([[0.0, 0.0, 1.0], tangent, tangent])


def jacobian(c: dict[str, Any], leg: int, q: np.ndarray) -> np.ndarray:
    p = points(c, leg, q)
    return np.column_stack([np.cross(a, p[3] - o) for a, o in zip(axes(c, leg, q), p[:3])])


def gravity_torque_bound(c: dict[str, Any], leg: int, q: np.ndarray, gravity: np.ndarray) -> np.ndarray:
    """Sum magnitudes per joint: intentionally gives no benefit for cancellation."""
    h, p, k, f = points(c, leg, q)
    ax = axes(c, leg, q)
    m = c["leg_mass_proxies"]
    lumps = [
        ((h + p) / 2, m["at_coxa_mid_kg"], 1),
        (p, m["at_pitch_kg"], 1),
        ((p + k) / 2, m["at_thigh_mid_kg"], 2),
        (k, m["at_knee_kg"], 2),
        ((k + f) / 2, m["at_shank_mid_kg"], 3),
        (f, m["at_foot_kg"], 3),
    ]
    torque = np.zeros(3)
    for location, mass, count in lumps:
        for j in range(count):
            torque[j] += abs(float(np.dot(ax[j], np.cross(location - [h, p, k][j], mass * gravity))))
    return torque


def skew(p: np.ndarray) -> np.ndarray:
    x, y, z = p
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def support_margin(feet: np.ndarray, com: np.ndarray, gravity: np.ndarray) -> float:
    if len(feet) < 3 or abs(gravity[2]) < 1e-12:
        return -math.inf
    # Intersect gravity line with the common ankle plane; finite feet are checked separately.
    projection = com[:2] + (feet[0, 2] - com[2]) / gravity[2] * gravity[:2]
    try:
        hull = ConvexHull(feet[:, :2])
    except QhullError:
        return -math.inf
    return float(np.min(-(hull.equations[:, :2] @ projection + hull.equations[:, 2])))


def allocate(
    c: dict[str, Any],
    feet: np.ndarray,
    active: tuple[int, ...],
    com: np.ndarray,
    gravity: np.ndarray,
    load_factor: float = 1.0,
) -> dict[str, Any]:
    """LP minimizes peak normalized torque/contact utilization under wrench constraints.

    All contacts are unilateral. No actuator preload is added to vehicle weight.
    A four-sided, inscribed friction pyramid is conservative relative to a circle.
    """
    n = len(active)
    if (
        n < 3
        or len(set(active)) != n
        or any(i not in range(6) for i in active)
        or np.shape(feet) != (6, 3)
        or not np.isfinite(feet).all()
        or np.shape(com) != (3,)
        or not np.isfinite(com).all()
        or np.shape(gravity) != (3,)
        or not np.isfinite(gravity).all()
        or gravity[2] >= 0
        or not math.isfinite(load_factor)
        or load_factor <= 0
    ):
        raise ValueError("Invalid support inputs")
    g = np.asarray(gravity) * load_factor
    aeq = np.zeros((6, 3 * n + 1))
    aeq[:3, : 3 * n] = np.tile(np.eye(3), (1, n))
    for j, i in enumerate(active):
        aeq[3:, 3 * j : 3 * j + 3] = skew(feet[i] - com)
    beq = np.r_[-c["gross_mass_kg"] * g, [0.0, 0.0, 0.0]]
    ub: list[np.ndarray] = []
    rhs: list[float] = []
    mu = c["screening"]["friction_coefficient_assumption"]
    torque_limit = c["actuator"]["design_torque_limit_nm"]
    js, gs = [], []
    for j, i in enumerate(active):
        q = ik(c, i, feet[i])
        jt = jacobian(c, i, q).T
        gb = gravity_torque_bound(c, i, q, g)
        js.append(jt)
        gs.append(gb)
        for sx, sy in itertools.product((-1, 1), repeat=2):
            row = np.zeros(3 * n + 1)
            row[3 * j : 3 * j + 3] = [sx, sy, -mu]
            ub.append(row)
            rhs.append(0)
        for axis in range(3):
            for sign in (-1, 1):
                row = np.zeros(3 * n + 1)
                row[3 * j : 3 * j + 3] = sign * jt[axis]
                row[-1] = -torque_limit
                ub.append(row)
                rhs.append(-gb[axis])
        row = np.zeros(3 * n + 1)
        row[3 * j + 2] = 1
        row[-1] = -c["screening"]["normal_force_limit_n"]
        ub.append(row)
        rhs.append(0)
    bounds = [b for _ in active for b in [(None, None), (None, None), (0, c["screening"]["normal_force_limit_n"])]] + [
        (0, 1)
    ]
    objective = np.r_[np.zeros(3 * n), 1.0]
    result = linprog(
        objective, A_ub=np.array(ub), b_ub=np.array(rhs), A_eq=aeq, b_eq=beq, bounds=bounds, method="highs"
    )
    margin = support_margin(feet[list(active)], com, g)
    if not result.success:
        return {"feasible": False, "reason": result.message, "support_margin_m": margin}
    forces = result.x[:-1].reshape(n, 3)
    torques = np.array([np.abs(jt @ f) + gb for jt, f, gb in zip(js, forces, gs)])
    cop_offsets = np.array(
        [c["foot_pivot_height_m"] * np.linalg.norm(f[:2]) / f[2] if f[2] > 1e-8 else 0 for f in forces]
    )
    residual = aeq @ result.x - beq
    return {
        "feasible": True,
        "peak_utilization": float(result.x[-1]),
        "active": list(active),
        "forces_n": forces.tolist(),
        "torque_bounds_nm": torques.tolist(),
        "max_torque_nm": float(torques.max()),
        "max_normal_n": float(forces[:, 2].max()),
        "force_residual_n": float(np.linalg.norm(residual[:3])),
        "moment_residual_nm": float(np.linalg.norm(residual[3:])),
        "support_margin_m": margin,
        "max_cop_offset_m": float(cop_offsets.max()),
    }


def gait_samples(c: dict[str, Any], subdivisions: int = 8):
    """One complete six-step wave cycle; stance feet move backward as chassis advances.

    Starts at the periodic phase, not six coincident neutral foot phases. One leg
    swings at a time. Swing is a cosine lift; body translation is foot sweep/5 per phase, plus a transfer dwell.
    """
    nominal = nominal_feet(c)
    order = (0, 3, 1, 4, 2, 5)
    length = c["screening"]["step_length_m"]
    # Duty factor 5/6. Each grounded foot traverses exactly length in five phases.
    advance = length / 5
    initial = np.zeros(6)
    for rank, i in enumerate(order):
        initial[i] = -length / 2 + rank * advance
    for phase, lifted in enumerate(order):
        for s in range(subdivisions + 1):
            t = s / subdivisions
            t = t**3 * (10 - 15 * t + 6 * t * t)  # zero endpoint velocity and acceleration
            p = nominal.copy()
            for rank, i in enumerate(order):
                if rank < phase:
                    p[i, 0] += length / 2 - (phase - rank - 1 + t) * advance
                elif rank > phase:
                    p[i, 0] += initial[i] - (phase + t) * advance
                else:
                    p[i, 0] += -length / 2 + length * t
                    p[i, 2] += c["screening"]["step_height_m"] * math.sin(math.pi * t) ** 2
            yield f"phase{phase}_sample{s}", p, tuple(i for i in range(6) if i != lifted)


def structural_checks(c: dict[str, Any]) -> dict[str, float]:
    s = c["structure"]
    f = c["screening"]["normal_force_limit_n"]
    # A deliberately conservative point load on the longest straight tube.
    resultant = f * math.sqrt(1 + c["screening"]["friction_coefficient_assumption"] ** 2)
    length = max(c["femur_m"], c["tibia_m"])
    b, t = s["tube_outer_m"], s["tube_wall_m"]
    second = (b**4 - (b - 2 * t) ** 4) / 12
    stress = resultant * length * b / (2 * second)
    deflection = resultant * length**3 / (3 * s["tube_modulus_assumption_pa"] * second)
    # Shaft/bearing screen includes the whole leg mass and a 0.40 m load arm.
    # A short hub offset alone would miss the yaw joint overturning moment.
    joint_force = (
        resultant + sum(c["leg_mass_proxies"].values()) * c["earth_gravity_m_s2"] * c["screening"]["load_factor"]
    )
    d = s["shaft_diameter_m"]
    moment = joint_force * s["shaft_load_eccentricity_m"]
    bending = 32 * moment / (math.pi * d**3)
    torsion = 16 * c["actuator"]["design_torque_limit_nm"] / (math.pi * d**3)
    vm = s["shaft_stress_concentration_factor"] * math.sqrt(bending * bending + 3 * torsion * torsion)
    reaction = joint_force / 2 + moment / s["shaft_bearing_span_m"]
    return {
        "tube_bending_stress_pa": stress,
        "tube_yield_factor": s["tube_yield_assumption_pa"] / stress,
        "tube_tip_deflection_m": deflection,
        "shaft_von_mises_pa": vm,
        "shaft_yield_factor": s["shaft_yield_requirement_pa"] / vm,
        "shaft_bending_moment_nm": moment,
        "bearing_reaction_n": reaction,
        "bearing_static_capacity_ratio": s["bearing_static_capacity_n"] / reaction,
    }


def power_checks(c: dict[str, Any]) -> dict[str, Any]:
    p = c["power"]
    ctrl = c["control"]
    energy = p["nominal_voltage_v"] * p["capacity_ah"]
    usable = energy * p["energy_usable_fraction_assumption"] - p["reserve_wh"]
    clamp_high = max(p["bench_supply_v"], p["charge_voltage_v"]) + p["clamp_voltage_rise_max_v"]
    clamp_low = p["operating_cutoff_v"] + p["clamp_voltage_rise_max_v"]
    independent_bound = 18 * c["actuator"]["design_torque_limit_nm"] * c["joint_velocity_limit_rad_s"]
    return {
        "nominal_energy_wh": energy,
        "planning_usable_wh": usable,
        "runtime_scenarios_min": {str(w): 60 * usable / w for w in p["mean_power_scenarios_w"]},
        "battery_continuous_bus_limit_w_at_cutoff": p["operating_cutoff_v"] * p["design_bus_current_a"],
        "clamp_max_bus_v": clamp_high,
        "driver_voltage_headroom_v": c["actuator"]["driver_voltage_range_v"][1] - clamp_high,
        "resistor_instantaneous_max_w": clamp_high**2
        / (p["brake_resistance_ohm"] * (1 - p["resistor_tolerance_fraction"])),
        "resistor_brake_current_max_a": clamp_high
        / (p["brake_resistance_ohm"] * (1 - p["resistor_tolerance_fraction"])),
        "resistor_absorption_min_w": clamp_low**2
        / (p["brake_resistance_ohm"] * (1 + p["resistor_tolerance_fraction"])),
        "independent_joint_mechanical_bound_w": independent_bound,
        "regen_bound_w": independent_bound,
        "can_utilization": ctrl["motors_per_bus"]
        * ctrl["frames_per_motor_cycle"]
        * ctrl["command_hz"]
        * ctrl["worst_frame_bits"]
        / ctrl["can_bitrate"]
        + ctrl["can_overhead_fraction"],
    }


def mass_budget(c: dict[str, Any]) -> dict[str, float]:
    with (DEFAULT_CONFIG.parent / "bom.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    mass = sum(float(r["qty_full"]) * float(r["unit_mass_budget_kg"]) for r in rows if r["onboard"] == "yes")
    return {
        "allocated_mass_kg": mass,
        "reserve_kg": c["gross_mass_kg"] - mass,
        "reserve_fraction": 1 - mass / c["gross_mass_kg"],
    }


def evaluate(c: dict[str, Any]) -> dict[str, Any]:
    checks = []
    worst = {"torque_nm": 0.0, "normal_n": 0.0, "cop_offset_m": 0.0, "force_residual_n": 0.0, "moment_residual_nm": 0.0}
    min_margin = math.inf
    min_pad_gap = math.inf
    joint_min = np.full(3, np.inf)
    joint_max = -joint_min
    failures = []
    count = 0
    x, y = c["com_uncertainty_xy_m"]
    coms = [np.array(c["com_m"]) + [dx, dy, 0] for dx, dy in itertools.product((-x, x), (-y, y))]
    tilt = math.radians(c["screening"]["slope_limit_deg"])
    gravities = [np.array([0.0, 0.0, -c["earth_gravity_m_s2"]])]
    for azimuth in np.linspace(0, 2 * math.pi, 8, endpoint=False):
        gravities.append(
            c["earth_gravity_m_s2"]
            * np.array([math.sin(tilt) * math.cos(azimuth), math.sin(tilt) * math.sin(azimuth), -math.cos(tilt)])
        )
    for name, feet, active in gait_samples(c):
        for i in range(6):
            try:
                q = ik(c, i, feet[i])
            except ValueError as exc:
                failures.append({"case": name, "reason": str(exc)})
                continue
            joint_min = np.minimum(joint_min, q)
            joint_max = np.maximum(joint_max, q)
        for i, j in itertools.combinations(range(6), 2):
            min_pad_gap = min(min_pad_gap, float(np.linalg.norm(feet[i, :2] - feet[j, :2]) - 2 * c["foot_radius_m"]))
        for com, g in itertools.product(coms, gravities):
            count += 1
            out = allocate(c, feet, active, com, g, c["screening"]["load_factor"])
            min_margin = min(min_margin, out["support_margin_m"])
            if not out["feasible"]:
                failures.append(
                    {"case": name, "com_m": com.tolist(), "gravity_m_s2": g.tolist(), "reason": out["reason"]}
                )
                continue
            for key, source in [
                ("torque_nm", "max_torque_nm"),
                ("normal_n", "max_normal_n"),
                ("cop_offset_m", "max_cop_offset_m"),
                ("force_residual_n", "force_residual_n"),
                ("moment_residual_nm", "moment_residual_nm"),
            ]:
                worst[key] = max(worst[key], out[source])
    structure = structural_checks(c)
    power = power_checks(c)
    mass = mass_budget(c)
    peak_rate = 0.0
    max_lever = 0.0
    previous = None
    for name, f, _ in gait_samples(c, 100):
        q = np.array([ik(c, i, f[i]) for i in range(6)])
        for i in range(6):
            ps = points(c, i, q[i])
            max_lever = max(max_lever, float(np.max(np.linalg.norm(ps[3] - ps[:3], axis=1))) + 0.04)
        if previous is not None and previous[0] == name.split("_")[0]:
            peak_rate = max(peak_rate, float(np.max(np.abs(q - previous[1]))) * 100 / c["screening"]["phase_time_s"])
        previous = (name.split("_")[0], q)
    landing = c["landing"]
    drop_energy = c["gross_mass_kg"] * c["earth_gravity_m_s2"] * (landing["clearance_m"] + landing["stroke_m"])
    drop_velocity = math.sqrt(2 * c["earth_gravity_m_s2"] * landing["clearance_m"])
    # Effective mass includes gravitational work during the shock absorber stroke.
    effective_mass = 2 * drop_energy / drop_velocity**2
    landing_result = {
        "single_damper_energy_j": drop_energy,
        "impact_velocity_m_s": drop_velocity,
        "effective_mass_single_kg": effective_mass,
        "effective_mass_four_kg": effective_mass / 4,
        "energy_capacity_ratio": landing["rated_energy_j"] / drop_energy,
        "qualification": "energy screen only; guided skids and drop testing required",
    }

    def check(name: str, passed: bool):
        checks.append({"name": name, "pass": bool(passed)})

    check("all_sampled_wrenches_feasible", not failures)
    check("support_margin", min_margin >= c["screening"]["support_margin_required_m"])
    check("foot_clearance", min_pad_gap >= c["screening"]["foot_clearance_required_m"])
    check("cop_inside_pad", worst["cop_offset_m"] <= c["foot_radius_m"] - c["screening"]["foot_cop_edge_reserve_m"])
    check("force_moment_residual", max(worst["force_residual_n"], worst["moment_residual_nm"]) < 1e-6)
    check(
        "tube_and_shaft_yield_screen",
        min(structure["tube_yield_factor"], structure["shaft_yield_factor"]) >= c["structure"]["minimum_yield_factor"],
    )
    check("gait_joint_speed", peak_rate <= c["joint_velocity_limit_rad_s"])
    check(
        "landing_energy_and_mass",
        drop_energy < landing["rated_energy_j"]
        and landing["effective_mass_range_kg"][0] <= effective_mass / 4
        and effective_mass <= landing["effective_mass_range_kg"][1],
    )
    check("mass_reserve", mass["reserve_fraction"] >= c["minimum_mass_reserve_fraction"])
    check("shaft_load_arm_covers_gait", max_lever <= c["structure"]["shaft_load_eccentricity_m"])
    check("bearing_static_screen", structure["bearing_static_capacity_ratio"] >= 2)
    check(
        "aux_voltage_range",
        c["power"]["aux_input_range_v"][0] <= c["power"]["operating_cutoff_v"]
        and power["clamp_max_bus_v"] <= c["power"]["aux_input_range_v"][1],
    )
    check("battery_current", c["power"]["design_bus_current_a"] <= c["power"]["continuous_current_a"])
    check("can_bandwidth", power["can_utilization"] <= c["control"]["max_bus_utilization"])
    check("clamp_voltage_screen", power["driver_voltage_headroom_v"] > 1)
    check("brake_current_screen", power["resistor_brake_current_max_a"] < c["power"]["regen_clamp_brake_current_a"])
    check("regen_power_absorption_screen", power["resistor_absorption_min_w"] > power["regen_bound_w"])
    return {
        "design_id": c["design_id"],
        "analytical_checks_pass": all(x["pass"] for x in checks),
        "hardware_validated": False,
        "flight_qualified": False,
        "checks": checks,
        "load_cases": count,
        "worst": worst,
        "min_support_margin_m": min_margin,
        "min_pad_gap_m": min_pad_gap,
        "joint_range_deg": [np.degrees(joint_min).tolist(), np.degrees(joint_max).tolist()],
        "structure": structure,
        "power": power,
        "landing": landing_result,
        "mass_budget": mass,
        "maximum_load_arm_with_offset_m": max_lever,
        "gait": {
            "peak_joint_speed_rad_s": peak_rate,
            "mean_body_speed_m_s": c["screening"]["step_length_m"]
            / 5
            / (c["screening"]["phase_time_s"] + c["screening"]["load_transfer_dwell_s"]),
        },
        "failure_count": len(failures),
        "first_failures": failures[:10],
        "limitations": [
            "Discrete quasi-static cases, not a dynamic or continuous collision proof.",
            "Friction, material properties, link mass proxies and COM envelope require measurement.",
            "No sinkage, anchor, lunar soil, fatigue, gearbox life or thermal qualification claim.",
            "Voltage transient margin requires oscilloscope verification; no clamp transient model.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    c = load_config(args.config)
    report = evaluate(c)
    report["config_sha256"] = hashlib.sha256(args.config.read_bytes()).hexdigest()
    report["bom_sha256"] = hashlib.sha256((DEFAULT_CONFIG.parent / "bom.csv").read_bytes()).hexdigest()
    report["model_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    print(serialized)
    return 0 if report["analytical_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
