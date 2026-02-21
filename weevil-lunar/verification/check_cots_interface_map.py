#!/usr/bin/env python3
"""Validate COTS interface map completeness for Phase 2 CAD handoff."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "cad" / "interfaces" / "phase2_cots_interface_map.csv"

REQUIRED_COLUMNS = {
    "interface_id",
    "domain",
    "cad_alias_group",
    "market_part_class",
    "nominal_standard",
    "critical_dims",
    "notes",
}

REQUIRED_INTERFACES = {
    "servo_mount_plate",
    "spline_adapter_20t",
    "pivot_flange_4xM3",
    "right_angle_mount",
    "actuation_lever_25mm",
    "shaft_interface_hex",
    "bearing_seat_standard",
    "chain_sprocket_stage",
    "gearbox_mount_pattern",
    "hub_to_wheel_interface",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", dest="map_path", default=str(DEFAULT_MAP))
    args = ap.parse_args()

    path = Path(args.map_path)
    if not path.exists():
        raise SystemExit(f"Missing COTS interface map: {path}")

    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    if not rows:
        raise SystemExit("COTS interface map has no rows")

    columns = set(rows[0].keys())
    missing_cols = REQUIRED_COLUMNS - columns
    if missing_cols:
        raise SystemExit(f"Missing required columns: {sorted(missing_cols)}")

    ids = {r["interface_id"].strip() for r in rows}
    missing_ids = REQUIRED_INTERFACES - ids
    if missing_ids:
        raise SystemExit(f"Missing required interfaces: {sorted(missing_ids)}")

    for idx, row in enumerate(rows, start=2):
        for col in REQUIRED_COLUMNS:
            if not row.get(col, "").strip():
                raise SystemExit(f"Row {idx}: empty required field '{col}'")

    print("COTS interface map check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
