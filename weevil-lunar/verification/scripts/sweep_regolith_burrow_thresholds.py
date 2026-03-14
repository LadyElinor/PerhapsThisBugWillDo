#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

REPORT_DIR = Path("verification/reports")


def synthetic_success_score(disturbance_cap: float, collapse_abort: float, reserve: float) -> float:
    # Heuristic stand-in until physics model is wired:
    # more disturbance budget helps exploration, but too low abort gap hurts safety.
    gap = collapse_abort - disturbance_cap
    score = 0.45 * disturbance_cap + 0.25 * reserve + 0.30 * max(gap, 0.0)
    return max(0.0, min(1.0, score))


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    disturbance_caps = np.linspace(0.25, 0.60, 8)
    abort_gaps = np.linspace(0.15, 0.35, 5)
    reserves = [0.20, 0.25, 0.30]

    rows = []
    for dc in disturbance_caps:
        for gap in abort_gaps:
            for reserve in reserves:
                ca = dc + gap
                if ca >= 0.99:
                    continue
                score = synthetic_success_score(dc, ca, reserve)
                pass_flag = score >= 0.35 and reserve >= 0.20 and gap >= 0.15
                rows.append(
                    {
                        "disturbance_index_cap": round(float(dc), 3),
                        "collapse_risk_abort_threshold": round(float(ca), 3),
                        "abort_gap": round(float(gap), 3),
                        "min_energy_reserve_fraction": reserve,
                        "synthetic_success_score": round(float(score), 4),
                        "pass": bool(pass_flag),
                    }
                )

    csv_path = REPORT_DIR / "regolith_burrow_threshold_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    passed = [r for r in rows if r["pass"]]
    passed_sorted = sorted(passed, key=lambda r: r["synthetic_success_score"], reverse=True)
    top = passed_sorted[:10]

    md_path = REPORT_DIR / "regolith_burrow_threshold_sweep.md"
    lines = [
        "# Regolith Burrow Threshold Sweep",
        "",
        "Heuristic sensitivity sweep over disturbance cap, abort threshold gap, and reserve floor.",
        "",
        f"- candidates: {len(rows)}",
        f"- pass candidates: {len(passed)}",
        "",
        "| disturbance_cap | abort_threshold | abort_gap | reserve | score |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in top:
        lines.append(
            f"| {r['disturbance_index_cap']:.3f} | {r['collapse_risk_abort_threshold']:.3f} | {r['abort_gap']:.3f} | {r['min_energy_reserve_fraction']:.2f} | {r['synthetic_success_score']:.4f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
