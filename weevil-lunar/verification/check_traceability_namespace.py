#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

TRACE = Path("verification/requirements_traceability.csv")
ALIASES = Path("verification/requirement_aliases.csv")
REPORT_DIR = Path("verification/reports")

CANON_PREFIXES = {
    "REQ-LOCO-",
    "REQ-FOOT-",
    "REQ-AUTO-",
    "REQ-ACT-",
    "REQ-DUST-",
    "REQ-THERM-",
    "REQ-PWR-",
    "REQ-COMMS-",
    "REQ-CAD-",
    "REQ-BURROW-",
}


def is_canonical(req_id: str) -> bool:
    return any(req_id.startswith(p) for p in CANON_PREFIXES)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    alias_map: dict[str, str] = {}
    with ALIASES.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            alias_map[row["legacy_requirement_id"].strip()] = row["canonical_requirement_id"].strip()

    rows = []
    unknown = []

    with TRACE.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            req = row["requirement_id"].strip()
            canonical = req if is_canonical(req) else alias_map.get(req, "")
            ok = bool(canonical)
            rows.append(
                {
                    "requirement_id": req,
                    "canonical_requirement_id": canonical,
                    "pass": ok,
                }
            )
            if not ok:
                unknown.append(req)

    csv_path = REPORT_DIR / "traceability_namespace_check.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["requirement_id", "canonical_requirement_id", "pass"])
        w.writeheader()
        w.writerows(rows)

    passed = len(unknown) == 0
    md_path = REPORT_DIR / "traceability_namespace_check.md"
    lines = [
        "# Traceability Namespace Check",
        "",
        f"- rows checked: {len(rows)}",
        f"- unknown requirement IDs: {len(unknown)}",
        f"- status: **{'PASS' if passed else 'FAIL'}**",
        "",
    ]
    if unknown:
        lines.append("## Unknown IDs")
        for req in sorted(set(unknown)):
            lines.append(f"- `{req}`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={'pass' if passed else 'fail'}")


if __name__ == "__main__":
    main()
