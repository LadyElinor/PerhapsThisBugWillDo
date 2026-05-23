#!/usr/bin/env python3
"""Lightweight validator for cad/weevil_leg_params.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]  # optional dependency; simple_yaml is the fallback

from simple_yaml import load_yaml_text

ROOT = Path(__file__).resolve().parents[2]
YAML_PATH = ROOT / "cad" / "weevil_leg_params.yaml"


class ValidationError(Exception):
    pass


def require(d: dict[str, Any], keys: list[str], ctx: str) -> None:
    for key in keys:
        if key not in d:
            raise ValidationError(f"Missing required key '{ctx}.{key}'")


def in_range(name: str, v: float, lo: float, hi: float) -> None:
    if not (lo <= v <= hi):
        raise ValidationError(f"{name}={v} out of bounds [{lo}, {hi}]")


def check_range_pair(name: str, pair: Any) -> None:
    if not isinstance(pair, list) or len(pair) != 2:
        raise ValidationError(f"{name} must be a two-value list")
    if pair[0] >= pair[1]:
        raise ValidationError(f"{name} must be strictly ascending")


def is_bool(name: str, v: Any) -> None:
    if not isinstance(v, bool):
        raise ValidationError(f"{name}={v!r} must be a boolean (true/false)")


def in_enum(name: str, v: Any, allowed: list[str]) -> None:
    if v not in allowed:
        raise ValidationError(f"{name}={v!r} must be one of {allowed}")


def is_positive(name: str, v: float) -> None:
    if not v > 0.0:
        raise ValidationError(f"{name}={v} must be positive")


def ordered(lo_name: str, lo: float, hi_name: str, hi: float) -> None:
    """Assert lo < hi for a pair of related thresholds."""
    if not lo < hi:
        raise ValidationError(
            f"{lo_name}={lo} must be strictly less than {hi_name}={hi}"
        )


def validate(data: dict[str, Any]) -> None:
    require(data, ["meta", "body", "coxa", "femur", "tibia_screw", "foot", "proximal_gimbal"], "root")
    meta = data["meta"]
    require(meta, ["version", "units"], "meta")
    if meta["units"] != "mm":
        raise ValidationError("meta.units must be 'mm'")

    body = data["body"]
    in_range("body.stance_height_mm", float(body["stance_height_mm"]), 100.0, 300.0)
    in_range("body.mass_total_kg", float(body["mass_total_kg"]), 5.0, 80.0)

    coxa = data["coxa"]
    check_range_pair("coxa.yaw_range_deg", coxa["yaw_range_deg"])
    in_range("coxa.shaft_diameter_mm", float(coxa["shaft_diameter_mm"]), 5.0, 30.0)

    femur = data["femur"]
    check_range_pair("femur.pitch_range_deg", femur["pitch_range_deg"])
    in_range("femur.link_length_mm", float(femur["link_length_mm"]), 20.0, 120.0)

    tibia = data["tibia_screw"]
    in_range("tibia_screw.pitch_mm_per_rev", float(tibia["pitch_mm_per_rev"]), 12.0, 15.0)
    in_range("tibia_screw.stroke_mm", float(tibia["stroke_mm"]), 25.0, 45.0)
    in_range("tibia_screw.rotation_range_deg", float(tibia["rotation_range_deg"]), 90.0, 150.0)

    foot = data["foot"]
    in_range("foot.radius_mm", float(foot["radius_mm"]), 70.0, 90.0)
    in_range("foot.pad_thickness_mm", float(foot["pad_thickness_mm"]), 5.0, 8.0)
    in_range("foot.cleat_engage_threshold_N", float(foot["cleat_engage_threshold_N"]), 10.0, 200.0)
    in_range("foot.cleat_forward_gain", float(foot["cleat_forward_gain"]), 0.1, 5.0)
    in_range("foot.cleat_lateral_gain", float(foot["cleat_lateral_gain"]), 0.1, 5.0)

    gimbal = data["proximal_gimbal"]
    in_range("proximal_gimbal.axis_orthogonality_target_deg", float(gimbal["axis_orthogonality_target_deg"]), 70.0, 110.0)
    in_range("proximal_gimbal.axis_orthogonality_tolerance_deg", float(gimbal["axis_orthogonality_tolerance_deg"]), 0.1, 30.0)

    validate_optional_sections(data)


def validate_optional_sections(data: dict[str, Any]) -> None:
    """Validate the subsystem sections that are not part of the core leg
    geometry. These are optional in the schema: each is validated only if
    present, but when present its fields must be well-formed."""

    if "tfj_compliance" in data:
        tfj = data["tfj_compliance"]
        require(tfj, ["enabled", "torsion_spring_k_Nm_per_rad", "damping_c_Nms_per_rad",
                      "neutral_angle_deg", "reduction_range_deg"], "tfj_compliance")
        is_bool("tfj_compliance.enabled", tfj["enabled"])
        is_positive("tfj_compliance.torsion_spring_k_Nm_per_rad", float(tfj["torsion_spring_k_Nm_per_rad"]))
        in_range("tfj_compliance.damping_c_Nms_per_rad", float(tfj["damping_c_Nms_per_rad"]), 0.0, 50.0)
        in_range("tfj_compliance.neutral_angle_deg", float(tfj["neutral_angle_deg"]), -45.0, 45.0)
        in_range("tfj_compliance.reduction_range_deg", float(tfj["reduction_range_deg"]), 0.0, 90.0)

    if "gait_phase" in data:
        gait = data["gait_phase"]
        require(gait, ["contact_z_threshold_mm", "min_stance_fraction", "max_stance_fraction"], "gait_phase")
        in_range("gait_phase.contact_z_threshold_mm", float(gait["contact_z_threshold_mm"]), 0.0, 20.0)
        in_range("gait_phase.min_stance_fraction", float(gait["min_stance_fraction"]), 0.0, 1.0)
        in_range("gait_phase.max_stance_fraction", float(gait["max_stance_fraction"]), 0.0, 1.0)
        ordered("gait_phase.min_stance_fraction", float(gait["min_stance_fraction"]),
                "gait_phase.max_stance_fraction", float(gait["max_stance_fraction"]))

    if "coupling" in data:
        coupling = data["coupling"]
        require(coupling, ["offplane_index_limit"], "coupling")
        in_range("coupling.offplane_index_limit", float(coupling["offplane_index_limit"]), 0.0, 1.0)

    if "mobility" in data:
        mob = data["mobility"]
        require(mob, ["mode_default", "virtual_rocker_bogie_enabled",
                      "tilt_warn_deg", "tilt_hard_limit_deg"], "mobility")
        in_enum("mobility.mode_default", mob["mode_default"], ["quasi_static", "dynamic"])
        is_bool("mobility.virtual_rocker_bogie_enabled", mob["virtual_rocker_bogie_enabled"])
        in_range("mobility.tilt_warn_deg", float(mob["tilt_warn_deg"]), 0.0, 90.0)
        in_range("mobility.tilt_hard_limit_deg", float(mob["tilt_hard_limit_deg"]), 0.0, 90.0)
        # A warn threshold at or above the hard limit would never fire usefully.
        ordered("mobility.tilt_warn_deg", float(mob["tilt_warn_deg"]),
                "mobility.tilt_hard_limit_deg", float(mob["tilt_hard_limit_deg"]))

    if "thermal" in data:
        thermal = data["thermal"]
        require(thermal, ["warm_electronics_core_enabled", "radiator_area_m2",
                          "insulation_stack", "dust_thermal_boundary"], "thermal")
        is_bool("thermal.warm_electronics_core_enabled", thermal["warm_electronics_core_enabled"])
        in_range("thermal.radiator_area_m2", float(thermal["radiator_area_m2"]), 0.0, 5.0)

    if "power" in data:
        power = data["power"]
        require(power, ["hybrid_profile_enabled", "day_energy_available_Wh",
                        "night_survival_load_Wh", "recovery_reserve_Wh",
                        "dust_derate_factor"], "power")
        is_bool("power.hybrid_profile_enabled", power["hybrid_profile_enabled"])
        is_positive("power.day_energy_available_Wh", float(power["day_energy_available_Wh"]))
        is_positive("power.night_survival_load_Wh", float(power["night_survival_load_Wh"]))
        in_range("power.recovery_reserve_Wh", float(power["recovery_reserve_Wh"]), 0.0, 1000.0)
        in_range("power.dust_derate_factor", float(power["dust_derate_factor"]), 0.0, 1.0)
        # Night survival plus reserve must fit inside the day energy budget,
        # otherwise the hybrid profile cannot close.
        night = float(power["night_survival_load_Wh"]) + float(power["recovery_reserve_Wh"])
        if night > float(power["day_energy_available_Wh"]):
            raise ValidationError(
                f"power: night_survival_load + recovery_reserve ({night} Wh) "
                f"exceeds day_energy_available ({power['day_energy_available_Wh']} Wh)"
            )

    if "sensing" in data:
        sensing = data["sensing"]
        require(sensing, ["mast_stereo_nav_enabled", "leg_slip_observability_enabled",
                          "watchdog_enabled"], "sensing")
        for key in ("mast_stereo_nav_enabled", "leg_slip_observability_enabled", "watchdog_enabled"):
            is_bool(f"sensing.{key}", sensing[key])

    if "urdf_defaults" in data:
        urdf = data["urdf_defaults"]
        require(urdf, ["mass_kg", "inertia_mode", "joint_approximation"], "urdf_defaults")
        masses = urdf["mass_kg"]
        require(masses, ["coxa", "femur", "tibia_assembly", "foot"], "urdf_defaults.mass_kg")
        for link, m in masses.items():
            in_range(f"urdf_defaults.mass_kg.{link}", float(m), 0.0, 20.0)
        in_enum("urdf_defaults.inertia_mode", urdf["inertia_mode"],
                ["box_approx_v0", "cylinder_approx_v0", "mesh_v1"])


def main() -> int:
    text = YAML_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if yaml is not None else load_yaml_text(text)
    validate(data)
    print(f"OK: {YAML_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
