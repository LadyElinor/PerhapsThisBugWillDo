#!/usr/bin/env python3
"""Build editable native PartDesign fixture concepts, without GUI dependencies.

This is a separated fixture layout, not an assembled rover. Native expressions
survive save/reopen without Python proxies. The adapter is explicitly a blank:
the repository does not specify a manufacturable spline tooth profile.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import PartDesign  # noqa: F401 -- registers native PartDesign object types

from generate_csvs_from_yaml import flatten, phase2_defaults, read_yaml

CAD = Path(__file__).resolve().parents[1]
BODY_NAMES = ["Body_AdapterBlank", "Body_PivotFlange", "Body_ServoMount", "Body_RightAngleMount", "Body_ActuationLever25"]


def feature(body, kind, name, expressions, rotation=None):
    obj = body.newObject("PartDesign::" + kind, name)
    if rotation is not None:
        obj.Placement.Rotation = rotation
    for prop, expression in expressions.items():
        obj.setExpression(prop, expression)
    obj.Refine = True
    body.Tip = obj
    body.Document.recompute()
    if obj.Shape.isNull() or "Invalid" in obj.State or "Error" in obj.State:
        raise ValueError(f"Cannot build {name}: {obj.State}")
    return obj


def cylinder(body, name, radius, height, cut=False, **position):
    expressions = {"Radius": radius, "Height": height}
    expressions.update({"Placement.Base." + axis: value for axis, value in position.items()})
    return feature(body, "SubtractiveCylinder" if cut else "AdditiveCylinder", name, expressions)


def box(body, name, length, width, height, **position):
    expressions = {"Length": length, "Width": width, "Height": height}
    expressions.update({"Placement.Base." + axis: value for axis, value in position.items()})
    return feature(body, "AdditiveBox", name, expressions)


def parameter_sheet(doc, params_path):
    rows = []
    flatten("", read_yaml(params_path), rows)
    rows.extend(phase2_defaults())
    # Explicit concept dimensions formerly embedded as numeric literals in the macro.
    rows.extend([
        {"alias": "servo_ear_depth_mm", "value": 14, "unit": "mm", "notes": "Inherited concept dimension"},
        {"alias": "servo_ear_height_ratio", "value": 0.6, "unit": "", "notes": "Inherited concept ratio"},
        {"alias": "servo_ear_base_ratio", "value": 0.2, "unit": "", "notes": "Inherited concept ratio"},
        {"alias": "ra_gusset_ratio", "value": 0.45, "unit": "", "notes": "Inherited concept ratio"},
        {"alias": "lever_tip_inset_mm", "value": 2.5, "unit": "mm", "notes": "Inherited concept dimension"},
    ])
    sheet = doc.addObject("Spreadsheet::Sheet", "Params")
    for index, row in enumerate(rows, 1):
        sheet.set(f"A{index}", row["alias"])
        value = str(row["value"])
        # CAD dimensions use explicit mm. Other source fields are retained as metadata.
        if row["unit"] == "mm":
            value += " mm"
        sheet.set(f"B{index}", value)
        sheet.setAlias(f"B{index}", row["alias"])
        sheet.set(f"C{index}", row["notes"])
    doc.recompute()
    return sheet


def build_document(params_path=CAD / "weevil_leg_params.yaml"):
    doc = App.newDocument("WeevilParametricFixtures")
    doc.addObject("App::FeaturePython", "DesignNotes")
    doc.DesignNotes.addProperty("App::PropertyString", "Status")
    doc.DesignNotes.Status = "Concept fixtures in a separated layout; not an assembled or manufacturing-qualified rover"
    doc.DesignNotes.addProperty("App::PropertyStringList", "Limitations")
    doc.DesignNotes.Limitations = [
        "Adapter is a cylindrical blank with a minor-diameter pilot bore; spline teeth are unspecified.",
        "Adapter bolt holes omitted: OD=10, BCD=8 and hole=2 mm imply zero outer ligament.",
        "Fixture geometry and layout do not establish materials, joint frames or load capacity.",
    ]
    doc.DesignNotes.addProperty("App::PropertyString", "ParameterSHA256")
    doc.DesignNotes.ParameterSHA256 = hashlib.sha256(Path(params_path).read_bytes()).hexdigest()
    parameter_sheet(doc, params_path)
    bodies = [doc.addObject("PartDesign::Body", name) for name in BODY_NAMES]
    for index, body in enumerate(bodies):
        body.Label = body.Name.removeprefix("Body_") + " (concept)"
        body.addProperty("App::PropertyString", "DesignStatus")
        body.DesignStatus = "concept"
        # Presentation spacing, not a kinematic or manufacturing dimension.
        body.Placement.Base = App.Vector(index * 60, 0, 0)

    adapter, flange, servo, angle, lever = bodies
    cylinder(adapter, "AdapterStock", "Params.spline_adapter_od_mm / 2", "Params.spline_hub_thickness_mm")
    cylinder(adapter, "PilotBore", "Params.spline_minor_d_mm / 2", "Params.spline_hub_thickness_mm", cut=True)

    cylinder(flange, "FlangeStock", "Params.flange_od_mm / 2", "Params.flange_thickness_mm")
    cylinder(flange, "FlangeBore", "Params.flange_id_mm / 2", "Params.flange_thickness_mm", cut=True)
    hole = cylinder(flange, "FlangeBolt", "Params.flange_hole_d_mm / 2", "Params.flange_thickness_mm",
                    cut=True, x="Params.flange_bcd_mm / 2")
    pattern = flange.newObject("PartDesign::PolarPattern", "FlangeBoltPattern")
    pattern.Originals = [hole]
    axis = next(o for o in flange.Origin.OriginFeatures if o.Name.startswith("Z_Axis"))
    pattern.Axis = (axis, [""])
    pattern.Angle = 360
    pattern.setExpression("Occurrences", "Params.flange_hole_count")
    flange.Tip = pattern
    doc.recompute()

    box(servo, "ServoPlate", "Params.servo_mount_width_mm", "Params.servo_mount_thickness_mm",
        "Params.servo_mount_height_mm", x="-Params.servo_mount_width_mm / 2", y="-Params.servo_mount_thickness_mm / 2")
    for side, x in [("Left", "-Params.servo_mount_width_mm / 2"),
                    ("Right", "Params.servo_mount_width_mm / 2 - Params.servo_mount_thickness_mm")]:
        box(servo, "ServoEar" + side, "Params.servo_mount_thickness_mm", "Params.servo_ear_depth_mm",
            "Params.servo_mount_height_mm * Params.servo_ear_height_ratio", x=x,
            y="-Params.servo_ear_depth_mm / 2", z="Params.servo_mount_height_mm * Params.servo_ear_base_ratio")
    for index, (sx, sz) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        feature(servo, "SubtractiveCylinder", f"ServoBolt{index}", {
            "Radius": "Params.servo_hole_d_mm / 2",
            # Drill the whole ear envelope, so no blind bores remain through the ears.
            "Height": "Params.servo_ear_depth_mm",
            "Placement.Base.x": f"{sx} * Params.servo_hole_pitch_x_mm / 2",
            "Placement.Base.y": "-Params.servo_ear_depth_mm / 2",
            "Placement.Base.z": f"Params.servo_mount_height_mm / 2 + {sz} * Params.servo_hole_pitch_y_mm / 2",
        }, App.Rotation(App.Vector(0, 0, 1), App.Vector(0, 1, 0)))

    box(angle, "BracketX", "Params.ra_leg_a_mm", "Params.ra_thickness_mm", "Params.ra_leg_b_mm")
    box(angle, "BracketY", "Params.ra_thickness_mm", "Params.ra_leg_a_mm", "Params.ra_leg_b_mm")
    box(angle, "BracketWeb", "Params.ra_leg_a_mm * Params.ra_gusset_ratio",
        "Params.ra_leg_a_mm * Params.ra_gusset_ratio", "Params.ra_gusset_thickness_mm",
        x="Params.ra_thickness_mm", y="Params.ra_thickness_mm", z="Params.ra_leg_b_mm * Params.ra_gusset_ratio")

    cylinder(lever, "LeverHub", "Params.lever_hub_d_mm / 2", "Params.lever_hub_thickness_mm")
    box(lever, "LeverArm", "Params.lever_length_mm", "Params.lever_width_mm", "Params.lever_thickness_mm",
        y="-Params.lever_width_mm / 2", z="(Params.lever_hub_thickness_mm - Params.lever_thickness_mm) / 2")
    cylinder(lever, "LeverTipBore", "Params.lever_tip_hole_d_mm / 2", "Params.lever_thickness_mm", cut=True,
             x="Params.lever_length_mm - Params.lever_tip_inset_mm", z="(Params.lever_hub_thickness_mm - Params.lever_thickness_mm) / 2")
    doc.recompute()
    for body in bodies:
        if body.Shape.isNull() or not body.Shape.isValid() or len(body.Shape.Solids) != 1:
            raise ValueError(f"Invalid fixture: {body.Name}")
        for obj in body.Group:
            if hasattr(obj, "Visibility"):
                obj.Visibility = obj == body.Tip
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, default=CAD / "weevil_leg_params.yaml")
    parser.add_argument("--output", type=Path, required=True, help="New output directory; existing paths are refused")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite {args.output}")
    doc = build_document(args.params)
    try:
        args.output.mkdir(parents=True)
        doc.saveAs(str((args.output / "Fixtures.FCStd").resolve()))
        manifest = {"design_status": "concept", "minimum_clearance_mm": 0.1,
                    "objects": [{"name": name} for name in BODY_NAMES]}
        (args.output / "selection.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Built five editable fixture concepts in {args.output}")
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    main()
