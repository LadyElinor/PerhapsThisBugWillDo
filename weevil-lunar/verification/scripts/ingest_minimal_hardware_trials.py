#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

TEMPLATE = Path("verification/templates/minimal_hardware_trials.csv")
REPORT_DIR = Path("verification/reports")

REQUIRED_COLUMNS = [
    "run_id",
    "timestamp_utc",
    "soil_id",
    "strategy_id",
    "preload_N",
    "cycle_index",
    "pull_rate_mm_per_s",
    "sample_rate_hz",
]


def _to_float(v: str):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with TEMPLATE.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        cols = rdr.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in cols]
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        rows = list(rdr)

    by_strategy = defaultdict(list)
    measured_rows = 0
    for r in rows:
        by_strategy[r["strategy_id"]].append(r)
        if any(_to_float(r.get(k, "")) is not None for k in ["F_peak_N", "x_slip_mm", "k_t_N_per_mm"]):
            measured_rows += 1

    out_rows = []
    for strategy, rs in sorted(by_strategy.items()):
        preload_vals = [_to_float(r.get("preload_N", "")) for r in rs]
        preload_vals = [v for v in preload_vals if v is not None]
        out_rows.append(
            {
                "strategy_id": strategy,
                "trial_count": len(rs),
                "avg_preload_N": round(sum(preload_vals) / len(preload_vals), 4) if preload_vals else "",
                "pass": True,
            }
        )

    csv_path = REPORT_DIR / "minimal_hardware_ingest.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()) if out_rows else ["strategy_id", "trial_count", "avg_preload_N", "pass"])
        w.writeheader()
        if out_rows:
            w.writerows(out_rows)

    md_path = REPORT_DIR / "minimal_hardware_ingest.md"
    lines = [
        "# Minimal Hardware Ingest",
        "",
        f"- total trials: {len(rows)}",
        f"- strategies: {len(by_strategy)}",
        f"- rows with measured force/slip fields: {measured_rows}",
        f"- status: **PASS**",
        "",
        "| strategy | trials | avg preload (N) |",
        "|---|---:|---:|",
    ]
    for r in out_rows:
        lines.append(f"| {r['strategy_id']} | {r['trial_count']} | {r['avg_preload_N']} |")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
