"""Unit tests for the verification receipts spine.

These pin the contracts that closed the original integrity gaps:
  * every harness script is registered in the manifest (no silent additions),
  * schema mismatch is `error`, never a silent `fail` (the old aggregator bug),
  * multi-column pass contracts evaluate correctly (offplane_impulse_recovery),
  * threshold sweeps gate on their declared envelope (axis orthogonality),
  * gate tables enforce expectations both ways: an expected-fail that passes
    is `drift`, and so is an expected-pass that fails,
  * status combination severity ordering is stable.
"""

from __future__ import annotations

import sys
from pathlib import Path

VERIFICATION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERIFICATION_DIR))

import receipts  # noqa: E402
from receipts import combine, evaluate_report, load_manifest  # noqa: E402


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "report.csv"
    p.write_text(text, encoding="utf-8")
    return p


# --- manifest coverage -----------------------------------------------------

def test_manifest_loads_with_schema_version_1():
    manifest = load_manifest()
    assert manifest["schema_version"] == 1
    assert manifest["harnesses"]


def test_every_toplevel_harness_script_is_registered():
    manifest = load_manifest()
    registered = {
        Path(spec["script"]).name
        for spec in manifest["harnesses"].values()
        if Path(spec["script"]).parts[0] == "verification"
    }
    on_disk = {p.name for p in VERIFICATION_DIR.glob("test_*.py")}
    unregistered = on_disk - registered
    assert not unregistered, (
        f"harness scripts not registered in harness_manifest.yaml: {sorted(unregistered)}; "
        "register them (with a report contract) or move real pytest tests into verification/tests/"
    )


def test_traceability_map_targets_exist():
    manifest = load_manifest()
    harnesses = set(manifest["harnesses"])
    for test_name, entry in manifest["traceability"]["test_map"].items():
        assert entry["harness"] in harnesses, f"{test_name} maps to unknown harness {entry['harness']}"
    for name in manifest["traceability"]["pending_linkage"]:
        assert name in harnesses, f"pending_linkage references unknown harness {name}"


def test_conftest_ignore_list_matches_manifest():
    import importlib.util

    guard_path = VERIFICATION_DIR / "conftest.py"
    spec = importlib.util.spec_from_file_location("verification_conftest_guard", guard_path)
    assert spec is not None and spec.loader is not None
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)

    manifest = load_manifest()
    expected = {
        Path(spec_["script"]).name
        for spec_ in manifest["harnesses"].values()
        if Path(spec_["script"]).parts[0] == "verification"
    }
    assert set(guard.collect_ignore) == expected


# --- pass_column contracts ---------------------------------------------------

def test_pass_column_all_rows_pass(tmp_path):
    p = _write(tmp_path, "test_id,pass\nA,True\nB,true\nC,1\n")
    status, _ = evaluate_report({"kind": "pass_column", "pass_columns": ["pass"]}, p)
    assert status == "pass"


def test_pass_column_partial_and_fail(tmp_path):
    p = _write(tmp_path, "test_id,pass\nA,True\nB,False\n")
    status, _ = evaluate_report({"kind": "pass_column", "pass_columns": ["pass"]}, p)
    assert status == "partial"
    p.write_text("test_id,pass\nA,False\n", encoding="utf-8")
    status2, _ = evaluate_report({"kind": "pass_column", "pass_columns": ["pass"]}, p)
    assert status2 == "fail"


def test_multi_pass_columns_require_all(tmp_path):
    """Regression: offplane_impulse_recovery gates on pass_time AND pass_slip."""
    p = _write(tmp_path, "test_id,pass_time,pass_slip\nX,True,True\n")
    spec = {"kind": "pass_column", "pass_columns": ["pass_time", "pass_slip"]}
    assert evaluate_report(spec, p)[0] == "pass"
    p.write_text("test_id,pass_time,pass_slip\nX,True,False\n", encoding="utf-8")
    assert evaluate_report(spec, p)[0] == "fail"


