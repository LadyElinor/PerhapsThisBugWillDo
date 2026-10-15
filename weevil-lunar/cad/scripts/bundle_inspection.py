"""Inspect handoff structure without FreeCAD; native geometry needs freecad_audit.py."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


def inspect_bundle(directory: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(gate, passed, detail):
        rows.append({"gate_id": gate, "passed": bool(passed), "detail": detail})

    step = directory / "weevil_leg_module_ap242.step"
    fcstd = directory / "Phase2_Templates.FCStd"
    urdf = directory / "weevil_leg_module.urdf"
    for path in (step, fcstd, urdf):
        add("present/" + path.suffix.lstrip(".").lower(), path.is_file() and path.stat().st_size > 0, path.name)
    schema = "missing/unreadable"
    try:
        text = step.read_text(encoding="utf-8", errors="replace").split("ENDSEC;", 1)[0]
        match = re.search(r"FILE_SCHEMA\s*\(\((.*?)\)\)\s*;", text, re.S)
        schema = " ".join(match.group(1).split()) if match else "missing FILE_SCHEMA"
    except OSError:
        pass
    add("step_schema_ap242", "AP242_MANAGED_MODEL_BASED_3D_ENGINEERING" in schema.upper(), schema)
    try:
        with zipfile.ZipFile(fcstd) as archive:
            doc = ET.fromstring(archive.read("Document.xml"))
        types = [node.get("type") for node in doc.findall("./Objects/Object")]
        expressions = doc.findall(".//ExpressionEngine/Expression")
        parametric = "Spreadsheet::Sheet" in types and "PartDesign::Body" in types and bool(expressions)
        detail = f"bodies={types.count('PartDesign::Body')}, sheets={types.count('Spreadsheet::Sheet')}, expressions={len(expressions)}"
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        parametric, detail = False, str(exc)
    add("parametric_document", parametric, detail)
    issues = []
    try:
        robot = ET.parse(urdf).getroot()
        links = robot.findall("link")
        joints = robot.findall("joint")
        if robot.tag != "robot" or not links or not joints:
            issues.append("missing robot/links/joints")
        for link in links:
            for tag in ("inertial", "collision", "visual"):
                if link.find(tag) is None:
                    issues.append(f"{link.get('name')}: missing {tag}")
        for joint in joints:
            if joint.get("type") in ("revolute", "prismatic"):
                limit = joint.find("limit")
                if limit is None or not all(k in limit.attrib for k in ("lower", "upper", "effort", "velocity")):
                    issues.append(f"{joint.get('name')}: missing complete limit")
            if joint.find("origin") is None:
                issues.append(f"{joint.get('name')}: origin unspecified")
    except (OSError, ET.ParseError) as exc:
        issues.append(str(exc))
    add("urdf_complete", not issues, "; ".join(issues) or "required elements present; dynamics not validated")
    return rows
