#!/usr/bin/env python3
"""Lightweight validator for cad/weevil_leg_params.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

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

    gimbal = data["proximal_gimbal"]
    in_range("proximal_gimbal.axis_orthogonality_target_deg", float(gimbal["axis_orthogonality_target_deg"]), 70.0, 110.0)
    in_range("proximal_gimbal.axis_orthogonality_tolerance_deg", float(gimbal["axis_orthogonality_tolerance_deg"]), 0.1, 30.0)


def main() -> int:
    text = YAML_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text) if yaml is not None else load_yaml_text(text)
    validate(data)
    print(f"OK: {YAML_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
