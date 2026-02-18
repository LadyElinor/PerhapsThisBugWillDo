#!/usr/bin/env python3
"""Generate FreeCAD parameter CSVs from cad/weevil_leg_params.yaml.

Outputs:
- cad/freecad_spreadsheet_template.csv
- cad/phase2_template_aliases.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from simple_yaml import load_yaml_text

ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = ROOT / "cad"
YAML_PATH = CAD_DIR / "weevil_leg_params.yaml"
BASE_CSV_PATH = CAD_DIR / "freecad_spreadsheet_template.csv"
PHASE2_CSV_PATH = CAD_DIR / "phase2_template_aliases.csv"

BASE_FIELDS = ["alias", "value", "unit", "notes"]


def unit_for(alias: str, value: Any) -> str:
    if alias.endswith("_mm"):
        return "mm"
    if alias.endswith("_kg"):
        return "kg"
    if alias.endswith("_deg"):
        return "deg"
    if alias.endswith("_N"):
        return "N"
    if alias.endswith("_Wh"):
        return "Wh"
    if alias.endswith("_m2"):
        return "m^2"
    if alias.endswith("_mm_per_rev"):
        return "mm/rev"
    if alias.endswith("_Nm_per_rad"):
        return "Nm/rad"
    if alias.endswith("_Nms_per_rad"):
        return "Nms/rad"
    if isinstance(value, bool):
        return "bool"
    return ""


def flatten(prefix: str, obj: Any, rows: list[dict[str, Any]]) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            next_prefix = f"{prefix}_{key}" if prefix else key
            flatten(next_prefix, val, rows)
        return

    if isinstance(obj, list) and len(obj) == 2 and prefix.endswith("_range_deg"):
        rows.append(
            {
                "alias": prefix.replace("_range_deg", "_min_deg"),
                "value": obj[0],
                "unit": "deg",
                "notes": "Auto-generated from YAML range lower bound",
            }
        )
        rows.append(
            {
                "alias": prefix.replace("_range_deg", "_max_deg"),
                "value": obj[1],
                "unit": "deg",
                "notes": "Auto-generated from YAML range upper bound",
            }
        )
        return

    rows.append(
        {
            "alias": prefix,
            "value": obj,
            "unit": unit_for(prefix, obj),
            "notes": "Auto-generated from cad/weevil_leg_params.yaml",
        }
    )


def read_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    return load_yaml_text(text)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BASE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def phase2_defaults() -> list[dict[str, Any]]:
    defaults = [
        ("spline_tooth_count", 20, "count", "Standard 20T servo spline"),
        ("spline_major_d_mm", 4.9, "mm", "Template major diameter"),
        ("spline_minor_d_mm", 3.8, "mm", "Template minor diameter"),
        ("spline_hub_thickness_mm", 4.0, "mm", "Template hub thickness"),
        ("spline_adapter_od_mm", 10.0, "mm", "Adapter outer diameter"),
        ("spline_bolt_circle_mm", 8.0, "mm", "Adapter bolt circle"),
        ("spline_bolt_d_mm", 2.0, "mm", "Adapter bolt diameter"),
        ("flange_od_mm", 28.0, "mm", "Pivot flange outer diameter"),
        ("flange_id_mm", 12.2, "mm", "Pivot flange inner diameter"),
        ("flange_thickness_mm", 4.5, "mm", "Pivot flange thickness"),
        ("flange_bcd_mm", 22.0, "mm", "Pivot flange bolt-circle"),
        ("flange_hole_count", 4, "count", "Pivot flange hole count"),
        ("flange_hole_d_mm", 3.2, "mm", "Pivot flange hole diameter"),
        ("servo_mount_width_mm", 28.0, "mm", "Servo mount width"),
        ("servo_mount_height_mm", 32.0, "mm", "Servo mount height"),
        ("servo_mount_thickness_mm", 3.0, "mm", "Servo mount thickness"),
        ("servo_hole_pitch_x_mm", 23.0, "mm", "Servo hole pitch X"),
        ("servo_hole_pitch_y_mm", 10.0, "mm", "Servo hole pitch Y"),
        ("servo_hole_d_mm", 2.2, "mm", "Servo hole diameter"),
        ("servo_axis_offset_mm", 8.0, "mm", "Servo axis offset"),
        ("ra_leg_a_mm", 30.0, "mm", "Right-angle mount leg A"),
        ("ra_leg_b_mm", 24.0, "mm", "Right-angle mount leg B"),
        ("ra_thickness_mm", 3.0, "mm", "Right-angle thickness"),
        ("ra_gusset_thickness_mm", 2.5, "mm", "Right-angle gusset"),
        ("ra_hole_d_mm", 2.2, "mm", "Right-angle hole diameter"),
        ("ra_hole_pitch_mm", 12.0, "mm", "Right-angle hole pitch"),
        ("lever_length_mm", 25.0, "mm", "Actuation lever length"),
        ("lever_width_mm", 8.0, "mm", "Actuation lever width"),
        ("lever_thickness_mm", 3.0, "mm", "Actuation lever thickness"),
        ("lever_hub_d_mm", 10.0, "mm", "Actuation lever hub diameter"),
        ("lever_hub_thickness_mm", 4.0, "mm", "Actuation lever hub thickness"),
        ("lever_tip_hole_d_mm", 2.0, "mm", "Actuation lever tip hole"),
    ]
    return [{"alias": a, "value": v, "unit": u, "notes": n} for a, v, u, n in defaults]


def main() -> None:
    params = read_yaml(YAML_PATH)
    rows: list[dict[str, Any]] = []
    flatten("", params, rows)
    write_csv(BASE_CSV_PATH, rows)
    write_csv(PHASE2_CSV_PATH, phase2_defaults())
    print(f"Wrote {BASE_CSV_PATH}")
    print(f"Wrote {PHASE2_CSV_PATH}")


if __name__ == "__main__":
    main()
