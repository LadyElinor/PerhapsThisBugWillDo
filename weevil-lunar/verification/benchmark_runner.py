#!/usr/bin/env python3
"""Run simple scenario benchmarks for original vs patched reduced-order model."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from models.lunar_integrated_weevil_leg import (
    ContactModel,
    LegState,
    evaluate_leg_state,
    load_params,
)

OUT_PATH = ROOT / "verification" / "reports" / "benchmark_comparison.csv"


@dataclass(frozen=True)
class Scenario:
    name: str
    femur_pitch_deg: float
    tibia_theta_deg: float


def run(contact: ContactModel) -> list[tuple[str, float, bool]]:
    params = load_params()
    scenarios = [
        Scenario("flat", -10.0, 0.0),
        Scenario("slope_25deg", 5.0, 30.0),
        Scenario("sinkage_recovery", -30.0, 60.0),
    ]

    rows: list[tuple[str, float, bool]] = []
    for sc in scenarios:
        out = evaluate_leg_state(
            LegState(coxa_yaw_deg=0.0, femur_pitch_deg=sc.femur_pitch_deg, tibia_theta_deg=sc.tibia_theta_deg),
            params,
            contact,
        )
        rows.append((sc.name, out.traction_n, out.reachable and out.traction_n > 1.0))
    return rows


def main() -> int:
    original = run(ContactModel(regolith_mu=0.55, internal_mu=0.02))
    patched = run(ContactModel(regolith_mu=0.55, internal_mu=0.004))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario", "original_traction_n", "patched_traction_n", "original_success", "patched_success"])
        for o, p in zip(original, patched):
            writer.writerow([o[0], round(o[1], 4), round(p[1], 4), o[2], p[2]])

    print(f"Wrote {OUT_PATH}")
    for o, p in zip(original, patched):
        print(f"{o[0]}: original={o[1]:.3f}N patched={p[1]:.3f}N")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
