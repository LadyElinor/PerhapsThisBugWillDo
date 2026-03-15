#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

REPORT_DIR = Path("verification/reports")
ERROR_CSV = REPORT_DIR / "bench_model_error.csv"
HISTORY_CSV = REPORT_DIR / "bench_model_error_trend_history.csv"
CHECK_CSV = REPORT_DIR / "bench_model_error_trend_check.csv"
CHECK_MD = REPORT_DIR / "bench_model_error_trend_check.md"


def _f(v: str) -> float:
    return float((v or "0").strip())


def main() -> None:
    if not ERROR_CSV.exists():
        raise FileNotFoundError(f"missing {ERROR_CSV}")

    with ERROR_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("empty bench_model_error.csv")

    mean_force = sum(_f(r.get("force_mae_N")) for r in rows) / len(rows)
    mean_slip = sum(_f(r.get("slip_mae_mm")) for r in rows) / len(rows)
    mean_stiff = sum(_f(r.get("stiffness_mae_N_per_mm")) for r in rows) / len(rows)
    fail_count = sum(1 for r in rows if str(r.get("pass", "")).lower() not in {"true", "1"})

    snapshot = {
        "sample_index": 0,
        "strategy_count": len(rows),
        "mean_force_mae_N": round(mean_force, 6),
        "mean_slip_mae_mm": round(mean_slip, 6),
        "mean_stiffness_mae_N_per_mm": round(mean_stiff, 6),
        "fail_count": fail_count,
    }

    existing = []
    if HISTORY_CSV.exists():
        with HISTORY_CSV.open("r", encoding="utf-8", newline="") as f:
            existing = list(csv.DictReader(f))

    snapshot["sample_index"] = len(existing) + 1

    fieldnames = [
        "sample_index",
        "strategy_count",
        "mean_force_mae_N",
        "mean_slip_mae_mm",
        "mean_stiffness_mae_N_per_mm",
        "fail_count",
    ]
    with HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not existing:
            w.writeheader()
        w.writerow(snapshot)

    if existing:
        prev = existing[-1]
        d_force = snapshot["mean_force_mae_N"] - _f(prev.get("mean_force_mae_N"))
        d_slip = snapshot["mean_slip_mae_mm"] - _f(prev.get("mean_slip_mae_mm"))
        d_stiff = snapshot["mean_stiffness_mae_N_per_mm"] - _f(prev.get("mean_stiffness_mae_N_per_mm"))
        d_fail = snapshot["fail_count"] - int(float(prev.get("fail_count", "0")))
    else:
        d_force = d_slip = d_stiff = 0.0
        d_fail = 0

    trend_pass = (d_fail <= 0) and (d_force <= 0.2) and (d_slip <= 0.1) and (d_stiff <= 0.1)

    with CHECK_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "sample_index",
                "delta_force_mae_N",
                "delta_slip_mae_mm",
                "delta_stiffness_mae_N_per_mm",
                "delta_fail_count",
                "pass",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "sample_index": snapshot["sample_index"],
                "delta_force_mae_N": round(d_force, 6),
                "delta_slip_mae_mm": round(d_slip, 6),
                "delta_stiffness_mae_N_per_mm": round(d_stiff, 6),
                "delta_fail_count": d_fail,
                "pass": trend_pass,
            }
        )

    CHECK_MD.write_text(
        "\n".join(
            [
                "# Bench Model Error Trend Check",
                "",
                f"- sample index: {snapshot['sample_index']}",
                f"- delta force MAE (N): {round(d_force, 6)}",
                f"- delta slip MAE (mm): {round(d_slip, 6)}",
                f"- delta stiffness MAE (N/mm): {round(d_stiff, 6)}",
                f"- delta fail count: {d_fail}",
                f"- status: **{'PASS' if trend_pass else 'FAIL'}**",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {HISTORY_CSV}")
    print(f"Wrote {CHECK_CSV}")
    print(f"Wrote {CHECK_MD}")


if __name__ == "__main__":
    main()
