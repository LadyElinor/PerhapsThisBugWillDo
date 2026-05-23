#!/usr/bin/env python3
"""Validate Phase 2 export bundle presence and basic structure."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "verification" / "reports"

REQUIRED = [
    Path("cad/export/Phase2_Templates.FCStd"),
    Path("cad/export/weevil_leg_module_ap242.step"),
    Path("cad/export/phase2_export_receipt.md"),
]


def main() -> None:
    rows = []
    passed = 0

    for p in REQUIRED:
        exists = p.exists()
        size_bytes = p.stat().st_size if exists else None
        nonempty = bool(exists and size_bytes and size_bytes > 0)
        ok = bool(exists and nonempty)
        passed += int(ok)
        rows.append(
            {
                "artifact": str(p).replace('\\', '/'),
                "exists": exists,
                "size_bytes": "" if size_bytes is None else size_bytes,
                "nonempty": nonempty,
                "pass": ok,
            }
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REPORT_DIR / "phase2_export_bundle.csv"
    md_path = REPORT_DIR / "phase2_export_bundle.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["artifact", "exists", "size_bytes", "nonempty", "pass"])
        w.writeheader()
        w.writerows(rows)

    status = "pass" if passed == len(REQUIRED) else "fail"
    lines = [
        "# Phase 2 Export Bundle Validation",
        "",
        f"- total: {len(REQUIRED)}",
        f"- passed: {passed}",
        "- policy: existence + non-empty structure check",
        f"- status: **{status.upper()}**",
        "",
        "| artifact | exists | size_bytes | nonempty | pass |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['artifact']} | {int(bool(r['exists']))} | {r['size_bytes']} | {int(bool(r['nonempty']))} | {int(bool(r['pass']))} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
