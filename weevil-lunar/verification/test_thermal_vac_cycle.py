#!/usr/bin/env python3
"""Thermal-vac cycle placeholder harness (v0.1 model-based)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ThermalRun:
    cycle_id: int
    min_temp_c: float
    max_temp_c: float
    thermal_shutdowns: int


def evaluate(run: ThermalRun) -> bool:
    # initial envelope placeholder
    in_band = (run.min_temp_c >= -120.0) and (run.max_temp_c <= 80.0)
    return in_band and (run.thermal_shutdowns == 0)


def main() -> None:
    runs = [
        ThermalRun(1, -85.0, 62.0, 0),
        ThermalRun(2, -92.0, 71.0, 0),
        ThermalRun(3, -101.0, 76.0, 0),
    ]

    out_rows = []
    passes = 0
    for r in runs:
        ok = evaluate(r)
        passes += int(ok)
        out_rows.append(
            {
                "cycle_id": r.cycle_id,
                "min_temp_c": r.min_temp_c,
                "max_temp_c": r.max_temp_c,
                "thermal_shutdowns": r.thermal_shutdowns,
                "pass": ok,
            }
        )

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "thermal_vac_cycle.csv"
    md_path = report_dir / "thermal_vac_cycle.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    summary = "pass" if passes == len(runs) else "fail"
    md_lines = [
        "# Thermal-Vac Cycle Test (v0.1)",
        "",
        "Model-based placeholder pending chamber campaign.",
        "",
        f"- total: {len(runs)}",
        f"- passed: {passes}",
        f"- status: **{summary.upper()}**",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={summary}")


if __name__ == "__main__":
    main()
