"""Failure injection for offline support gates and regression checks for COTS-1.1."""

from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from models.cots_rover import allocate, load_config, nominal_feet
from models.cots_support_guard import Snapshot, SupportMonitor, allocation_reasons, phase_preflight

ROOT = Path(__file__).resolve().parents[2]


def snap(t=0.0, contacts=(True,) * 6, **kwargs):
    return Snapshot(t, contacts, (0.0,) * 18, (0.0,) * 6, 0.0, True, **kwargs)


def test_monitor_complete_synthetic_wave_and_hardware_never_released():
    monitor = SupportMonitor()
    assert monitor.output()["advance_inhibited"]
    assert monitor.arm(snap(), restraint_confirmed=True)["state"] == "READY"
    t = 0.0
    for leg in (0, 3, 1, 4, 2, 5):
        t += 0.004
        assert monitor.observe(snap(t), swing_leg=leg)["state"] == "SWING"
        t += 0.004
        contacts = tuple(i != leg for i in range(6))
        out = monitor.observe(snap(t, contacts), swing_leg=leg)
        assert out["offline_sequence_permitted"]
        assert not out["hardware_motion_allowed"] and not out["automatic_recovery_allowed"]
        t += 0.004
        assert monitor.observe(snap(t))["state"] == "READY"


def test_loss_latches_until_explicit_six_contact_rearm():
    monitor = SupportMonitor()
    monitor.arm(snap(), restraint_confirmed=True)
    monitor.observe(snap(0.004), swing_leg=0)
    out = monitor.observe(snap(0.008, (False, False, True, True, True, True)), swing_leg=0)
    assert out["state"] == "FAULT_LATCHED"
    assert out["reason"] == "support_contact_lost" and out["advance_inhibited"]
    assert out["response"] == "EXTERNAL_RESTRAINT_REQUIRED"
    assert not out["automatic_recovery_allowed"]
    assert monitor.observe(snap(0.012))["state"] == "FAULT_LATCHED"
    assert monitor.arm(snap(0.016))["state"] == "FAULT_LATCHED"
    assert monitor.arm(snap(0.020, (False,) + (True,) * 5), restraint_confirmed=True)["state"] == "FAULT_LATCHED"
    assert monitor.arm(snap(0.024), restraint_confirmed=True)["state"] == "READY"


@pytest.mark.parametrize("field,value,reason", [
    ("motor_age_ms", (40.0,) + (0.0,) * 17, "stale_feedback"),
    ("contact_age_ms", (40.0,) + (0.0,) * 5, "stale_feedback"),
    ("heartbeat_age_ms", 100.0, "heartbeat_timeout"),
    ("heartbeat_age_ms", -1.0, "invalid_timing"),
    ("now_s", float("nan"), "invalid_timing"),
    ("now_s", 0.0, "clock_not_increasing"),
    ("now_s", -0.1, "invalid_timing"),
    ("contacts", (1,) * 6, "invalid_contact_states"),
    ("contacts", None, "invalid_contact_states"),
    ("motor_age_ms", None, "invalid_feedback_channels"),
    ("motor_age_ms", (0.0,) * 17, "missing_feedback_channels"),
    ("contact_age_ms", (float("inf"),) * 6, "invalid_timing"),
    ("feedback_valid", False, "invalid_feedback"),
    ("feedback_valid", 1, "invalid_feedback"),
])
def test_stale_malformed_or_out_of_order_feedback_fails_closed(field, value, reason):
    monitor = SupportMonitor()
    monitor.arm(snap(), restraint_confirmed=True)
    out = monitor.observe(replace(snap(0.004), **{field: value}))
    assert out["state"] == "FAULT_LATCHED" and out["reason"] == reason
    assert not out["hardware_motion_allowed"] and out["advance_inhibited"]


def test_plan_changes_cannot_relabel_a_lost_foot_as_swing():
    monitor = SupportMonitor()
    monitor.arm(snap(), restraint_confirmed=True)
    assert monitor.observe(snap(0.004, (False,) + (True,) * 5), swing_leg=0)["state"] == "FAULT_LATCHED"
    monitor.arm(snap(0.008), restraint_confirmed=True)
    monitor.observe(snap(0.012), swing_leg=0)
    assert monitor.observe(snap(0.016), swing_leg=1)["reason"] == "swing_switch_without_six_contact_transfer"


def test_cannot_end_swing_before_touchdown_or_rearm_an_active_sequence():
    monitor = SupportMonitor()
    monitor.arm(snap(), restraint_confirmed=True)
    assert monitor.arm(snap(0.004), restraint_confirmed=True)["reason"] == "cannot_rearm_active_sequence"
    monitor.arm(snap(0.008), restraint_confirmed=True)
    monitor.observe(snap(0.012), swing_leg=0)
    out = monitor.observe(snap(0.016, (False,) + (True,) * 5))
    assert out["reason"] == "transfer_requires_six_contacts"


@pytest.mark.parametrize("kwargs", [
    {"phase": -1}, {"phase": 6}, {"phase": True},
    {"phase": 0, "subdivisions": 0}, {"phase": 0, "subdivisions": 3},
    {"phase": 0, "slope_deg": 6}, {"phase": 0, "slope_deg": float("nan")},
])
def test_preflight_rejects_invalid_or_undersampled_plans(kwargs):
    with pytest.raises(ValueError):
        phase_preflight(load_config(), **kwargs)


def test_preflight_cannot_pass_vacuously(monkeypatch):
    monkeypatch.setattr("models.cots_support_guard.gait_samples", lambda *args: iter(()))
    with pytest.raises(ValueError, match="Incomplete preflight"):
        phase_preflight(load_config(), 0)


@pytest.mark.parametrize("field,value", [
    ("max_cop_offset_m", 0.071), ("support_margin_m", 0.039),
    ("force_residual_n", 0.001), ("moment_residual_nm", 0.001),
    ("max_torque_nm", 43.3), ("max_normal_n", 300.1),
    ("max_normal_n", float("nan")), ("max_torque_nm", True),
])
def test_solver_success_does_not_bypass_secondary_constraints(field, value):
    c = load_config()
    result = allocate(c, nominal_feet(c), tuple(range(6)), np.array(c["com_m"]), np.array([0, 0, -9.80665]), 1.3)
    assert not allocation_reasons(c, result)
    result[field] = value
    assert allocation_reasons(c, result)


def test_correction_report_preserves_failed_baseline_and_release_blockers():
    path = ROOT / "verification/cots/tranche_03"
    spec = json.loads((path / "spec.json").read_text())
    for name, expected in spec["frozen_inputs_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    report = json.loads((path / "results.json").read_text())
    assert report["spec_sha256"] == hashlib.sha256((path / "spec.json").read_bytes()).hexdigest()
    for name, expected in report["input_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    assert all(report["correction_checks"].values())
    geo = report["geometry"]
    assert geo["solid_count"] == 86 and geo["pair_checks"] == 113305
    assert geo["resolved_modeled_pairs"] == 10 and geo["remaining_overlapping_pairs"] == 60
    assert len(geo["baseline_issue_ledger"]) == 70
    assert not geo["all_modeled_solids_clear"] and not geo["fabrication_released"]
    assert report["counts"]["nominal_cases"] == 1080 and report["counts"]["nominal_rejected"] == 0
    assert report["counts"]["loss_cases"] == 5400 and report["counts"]["loss_rejected"] > 0
    assert all(not p["single_loss_static_contingency_pass"] for p in report["phases"])
    assert not report["hardware_motion_allowed"] and not report["dynamic_recovery_proven"]
