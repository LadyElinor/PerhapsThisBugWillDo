#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

REPORT_DIR = Path("verification/reports")
STATUS_CSV = REPORT_DIR / "copilot_status.csv"
HISTORY_CSV = REPORT_DIR / "copilot_trend_history.csv"


def main() -> None:
    if not STATUS_CSV.exists():
        raise FileNotFoundError(f"missing status file: {STATUS_CSV}")

    with STATUS_CSV.open("r", encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))

    fieldnames = [
        "timestamp_utc",
        "total_findings",
        "high",
        "medium",
        "low",
        "weighted_score",
        "max_weighted_score",
        "pass",
    ]

    exists = HISTORY_CSV.exists()
    with HISTORY_CSV.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"Appended {HISTORY_CSV}")


if __name__ == "__main__":
    main()
