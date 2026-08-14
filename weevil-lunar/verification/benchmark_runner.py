#!/usr/bin/env python3
"""Run simple scenario benchmarks for original vs patched reduced-order model."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from models.contact import (  # noqa: E402
    FootGeometry,
    RegolithContactModel,
    RegolithProperties,
    RegolithType,
)
from models.lunar_integrated_weevil_leg import ContactModel, LegState, evaluate_leg_state, load_params

OUT_PATH = ROOT / "verification" / "reports" / "benchmark_comparison.csv"


@dataclass(frozen=True)
class Scenario:
    name: str
    femur_pitch_deg: float
    tibia_theta_deg: float


def scenario_contact_traction(params, state: LegState, contact: ContactModel) -> tuple[float, bool]:
    regolith = RegolithProperties.from_type(RegolithType.MARE)
    foot = FootGeometry.circular(
        radius=params.tibia_stroke_mm / 1000.0,
        cleat_gain_forward=params.cleat_forward_gain,
        cleat_gain_lateral=1.0,
        cleat_engage_threshold_preload=params.preload_n,
    )
    model = RegolithContactModel(regolith, foot)

    out = evaluate_leg_state(state, params, contact)

    femur_abs = abs(state.femur_pitch_deg)
    tibia_abs = abs(state.tibia_theta_deg)
    preload_scale = max(0.25, 1.0 - femur_abs / 120.0 + tibia_abs / 240.0)
    body_scale = max(0.25, 1.0 + state.femur_pitch_deg / 90.0 + tibia_abs / 180.0)

    preload_normal = params.preload_n * preload_scale
    body_normal_load = params.preload_n * body_scale
    contact_forces = model.compute_contact_forces_with_preload(
        body_normal_load=body_normal_load,
        preload_normal=preload_normal,
        twist_settle_gain=max(0.5, 1.0 - contact.internal_mu),
        use_directional_cleats=True,
    )

    traction_n = contact_forces.max_shear_forward * max(0.0, contact.regolith_mu)
    success = out.reachable and contact_forces.anchored and traction_n > 1.0
    return traction_n, success


def run(contact: ContactModel) -> list[tuple[str, float, bool]]:
    params = load_params()
    scenarios = [
        Scenario("flat", -10.0, 0.0),
        Scenario("slope_25deg", 5.0, 30.0),
        Scenario("sinkage_recovery", -30.0, 60.0),
    ]

    rows: list[tuple[str, float, bool]] = []
    for sc in scenarios:
        state = LegState(coxa_yaw_deg=0.0, femur_pitch_deg=sc.femur_pitch_deg, tibia_theta_deg=sc.tibia_theta_deg)
        traction_n, success = scenario_contact_traction(params, state, contact)
        rows.append((sc.name, traction_n, success))
    return rows


def main() -> int:
    original = run(ContactModel(regolith_mu=0.55, internal_mu=0.02))
    patched = run(ContactModel(regolith_mu=0.55, internal_mu=0.004))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["scenario", "original_traction_n", "patched_traction_n", "original_success", "patched_success"])
        for o, p in zip(original, patched):
            writer.writerow([o[0], round(o[1], 4), round(p[1], 4), o[2], p[2]])

    print(f"Wrote {OUT_PATH}")
    for o, p in zip(original, patched):
        print(f"{o[0]}: original={o[1]:.3f}N patched={p[1]:.3f}N")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
