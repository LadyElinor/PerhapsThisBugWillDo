#!/usr/bin/env python3
"""Integrated gate check for Weevil-Lunar verification reports."""

from __future__ import annotations

import csv
from pathlib import Path


REPORTS = {
    "mobility": [
        "steep_slope_state_machine.csv",
    ],
    "foot": [
        "steep_slope_state_machine.csv",
    ],
    "autonomy": [
        "steep_slope_state_machine.csv",
        "autonomy_health_planner.csv",
    ],
    "dust": [
        "dust_ingress_endurance.csv",
    ],
    "thermal": [
        "thermal_vac_cycle.csv",
    ],
    "actuation": [
        "actuation_bench.csv",
    ],
    "power": [
        "power_comms_profile.csv",
    ],
    "comms": [
        "power_comms_profile.csv",
    ],
}


def status_from_csv(path: Path) -> str:
    if not path.exists():
        return "missing"
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
    if not rows:
        return "missing"
    if all(str(r.get("pass", "")).lower() in {"true", "1"} for r in rows):
        return "pass"
    if any(str(r.get("pass", "")).lower() in {"true", "1"} for r in rows):
        return "partial"
    return "fail"


def main() -> None:
    report_dir = Path("verification/reports")
    out_rows = []
    for cls, files in REPORTS.items():
        file_statuses = []
        for fn in files:
            s = status_from_csv(report_dir / fn)
            file_statuses.append((fn, s))
        if all(s == "pass" for _, s in file_statuses):
            cls_status = "pass"
        elif any(s == "missing" for _, s in file_statuses):
            cls_status = "missing"
        elif any(s in {"fail", "partial"} for _, s in file_statuses):
            cls_status = "partial"
        else:
            cls_status = "unknown"
        out_rows.append({"class": cls, "status": cls_status, "details": "; ".join([f"{f}:{s}" for f, s in file_statuses])})

    csv_path = report_dir / "gate_check.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["class", "status", "details"])
        w.writeheader()
        w.writerows(out_rows)

    md_lines = ["# Integrated Gate Check", "", "| class | status | details |", "|---|---|---|"]
    for r in out_rows:
        md_lines.append(f"| {r['class']} | {r['status']} | {r['details']} |")

    md_path = report_dir / "gate_check.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
