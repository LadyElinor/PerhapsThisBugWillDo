#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

REPORT_DIR = Path("verification/reports")
HISTORY_CSV = REPORT_DIR / "copilot_trend_history.csv"


def _to_int(v: str) -> int:
    return int(float(v))


def main() -> None:
    if not HISTORY_CSV.exists():
        raise FileNotFoundError(f"missing trend history: {HISTORY_CSV}")

    rows = []
    with HISTORY_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    current = rows[-1]
    previous = rows[-2] if len(rows) >= 2 else None

    cur_high = _to_int(current.get("high", "0"))
    cur_score = _to_int(current.get("weighted_score", "0"))

    if previous is None:
        trend_pass = True
        delta_high = 0
        delta_score = 0
        note = "first trend sample"
    else:
        prev_high = _to_int(previous.get("high", "0"))
        prev_score = _to_int(previous.get("weighted_score", "0"))
        delta_high = cur_high - prev_high
        delta_score = cur_score - prev_score
        trend_pass = (delta_high <= 1) and (delta_score <= 5)
        note = "ok" if trend_pass else "regression spike detected"

    out_csv = REPORT_DIR / "copilot_trend_check.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "current_timestamp_utc",
                "current_high",
                "current_weighted_score",
                "delta_high",
                "delta_weighted_score",
                "pass",
                "note",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "current_timestamp_utc": current.get("timestamp_utc", ""),
                "current_high": cur_high,
                "current_weighted_score": cur_score,
                "delta_high": delta_high,
                "delta_weighted_score": delta_score,
                "pass": trend_pass,
                "note": note,
            }
        )

    out_md = REPORT_DIR / "copilot_trend_check.md"
    lines = [
        "# Copilot Trend Check",
        "",
        f"- current timestamp: {current.get('timestamp_utc', '')}",
        f"- current high findings: {cur_high}",
        f"- current weighted score: {cur_score}",
        f"- delta high: {delta_high}",
        f"- delta weighted score: {delta_score}",
        f"- status: **{'PASS' if trend_pass else 'FAIL'}**",
        f"- note: {note}",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print(f"STATUS={'pass' if trend_pass else 'fail'}")


if __name__ == "__main__":
    main()
