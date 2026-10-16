"""Controls for frozen experiments and fail-closed handling of physical records."""

import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "verification/cots"
sys.path.insert(0, str(SCRIPTS))


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def bench():
    return module("check_bench_evidence")


@pytest.fixture
def valid_record(tmp_path, bench):
    manifest = json.loads(bench.TEMPLATE.read_text())
    manifest.update(
        dataset_origin="synthetic_control",
        csv_file="synthetic.csv",
        acquisition_utc="2026-10-16T00:00:00Z",
        operator="SYNTHETIC CONTROL",
        fixture_id="synthetic",
        actuator_serial="synthetic",
        driver_revision="synthetic",
        firmware_revision="synthetic",
        calibration_record="synthetic",
        temperature_limits_c={"motor_case_temp_c": 70.0, "driver_temp_c": 70.0},
        temperature_limit_sources={
            "motor_case_temp_c": "SYNTHETIC LIMIT, NOT A SUPPLIER SPEC",
            "driver_temp_c": "SYNTHETIC LIMIT, NOT A SUPPLIER SPEC",
        },
    )
    rows = [dict(zip(bench.FIELDS, (t, 42.0, 40.0, 41.0, 22.0, 36.0, 4.0, 60.0, 1, 1, 0))) for t in range(3601)]
    path = tmp_path / "manifest.json"
    return path, manifest, rows


def write_record(bench, record):
    path, manifest, rows = record
    raw = path.parent / manifest["csv_file"]
    with raw.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=bench.FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest["csv_sha256"] = hashlib.sha256(raw.read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest))
    return path


def test_no_measurements_never_pass(bench, tmp_path):
    for path in (bench.TEMPLATE, tmp_path / "missing.json"):
        r = bench.evaluate_record(path)
        assert r["status"] == "SOURCE-GATED"
        assert r["gates_closed"] == [] and not r["hardware_validated"]


def test_valid_synthetic_record_remains_non_evidence(bench, valid_record):
    r = bench.evaluate_record(write_record(bench, valid_record))
    assert r["status"] == "SYNTHETIC_CONTROL_ONLY"
    assert all(r["checks"].values())
    assert r["metrics"]["duration_s"] == 3600
    assert r["gates_closed"] == [] and not r["hardware_validated"]


def test_measured_declaration_still_requires_physical_review(bench, valid_record):
    valid_record[1]["dataset_origin"] = "measured"  # Test the classification only; data remain synthetic.
    r = bench.evaluate_record(write_record(bench, valid_record))
    assert r["status"] == "NUMERICAL_CHECKS_PASS_REVIEW_REQUIRED"
    assert not r["hardware_validated"] and not r["gates_closed"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("measured_torque_nm", 0),
        ("measured_torque_nm", -42),
        ("measured_torque_nm", 43.3),
        ("torque_sensor_ok", 0),
        ("motor_feedback_ok", 0),
        ("driver_fault_code", 1),
        ("bus_voltage_v", 53),
        ("bus_voltage_v", 33),
        ("bus_current_a", 17),
        ("aux_output_power_w", 101),
        ("motor_case_temp_c", 71),
        ("driver_temp_c", 71),
        ("time_s", 0),
        ("measured_torque_nm", float("nan")),
        ("motor_feedback_ok", 2),
        ("ambient_temp_c", ""),
        ("driver_fault_code", 0.5),
    ],
)
def test_single_bad_sample_cannot_be_averaged_away(bench, valid_record, field, value):
    valid_record[2][1800][field] = value
    r = bench.evaluate_record(write_record(bench, valid_record))
    assert r["status"] == "REJECTED"
    assert not r["hardware_validated"]


def test_short_gapped_or_heating_record_fails(bench, valid_record):
    for kind in ("short", "gap", "heating"):
        path, m, rows = copy.deepcopy(valid_record)
        if kind == "short":
            rows = rows[:-1]
        if kind == "gap":
            del rows[1500:1503]
        if kind == "heating":
            for row in rows:
                row["motor_case_temp_c"] += row["time_s"] * 0.003
        r = bench.evaluate_record(write_record(bench, (path, m, rows)))
        assert r["status"] == "REJECTED", kind
        if kind == "heating":
            assert "motor_case_temp_c_tail_rise" in r["reasons"]
            assert r["checks"]["motor_case_temp_c_limit"]


def test_missing_supplier_limit_and_tampering_are_not_evidence(bench, valid_record):
    valid_record[1]["temperature_limit_sources"] = {}
    r = bench.evaluate_record(write_record(bench, valid_record))
    assert r["status"] == "SOURCE-GATED"
    path, m, _ = valid_record
    raw = path.parent / m["csv_file"]
    raw.write_text(raw.read_text() + "\n")
    assert bench.evaluate_record(path)["status"] == "REJECTED"


def test_unknown_protocol_and_malformed_manifest_rejected(bench, valid_record):
    valid_record[1]["protocol_id"] = "unreviewed"
    path = write_record(bench, valid_record)
    assert bench.evaluate_record(path)["status"] == "REJECTED"
    for malformed in ([], None, {"dataset_origin": "measured", "csv_file": 12}):
        path.write_text(json.dumps(malformed))
        assert bench.evaluate_record(path)["status"] == "REJECTED"


def test_frozen_baseline_and_experiment_controls(tmp_path):
    runner = module("run_tranche_02")
    spec = runner.frozen_spec()
    assert all(runner.controls(runner.load_config()).values())
    spec["frozen_inputs_sha256"]["models/cots_rover.py"] = "0" * 64
    p = tmp_path / "changed.json"
    p.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="Frozen input changed"):
        runner.frozen_spec(p)


def test_report_keeps_rejections_visible_and_baseline_hashes():
    runner = module("run_tranche_02")
    report = json.loads((SCRIPTS / "tranche_02/robustness.json").read_text())
    geometry = json.loads((SCRIPTS / "tranche_02/geometry.json").read_text())
    assert report["spec_sha256"] == geometry["spec_sha256"] == runner.sha256(runner.SPEC)
    assert report["dense_interpolation"]["cases"] == 1728
    assert sum(p["cases"] for p in report["profiles"].values()) == 10800
    loss = report["support_loss"]
    assert loss["cases"] == 5400 and loss["rejection_count"] > 0
    assert loss["verdict"] == "CLOSED_UNDER_TESTED_SPECIFICATION"
    assert not report["hardware_validated"] and not geometry["fabrication_released"]
    assert geometry["unique_overlapping_pairs"] > 0 and not geometry["all_modeled_solids_clear"]
