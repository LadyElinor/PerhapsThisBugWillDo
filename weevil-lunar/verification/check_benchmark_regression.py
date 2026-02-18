#!/usr/bin/env python3
"""Fail CI when benchmark traction regresses beyond threshold."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "verification" / "reports" / "benchmark_comparison.csv"
BASELINE = ROOT / "verification" / "baselines" / "benchmark_baseline.csv"
MAX_DROP_FRACTION = 0.10  # 10%


def load_rows(path: Path) -> dict[str, dict[str, float]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        out: dict[str, dict[str, float]] = {}
        for row in reader:
            scenario = row["scenario"]
            out[scenario] = {
                "original": float(row["original_traction_n"]),
                "patched": float(row["patched_traction_n"]),
            }
        return out


def main() -> int:
    if not REPORT.exists():
        raise SystemExit(f"Missing report: {REPORT}")

    report_rows = load_rows(REPORT)

    # Guard 1: patched should not drop >10% below original in same run.
    for scenario, vals in report_rows.items():
        floor = vals["original"] * (1.0 - MAX_DROP_FRACTION)
        if vals["patched"] < floor:
            raise SystemExit(
                f"Regression: scenario '{scenario}' patched={vals['patched']:.4f} "
                f"< allowed floor {floor:.4f} ({MAX_DROP_FRACTION:.0%} below original)"
            )

    # Guard 2: if baseline exists, patched should not drop >10% below baseline patched.
    if BASELINE.exists():
        baseline_rows = load_rows(BASELINE)
        for scenario, vals in report_rows.items():
            if scenario not in baseline_rows:
                continue
            baseline_patched = baseline_rows[scenario]["patched"]
            floor = baseline_patched * (1.0 - MAX_DROP_FRACTION)
            if vals["patched"] < floor:
                raise SystemExit(
                    f"Regression vs baseline: scenario '{scenario}' patched={vals['patched']:.4f} "
                    f"< baseline floor {floor:.4f}"
                )

    print("Benchmark regression checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
