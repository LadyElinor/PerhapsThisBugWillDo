#!/usr/bin/env python3
"""Validate Phase 2 export bundle presence and basic freshness."""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

REQUIRED = [
    Path("cad/export/Phase2_Templates.FCStd"),
    Path("cad/export/weevil_leg_module_ap242.step"),
    Path("cad/export/phase2_export_receipt.md"),
]

FRESH_HOURS = 24 * 7  # one week freshness window


def main() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    passed = 0

    for p in REQUIRED:
        exists = p.exists()
        fresh = False
        age_hours = None
        if exists:
            mtime = dt.datetime.fromtimestamp(p.stat().st_mtime, tz=dt.timezone.utc)
            age_hours = (now - mtime).total_seconds() / 3600.0
            fresh = age_hours <= FRESH_HOURS
        ok = bool(exists and fresh)
        passed += int(ok)
        rows.append(
            {
                "artifact": str(p).replace('\\', '/'),
                "exists": exists,
                "age_hours": "" if age_hours is None else round(age_hours, 2),
                "fresh_lte_168h": fresh,
                "pass": ok,
            }
        )

    out_dir = Path("verification/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "phase2_export_bundle.csv"
    md_path = out_dir / "phase2_export_bundle.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["artifact", "exists", "age_hours", "fresh_lte_168h", "pass"])
        w.writeheader()
        w.writerows(rows)

    status = "pass" if passed == len(REQUIRED) else "fail"
    lines = [
        "# Phase 2 Export Bundle Validation",
        "",
        f"- total: {len(REQUIRED)}",
        f"- passed: {passed}",
        f"- freshness_window_hours: {FRESH_HOURS}",
        f"- status: **{status.upper()}**",
        "",
        "| artifact | exists | age_hours | fresh<=168h | pass |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['artifact']} | {int(bool(r['exists']))} | {r['age_hours']} | {int(bool(r['fresh_lte_168h']))} | {int(bool(r['pass']))} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
