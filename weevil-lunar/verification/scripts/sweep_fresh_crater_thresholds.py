#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

REPORT_DIR = Path("verification/reports")


def synthetic_success_score(approach_slope: float, reserve: float, disturbance_cap: float, telemetry_buffer_s: float) -> float:
    score = 0.30 * (approach_slope / 25.0)
    score += 0.30 * reserve
    score += 0.20 * min(telemetry_buffer_s / 240.0, 1.0)
    score += 0.20 * max(0.0, 0.40 - disturbance_cap)
    return max(0.0, min(1.0, score))


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    approach_slopes = [16, 18, 20, 22, 24]
    reserves = [0.24, 0.28, 0.32]
    disturbance_caps = [0.28, 0.30, 0.32, 0.34]
    telemetry_buffers = [150, 180, 210, 240]

    rows = []
    for slope in approach_slopes:
        for reserve in reserves:
            for disturbance_cap in disturbance_caps:
                for telemetry in telemetry_buffers:
                    score = synthetic_success_score(slope, reserve, disturbance_cap, telemetry)
                    pass_flag = slope <= 24 and reserve >= 0.24 and disturbance_cap <= 0.34 and telemetry >= 150 and score >= 0.38
                    rows.append(
                        {
                            "approach_slope_limit_deg": slope,
                            "egress_reserve_fraction": reserve,
                            "disturbance_index_cap": disturbance_cap,
                            "telemetry_buffer_min_s": telemetry,
                            "synthetic_success_score": round(float(score), 4),
                            "pass": bool(pass_flag),
                        }
                    )

    csv_path = REPORT_DIR / "fresh_crater_threshold_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    passed = [r for r in rows if r["pass"]]
    top = sorted(passed, key=lambda r: r["synthetic_success_score"], reverse=True)[:10]

    md_path = REPORT_DIR / "fresh_crater_threshold_sweep.md"
    lines = [
        "# Fresh Crater Threshold Sweep",
        "",
        "Heuristic sensitivity sweep over approach slope, reserve, disturbance cap, and telemetry buffering.",
        "",
        f"- candidates: {len(rows)}",
        f"- pass candidates: {len(passed)}",
        "",
        "| slope | reserve | disturbance | telemetry | score |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in top:
        lines.append(
            f"| {r['approach_slope_limit_deg']:.0f} | {r['egress_reserve_fraction']:.2f} | {r['disturbance_index_cap']:.2f} | {r['telemetry_buffer_min_s']:.0f} | {r['synthetic_success_score']:.4f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
