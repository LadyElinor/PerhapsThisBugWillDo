#!/usr/bin/env python3
"""Parameter sensitivity sweep for directional slope margin robustness."""

from __future__ import annotations

import csv
import itertools
import math
import sys
from pathlib import Path


def margin_down(traction_n: float, normal_n: float, slope_deg: float) -> float:
    demand = normal_n * math.sin(math.radians(slope_deg))
    return traction_n / demand if demand > 0 else float("inf")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from models.lunar_integrated_weevil_leg import (  # noqa: WPS433
        ContactModel,
        LegState,
        evaluate_leg_state,
        load_params,
    )

    p = load_params()
    out_dir = Path("results/sensitivity")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "parameter_sweep.csv"
    md_path = out_dir / "parameter_sweep.md"

    cohesion_mu = [0.45, 0.55, 0.65]
    internal_mu = [0.002, 0.004, 0.01]
    gravity_scale = [0.9, 1.0, 1.1]
    preload = [0.9 * p.preload_n, p.preload_n, 1.1 * p.preload_n]

    rows: list[dict[str, float | bool]] = []
    for mu, imu, gscale, pre in itertools.product(cohesion_mu, internal_mu, gravity_scale, preload):
        state = LegState(0.0, 0.0, 0.0)
        result = evaluate_leg_state(state, p, ContactModel(regolith_mu=mu, internal_mu=imu))
        # gravity scaling proxy applied to traction demand-side for robustness envelope
        m45 = margin_down(result.traction_n * gscale, pre, 45.0)
        rows.append(
            {
                "regolith_mu": mu,
                "internal_mu": imu,
                "gravity_scale": gscale,
                "preload_n": pre,
                "margin_45deg": m45,
                "pass_margin": m45 >= 1.05,
            }
        )

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    passes = sum(1 for r in rows if r["pass_margin"])
    lines = [
        "# Parameter Sweep Robustness Report",
        "",
        "Sensitivity sweep over regolith/contact and preload/gravity",
        "scaling around nominal settings.",
        "",
        f"- total_cases: {len(rows)}",
        f"- pass_cases (margin>=1.05): {passes}",
        f"- pass_rate: {passes/len(rows):.2%}",
        "",
        "## Notes",
        "- This is a reduced-order robustness screen, not full terramechanics calibration.",
        "- Next step: compare against Bekker/Wong-Reece baseline envelopes and simulant ranges.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
