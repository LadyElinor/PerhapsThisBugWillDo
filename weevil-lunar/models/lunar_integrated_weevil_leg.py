#!/usr/bin/env python3
"""Reduced-order lunar weevil leg model.

Focus:
- helical tibia coupling (rotation -> prismatic displacement)
- explicit separation of internal joint friction vs regolith friction
- preload in N (never inferred from Earth gravity)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
PARAMS_PATH = ROOT / "cad" / "weevil_leg_params.yaml"

# Reuse parser from cad/scripts without requiring external YAML deps.
import sys
sys.path.append(str(ROOT / "cad" / "scripts"))
from simple_yaml import load_yaml_text  # type: ignore

EARTH_G = 9.81
LUNAR_G = 1.62


@dataclass(frozen=True)
class ContactModel:
    regolith_mu: float = 0.55
    internal_mu: float = 0.004


@dataclass(frozen=True)
class LegState:
    coxa_yaw_deg: float
    femur_pitch_deg: float
    tibia_theta_deg: float


@dataclass(frozen=True)
class LegParams:
    coxa_range: tuple[float, float]
    femur_range: tuple[float, float]
    tibia_range_total_deg: float
    tibia_pitch_mm_per_rev: float
    femur_link_mm: float
    tibia_stroke_mm: float
    preload_n: float
    axis_target_deg: float
    axis_tol_deg: float
    cleat_forward_gain: float


@dataclass(frozen=True)
class EvalResult:
    reachable: bool
    tip_x_mm: float
    tip_z_mm: float
    normal_n: float
    traction_n: float


def load_params(path: Path = PARAMS_PATH) -> LegParams:
    text = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text) if yaml is not None else load_yaml_text(text)
    return LegParams(
        coxa_range=tuple(raw["coxa"]["yaw_range_deg"]),
        femur_range=tuple(raw["femur"]["pitch_range_deg"]),
        tibia_range_total_deg=float(raw["tibia_screw"]["rotation_range_deg"]),
        tibia_pitch_mm_per_rev=float(raw["tibia_screw"]["pitch_mm_per_rev"]),
        femur_link_mm=float(raw["femur"]["link_length_mm"]),
        tibia_stroke_mm=float(raw["tibia_screw"]["stroke_mm"]),
        preload_n=float(raw["foot"]["cleat_engage_threshold_N"]),
        axis_target_deg=float(raw["proximal_gimbal"]["axis_orthogonality_target_deg"]),
        axis_tol_deg=float(raw["proximal_gimbal"]["axis_orthogonality_tolerance_deg"]),
        cleat_forward_gain=float(raw["foot"]["cleat_forward_gain"]),
    )


def helical_displacement_mm(theta_deg: float, pitch_mm_per_rev: float) -> float:
    return (theta_deg / 360.0) * pitch_mm_per_rev


def axis_is_within_tolerance(actual_deg: float, target_deg: float, tol_deg: float) -> bool:
    return abs(actual_deg - target_deg) <= tol_deg


def evaluate_leg_state(state: LegState, params: LegParams, contact: ContactModel) -> EvalResult:
    reachable = (
        params.coxa_range[0] <= state.coxa_yaw_deg <= params.coxa_range[1]
        and params.femur_range[0] <= state.femur_pitch_deg <= params.femur_range[1]
        and abs(state.tibia_theta_deg) <= params.tibia_range_total_deg / 2.0
    )

    femur_rad = math.radians(state.femur_pitch_deg)
    ext_mm = helical_displacement_mm(state.tibia_theta_deg, params.tibia_pitch_mm_per_rev)
    ext_mm = max(-params.tibia_stroke_mm / 2.0, min(params.tibia_stroke_mm / 2.0, ext_mm))
    tibia_effective_mm = params.tibia_stroke_mm + ext_mm

    tip_x = params.femur_link_mm * math.cos(femur_rad) + tibia_effective_mm * math.cos(femur_rad)
    tip_z = params.femur_link_mm * math.sin(femur_rad) + tibia_effective_mm * math.sin(femur_rad)

    normal_n = params.preload_n
    terrain_term = max(0.0, contact.regolith_mu * normal_n * params.cleat_forward_gain)
    efficiency = max(0.0, 1.0 - contact.internal_mu)
    lunar_scale = LUNAR_G / EARTH_G
    traction_n = terrain_term * efficiency * lunar_scale

    return EvalResult(
        reachable=reachable,
        tip_x_mm=tip_x,
        tip_z_mm=tip_z,
        normal_n=normal_n,
        traction_n=traction_n,
    )


def sample_states(params: LegParams) -> Iterable[LegState]:
    for c in (params.coxa_range[0], 0.0, params.coxa_range[1]):
        for f in (params.femur_range[0], 0.0, params.femur_range[1]):
            for t in (-params.tibia_range_total_deg / 2.0, 0.0, params.tibia_range_total_deg / 2.0):
                yield LegState(c, f, t)


def main() -> int:
    params = load_params()
    contact = ContactModel()

    # sanity check for proximal axis assumptions (orthogonal by design)
    if not axis_is_within_tolerance(90.0, params.axis_target_deg, params.axis_tol_deg):
        raise SystemExit("Axis orthogonality sanity check failed")

    for state in sample_states(params):
        result = evaluate_leg_state(state, params, contact)
        print(state, "=>", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
