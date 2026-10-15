#!/usr/bin/env python3
"""Inspect the historical handoff; known incompleteness remains visible in receipts."""
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "scripts"))
from bundle_inspection import inspect_bundle


def main() -> None:
    rows = inspect_bundle(ROOT / "cad" / "export")
    report_dir = ROOT / "verification" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "phase2_export_bundle.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate_id", "passed", "detail"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# Historical CAD bundle inspection", "",
             "Format/completeness screening only. Native geometry is checked separately by freecad_audit.py.", "",
             "| Gate | Actual pass | Detail |", "|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['gate_id']} | {row['passed']} | {row['detail']} |")
    (report_dir / "phase2_export_bundle.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path}; actual pass={sum(row['passed'] for row in rows)}/{len(rows)}")


if __name__ == "__main__":
    main()
