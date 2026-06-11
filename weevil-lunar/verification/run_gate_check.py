#!/usr/bin/env python3
"""Integrated gate check for Weevil-Lunar verification, driven by receipts.

Consumes verification/reports/receipts.json (produced by
run_verification_suite.py) and rolls harness statuses up into subsystem
gate classes. With --strict, exits nonzero unless every class is `pass` --
this is the CI enforcement point.

Historical note: the previous version of this script read the report CSVs
directly and hardcoded a column literally named `pass`, which misreported
schema-divergent reports (offplane_impulse_recovery, sensitivity sweeps)
as failures, and it could not fail a build. Status reading now lives in
receipts.py under the contracts declared in harness_manifest.yaml.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import WEEVIL_ROOT, combine, load_receipts  # noqa: E402

# Subsystem gate classes -> harnesses whose receipts they roll up.
CLASSES: dict[str, list[str]] = {
    "mobility": [
        "steep_slope_state_machine",
        "duty_cycle_cadence_envelope",
        "offplane_impulse_recovery",
        "rover_informed_profile",
    ],
    "foot": ["steep_slope_state_machine", "offplane_coupling_index", "contact_package"],
    "autonomy": ["steep_slope_state_machine", "autonomy_health_planner", "stance_phase_detection"],
    "dust": ["dust_ingress_endurance"],
    "thermal": ["thermal_vac_cycle", "rover_informed_profile"],
    "actuation": ["actuation_bench"],
    "power": ["power_comms_profile", "rover_informed_profile"],
    "comms": ["power_comms_profile", "rover_informed_profile"],
    "gait_phase": ["stance_phase_detection", "duty_cycle_cadence_envelope"],
    "coupling": [
        "offplane_coupling_index",
        "offplane_impulse_recovery",
        "axis_orthogonality_sensitivity",
    ],
    "cad_phase2": ["phase2_cad_artifacts", "phase2_export_bundle"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero unless every gate class is `pass` (CI mode)",
    )
    args = parser.parse_args()

    try:
        receipts = load_receipts()
    except FileNotFoundError as exc:
        print(f"GATE CHECK ERROR: {exc}")
        return 1 if args.strict else 0

    harnesses = receipts.get("harnesses", {})
    out_rows: list[dict[str, str]] = []
    for cls, members in CLASSES.items():
        statuses, details = [], []
        for name in members:
            h = harnesses.get(name)
            status = h["status"] if h else "missing"
            statuses.append(status)
            details.append(f"{name}:{status}")
        out_rows.append(
            {"class": cls, "status": combine(statuses), "details": "; ".join(details)}
        )

    report_dir = WEEVIL_ROOT / "verification" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    csv_path = report_dir / "gate_check.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["class", "status", "details"], lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    md_lines = [
        "# Integrated Gate Check",
        "",
        f"- receipts commit: {receipts.get('git_commit', 'unknown')}",
        f"- receipts generated: {receipts.get('generated_at', 'unknown')}",
        "",
        "| class | status | details |",
        "|---|---|---|",
    ]
    for r in out_rows:
        md_lines.append(f"| {r['class']} | {r['status']} | {r['details']} |")
    md_path = report_dir / "gate_check.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")

    bad = [r for r in out_rows if r["status"] != "pass"]
    for r in bad:
        print(f"GATE NOT PASS: {r['class']} -> {r['status']} ({r['details']})")
    if args.strict and bad:
        print(f"STRICT GATE: {len(bad)} class(es) not passing")
        return 1
    print("STATUS=" + ("pass" if not bad else "fail"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