def test_schema_mismatch_is_error_not_fail(tmp_path):
    """Regression: the old aggregator reported schema-divergent reports as
    silent failures. A missing declared column is broken instrumentation."""
    p = _write(tmp_path, "test_id,pass_time,pass_slip\nX,True,True\n")
    status, detail = evaluate_report({"kind": "pass_column", "pass_columns": ["pass"]}, p)
    assert status == "error"
    assert "schema mismatch" in detail


def test_missing_and_empty_reports(tmp_path):
    status, _ = evaluate_report({"kind": "pass_column"}, tmp_path / "nope.csv")
    assert status == "missing"
    p = _write(tmp_path, "test_id,pass\n")
    assert evaluate_report({"kind": "pass_column"}, p)[0] == "missing"


# --- threshold contracts -----------------------------------------------------

def test_threshold_pass_and_fail(tmp_path):
    spec = {
        "kind": "threshold",
        "where": {"column": "axis_error_deg", "equals": 15.0},
        "metric": "rate",
        "min": 0.80,
    }
    p = _write(tmp_path, "axis_error_deg,rate\n0.0,0.92\n15.0,0.84\n")
    assert evaluate_report(spec, p)[0] == "pass"
    p.write_text("axis_error_deg,rate\n0.0,0.92\n15.0,0.71\n", encoding="utf-8")
    assert evaluate_report(spec, p)[0] == "fail"


def test_threshold_missing_where_row_is_error(tmp_path):
    spec = {
        "kind": "threshold",
        "where": {"column": "axis_error_deg", "equals": 15.0},
        "metric": "rate",
        "min": 0.80,
    }
    p = _write(tmp_path, "axis_error_deg,rate\n0.0,0.92\n")
    status, _ = evaluate_report(spec, p)
    assert status == "error"


# --- gate_table contracts ----------------------------------------------------

GATE_SPEC = {
    "kind": "gate_table",
    "name_column": "gate_id",
    "pass_column": "passed",
    "expected_fail": ["mare/baseline_45deg"],
}


def test_gate_table_expected_fail_is_pass_overall(tmp_path):
    p = _write(tmp_path, "gate_id,passed\nmare/baseline_45deg,False\nrescue/mare,True\n")
    status, detail = evaluate_report(GATE_SPEC, p)
    assert status == "pass"
    assert "expected-fail" in detail


def test_gate_table_drift_when_expected_fail_passes(tmp_path):
    """An expected baseline failure that starts passing is a model change
    that must be reviewed, not silently absorbed."""
    p = _write(tmp_path, "gate_id,passed\nmare/baseline_45deg,True\nrescue/mare,True\n")
    assert evaluate_report(GATE_SPEC, p)[0] == "drift"


def test_gate_table_drift_when_expected_pass_fails(tmp_path):
    p = _write(tmp_path, "gate_id,passed\nmare/baseline_45deg,False\nrescue/mare,False\n")
    assert evaluate_report(GATE_SPEC, p)[0] == "drift"


def test_gate_table_drift_when_declared_gate_absent(tmp_path):
    p = _write(tmp_path, "gate_id,passed\nrescue/mare,True\n")
    status, detail = evaluate_report(GATE_SPEC, p)
    assert status == "drift"
    assert "absent" in detail


# --- combination semantics ---------------------------------------------------

def test_combine_severity_order():
    assert combine(["pass", "pass"]) == "pass"
    assert combine(["pass", "partial"]) == "partial"
    assert combine(["partial", "fail"]) == "fail"
    assert combine(["fail", "drift"]) == "drift"
    assert combine(["drift", "missing"]) == "missing"
    assert combine(["missing", "error"]) == "error"
    assert combine([]) == "missing"


def test_truthy_vocabulary():
    assert receipts.truthy("True") and receipts.truthy("1") and receipts.truthy("pass")
    assert not receipts.truthy("False") and not receipts.truthy("0") and not receipts.truthy("")
