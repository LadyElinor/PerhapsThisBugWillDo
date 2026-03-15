#!/usr/bin/env python3
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

INPUT = Path("verification/templates/uncertainty_ledger.csv")
OUT_DIR = Path("verification/reports")
MAX_STALE_DAYS = 14


def _parse_iso(ts: str) -> datetime | None:
    s = (ts or "").strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        raise FileNotFoundError(f"missing {INPUT}")

    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    now = datetime.now(timezone.utc)
    out_rows = []
    overall_pass = True

    for r in rows:
        item_id = (r.get("item_id") or "").strip()
        bucket = (r.get("bucket") or "").strip().lower()
        impact = (r.get("impact") or "").strip().lower()
        owner = (r.get("owner") or "").strip()
        next_measurement = (r.get("next_measurement") or "").strip()
        last_updated = _parse_iso(r.get("last_updated_utc") or "")

        stale = False
        if last_updated is None:
            stale = True
        else:
            age_days = (now - last_updated).total_seconds() / 86400.0
            stale = age_days > MAX_STALE_DAYS

        high_impact_unknown = bucket == "unknown" and impact == "high"
        owner_ok = bool(owner and owner.lower() != "unassigned")
        measurement_ok = bool(next_measurement)

        if high_impact_unknown and (not owner_ok or not measurement_ok):
            row_pass = False
        else:
            row_pass = not stale

        overall_pass = overall_pass and row_pass
        out_rows.append(
            {
                "item_id": item_id,
                "bucket": bucket,
                "impact": impact,
                "high_impact_unknown": high_impact_unknown,
                "owner_ok": owner_ok,
                "next_measurement_ok": measurement_ok,
                "stale": stale,
                "pass": row_pass,
            }
        )

    out_csv = OUT_DIR / "uncertainty_ledger_check.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "item_id",
                "bucket",
                "impact",
                "high_impact_unknown",
                "owner_ok",
                "next_measurement_ok",
                "stale",
                "pass",
            ],
        )
        w.writeheader()
        w.writerows(out_rows)

    out_md = OUT_DIR / "uncertainty_ledger.md"
    lines = [
        "# Uncertainty Ledger Check",
        "",
        f"- items evaluated: {len(out_rows)}",
        f"- stale threshold (days): {MAX_STALE_DAYS}",
        f"- status: **{'PASS' if overall_pass else 'FAIL'}**",
        "",
        "| item | bucket | impact | high-impact unknown | owner ok | next measurement ok | stale | pass |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in out_rows:
        lines.append(
            f"| {r['item_id']} | {r['bucket']} | {r['impact']} | {r['high_impact_unknown']} | {r['owner_ok']} | {r['next_measurement_ok']} | {r['stale']} | {r['pass']} |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print(f"STATUS={'pass' if overall_pass else 'fail'}")


if __name__ == "__main__":
    main()
