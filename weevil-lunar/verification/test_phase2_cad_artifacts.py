#!/usr/bin/env python3
"""Check presence of phase-2 CAD planning/scaffold artifacts."""

from __future__ import annotations

import csv
from pathlib import Path


REQUIRED = [
    "cad/rover_freecad_mapping_phase2.md",
    "cad/reference/mrover_manifest.md",
    "cad/phase2_template_aliases.csv",
    "cad/phase2_freecad_import_rebuild.md",
    "cad/Phase2_Templates.FCMacro",
    "cad/Phase2_Export.FCMacro",
    "cad/phase2_integration_manifest.yaml",
    "cad/adapters/spline_20T_adapter_template.md",
    "cad/interfaces/pivot_flange_template.md",
    "cad/fixtures/servo_mount_template.md",
    "cad/fixtures/right_angle_mount_template.md",
    "cad/fixtures/actuation_lever_25mm_template.md",
    "cad/export/weevil_leg_module.urdf",
]


def main() -> None:
    root = Path('.')
    rows = []
    passes = 0
    for rel in REQUIRED:
        exists = (root / rel).exists()
        passes += int(exists)
        rows.append({"artifact": rel, "pass": exists})

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "phase2_cad_artifacts.csv"
    md_path = report_dir / "phase2_cad_artifacts.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["artifact", "pass"])
        w.writeheader()
        w.writerows(rows)

    status = "pass" if passes == len(REQUIRED) else "fail"
    md = [
        "# Phase 2 CAD Artifacts Check",
        "",
        f"- total: {len(REQUIRED)}",
        f"- passed: {passes}",
        f"- status: **{status.upper()}**",
        "",
        "| artifact | pass |",
        "|---|---:|",
    ]
    for r in rows:
        md.append(f"| {r['artifact']} | {int(bool(r['pass']))} |")
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
