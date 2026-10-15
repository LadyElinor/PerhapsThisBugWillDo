#!/usr/bin/env python3
"""Headless, explicit-selection CAD audit. Run in a disposable FreeCAD Python process.

Shapes are in mm. Density is kg/m^3. Inertia is about each solid's COM in
world-oriented axes; it is NOT already a URDF link-frame inertia.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import tempfile

import FreeCAD as App
import Part
import Import


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def step_schema(path):
    header = Path(path).read_text(errors="replace").split("ENDSEC;", 1)[0]
    match = re.search(r"FILE_SCHEMA\s*\(\((.*?)\)\)\s*;", header, re.S)
    if not match:
        raise ValueError("STEP FILE_SCHEMA missing")
    return " ".join(match.group(1).split())


def world_shape(obj):
    if obj.TypeId in ("App::Part", "App::Link", "App::LinkElement"):
        raise ValueError(f"{obj.Name}: select a physical feature/body, not a group/link")
    if not hasattr(obj, "Shape") or obj.Shape.isNull():
        raise ValueError(f"{obj.Name}: missing or null shape")
    for dependency in [obj, *obj.OutListRecursive]:
        if any(x in str(dependency.State) for x in ("Error", "Invalid", "Touched")):
            raise ValueError(f"{obj.Name}: unresolved dependency {dependency.Name}: {dependency.State}")
    shape = obj.Shape.copy()
    # Native PartDesign bodies can wrap their single solid in a Compound.
    # Unwrap only one-child compounds; never discard extra faces/edges/solids.
    while shape.ShapeType == "Compound" and len(shape.childShapes()) == 1:
        shape = shape.childShapes()[0]
    if shape.ShapeType != "Solid" or len(shape.Solids) != 1:
        raise ValueError(f"{obj.Name}: expected exactly one solid, got {shape.ShapeType}")
    # Shape already contains the object's placement. Apply only ancestor placement.
    parent = obj.getGlobalPlacement().multiply(obj.Placement.inverse())
    shape.Placement = parent.multiply(shape.Placement)
    if not shape.isValid() or not shape.isClosed():
        raise ValueError(f"{obj.Name}: invalid or open solid")
    if not math.isfinite(shape.Volume) or shape.Volume <= 0:
        raise ValueError(f"{obj.Name}: non-positive/non-finite volume")
    return shape


def metrics(name, shape, density=None):
    box = shape.BoundBox
    row = dict(name=name, volume_mm3=shape.Volume,
               center_of_mass_m=[v * 1e-3 for v in shape.CenterOfMass],
               bounds_mm=[box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax],
               density_kg_m3=density, mass_kg=None, inertia_com_world_kg_m2=None)
    if density is not None:
        density = float(density)
        if not math.isfinite(density) or density <= 0:
            raise ValueError(f"{name}: density must be finite and positive")
        row["mass_kg"] = shape.Volume * density * 1e-9
        matrix = shape.MatrixOfInertia
        row["inertia_com_world_kg_m2"] = [
            [matrix.A[i * 4 + j] * density * 1e-15 for j in range(3)] for i in range(3)
        ]
    return row


def pair_check(a, sa, b, sb, clearance_mm, volume_tolerance_mm3):
    common = sa.common(sb)
    if not common.isNull() and not common.isValid():
        raise ValueError(f"Boolean intersection failed for {a}/{b}")
    overlap = 0.0 if common.isNull() else max(0.0, common.Volume)
    distance = float(sa.distToShape(sb)[0])
    duplicate = (abs(sa.Volume - sb.Volume) <= volume_tolerance_mm3
                 and abs(overlap - sa.Volume) <= volume_tolerance_mm3)
    status = ("duplicate" if duplicate else "overlap" if overlap > volume_tolerance_mm3
              else "below_clearance" if distance < clearance_mm else "clear")
    return dict(objects=[a, b], minimum_distance_mm=distance,
                overlap_volume_mm3=overlap, status=status)


def audit_document(doc, manifest):
    specs = manifest["objects"]
    names = [o["name"] for o in specs]
    if not names or len(names) != len(set(names)):
        raise ValueError("An explicit, nonempty list of unique internal object names is required")
    doc.recompute()
    clearance = float(manifest.get("minimum_clearance_mm", 0.0))
    volume_tol = float(manifest.get("volume_tolerance_mm3", 1e-6))
    if not math.isfinite(clearance) or clearance < 0 or not math.isfinite(volume_tol) or volume_tol <= 0:
        raise ValueError("Clearance must be nonnegative; volume tolerance must be positive")
    allowed_touch = {frozenset(pair) for pair in manifest.get("allow_touching_pairs", [])}
    for pair in allowed_touch:
        if len(pair) != 2 or not pair.issubset(names):
            raise ValueError("allow_touching_pairs must name two selected objects")
    shapes = {}
    report = dict(freecad=App.Version(), occt=Part.OCC_VERSION, errors=[], parts=[], pairs=[],
                  units=dict(length="mm", mass="kg", inertia="kg m^2"),
                  inertia_frame="solid COM; axes parallel to document world axes",
                  assessment="geometry screening only; no strength, motion, or lunar qualification")
    report["design_status"] = manifest.get("design_status", "unspecified")
    notes = doc.getObject("DesignNotes")
    report["design_limitations"] = list(getattr(notes, "Limitations", []))
    for spec in specs:
        name = spec["name"]
        obj = doc.getObject(name)
        try:
            if obj is None:
                raise ValueError(f"{name}: object not found (use internal Name, not Label)")
            shape = world_shape(obj)
            row = metrics(name, shape, spec.get("density_kg_m3"))
            row["label"] = obj.Label
            row["design_status"] = getattr(obj, "DesignStatus", "unspecified")
            shapes[name] = shape
            report["parts"].append(row)
        except (ValueError, RuntimeError) as exc:
            report["errors"].append(str(exc))
    for (a, sa), (b, sb) in itertools.combinations(shapes.items(), 2):
        try:
            pair = pair_check(a, sa, b, sb, clearance, volume_tol)
            if pair["status"] == "below_clearance" and frozenset((a, b)) in allowed_touch:
                pair["status"] = "permitted_contact_clearance"
            report["pairs"].append(pair)
            if pair["status"] in ("duplicate", "overlap", "below_clearance"):
                report["errors"].append(f"{a}/{b}: {pair['status']}")
        except (ValueError, RuntimeError) as exc:
            report["errors"].append(str(exc))
    report["passed"] = not report["errors"]
    return report, shapes


def export_verified(shapes, destination):
    """Export one instance of each selected shape; publish only after round-trip checks.

    Uses AP242DIS supplied by this FreeCAD/OCCT build. This does not certify Ed2,
    semantic PMI, full assembly constraints, materials, or a manufacturing package.
    """
    target = Path(destination).resolve()
    if target.exists():
        raise ValueError(f"Refusing to overwrite {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    tempdoc = App.newDocument("WeevilAuditExport")
    try:
        objects = []
        for name, shape in shapes.items():
            obj = tempdoc.addObject("Part::Feature", name)
            obj.Shape = shape.copy()
            objects.append(obj)
        tempdoc.recompute()
        # Preferences alone did not update the initialized OCCT writer in our probe.
        Part.setStaticValue("write.step.schema", "AP242DIS")
        Part.setStaticValue("write.step.unit", "MM")
        with tempfile.TemporaryDirectory(dir=target.parent) as scratch:
            candidate = Path(scratch)/"candidate.step"
            Import.export(objects, str(candidate), exportHidden=True, legacy=False, keepPlacement=True)
            schema = step_schema(candidate)
            if "AP242_MANAGED_MODEL_BASED_3D_ENGINEERING" not in schema.upper():
                raise ValueError(f"Wrong STEP schema: {schema}")
            restored = Part.read(str(candidate))
            expected = sum(s.Volume for s in shapes.values())
            if (not restored.isValid() or len(restored.Solids) != len(shapes)
                    or not math.isclose(restored.Volume, expected, rel_tol=1e-8, abs_tol=1e-5)):
                raise ValueError("STEP round-trip failed validity, solid-count or volume check")
            # Also match each solid spatially: counts/volumes alone miss moved parts.
            unmatched = list(restored.Solids)
            for name, shape in shapes.items():
                for index, other in enumerate(unmatched):
                    tolerance = max(1e-5, shape.Volume * 1e-8)
                    if (abs(shape.Volume-other.Volume) <= tolerance
                            and abs(shape.common(other).Volume-shape.Volume) <= tolerance):
                        unmatched.pop(index)
                        break
                else:
                    raise ValueError(f"STEP round-trip spatial match failed for {name}")
            with target.open("xb") as handle:
                handle.write(candidate.read_bytes())
        return dict(path=str(target), sha256=digest(target), file_schema=schema,
                    solids=len(restored.Solids), volume_mm3=restored.Volume,
                    spatial_roundtrip=True, pmi_verified=False)
    finally:
        App.closeDocument(tempdoc.Name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--step", type=Path)
    args = parser.parse_args()
    doc = App.openDocument(str(args.document.resolve()))
    try:
        manifest = json.loads(args.manifest.read_text())
        report, shapes = audit_document(doc, manifest)
        report["inputs"] = {str(p): digest(p) for p in (args.document, args.manifest)}
        if args.step and report["passed"]:
            try:
                report["export"] = export_verified(shapes, args.step)
            except Exception as exc:
                report["errors"].append(f"Export failed: {exc}")
                report["passed"] = False
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
        print(json.dumps(dict(passed=report["passed"], report=str(args.report), errors=report["errors"])))
        return 0 if report["passed"] else 2
    finally:
        App.closeDocument(doc.Name)


if __name__ == "__main__":
    raise SystemExit(main())
