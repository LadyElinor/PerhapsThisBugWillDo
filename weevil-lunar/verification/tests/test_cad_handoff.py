"""Behavioral regressions for travel limits and historical artifact screening."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cad" / "scripts"))
from bundle_inspection import inspect_bundle
from models.lunar_integrated_weevil_leg import ContactModel, LegState, evaluate_leg_state, load_params, sample_states, screw_travel


def test_configured_travel_is_rotation_limited():
    report = screw_travel(load_params())
    assert report.available_travel_mm == pytest.approx(4.5)
    assert report.stroke_utilization == pytest.approx(4.5 / 35)
    assert report.rotation_for_full_stroke_deg == pytest.approx(933.3333333333)
    assert report.limiting_constraint == "rotation"


def test_mechanical_stop_cannot_be_reported_as_reachable():
    params = replace(load_params(), tibia_stroke_mm=1)
    report = screw_travel(params)
    assert report.limiting_constraint == "stroke"
    assert report.available_travel_mm == pytest.approx(1)
    result = evaluate_leg_state(LegState(0, 0, 60), params, ContactModel())
    assert not result.reachable  # Previously silently clipped and reported reachable.
    assert all(evaluate_leg_state(s, params, ContactModel()).reachable for s in sample_states(params))
    endpoints = [evaluate_leg_state(LegState(0, 0, sign * report.effective_rotation_range_deg / 2), params, ContactModel()).tip_x_mm for sign in (-1, 1)]
    assert endpoints == pytest.approx([params.femur_link_mm, params.femur_link_mm + 1])


@pytest.mark.parametrize("field", ["tibia_stroke_mm", "tibia_range_total_deg", "tibia_pitch_mm_per_rev"])
@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_screw_parameters_rejected(field, value):
    with pytest.raises(ValueError, match="finite and positive"):
        screw_travel(replace(load_params(), **{field: value}))


def test_nonfinite_joint_state_rejected():
    with pytest.raises(ValueError, match="finite angles"):
        evaluate_leg_state(LegState(float("nan"), 0, 0), load_params(), ContactModel())


def test_historical_bundle_exposes_known_failures():
    rows = {row["gate_id"]: row for row in inspect_bundle(ROOT / "cad" / "export")}
    assert all(rows[name]["passed"] for name in ("present/step", "present/fcstd", "present/urdf"))
    for name in ("step_schema_ap242", "parametric_document", "urdf_complete"):
        assert not rows[name]["passed"]
    assert "AUTOMOTIVE_DESIGN" in rows["step_schema_ap242"]["detail"]


def test_missing_and_corrupt_files_fail_without_false_green(tmp_path):
    assert not any(row["passed"] for row in inspect_bundle(tmp_path))
    (tmp_path / "Phase2_Templates.FCStd").write_bytes(b"not a zip")
    (tmp_path / "weevil_leg_module.urdf").write_text("<broken")
    (tmp_path / "weevil_leg_module_ap242.step").write_text("AP242 in filename is not a schema")
    rows = {row["gate_id"]: row for row in inspect_bundle(tmp_path)}
    for name in ("step_schema_ap242", "parametric_document", "urdf_complete"):
        assert not rows[name]["passed"]


def test_multiline_schema_and_native_expression_structure(tmp_path):
    (tmp_path / "weevil_leg_module_ap242.step").write_text("HEADER;\nFILE_SCHEMA((\n'AP242_MANAGED_MODEL_BASED_3D_ENGINEERING_MIM_LF'\n));\nENDSEC;")
    with zipfile.ZipFile(tmp_path / "Phase2_Templates.FCStd", "w") as archive:
        archive.writestr("Document.xml", '<Document><Objects><Object type="Spreadsheet::Sheet"/><Object type="PartDesign::Body"/></Objects><ObjectData><ExpressionEngine><Expression path="Height" expression="Params.height"/></ExpressionEngine></ObjectData></Document>')
    rows = {row["gate_id"]: row for row in inspect_bundle(tmp_path)}
    assert rows["step_schema_ap242"]["passed"]
    assert rows["parametric_document"]["passed"]
    assert not rows["urdf_complete"]["passed"]
