from __future__ import annotations

import json
from pathlib import Path

from receipts import load_manifest
from simulators.common.comparative_report import _build_summary


def test_manifest_requires_data_source_for_all_harnesses():
    manifest = load_manifest()
    harnesses = manifest["harnesses"]
    assert harnesses
    for spec in harnesses.values():
        assert spec["data_source"] in {"placeholder", "model_coupled", "backend", "hardware"}


def test_comparative_summary_stays_non_evidence_when_placeholder_backend_present():
    mj_metrics = {
        "completed": {"available": True, "value": True},
        "normal_reaction_n": {"available": True, "value": 1.0},
        "tangential_reaction_n": {"available": True, "value": 1.0},
        "slip_distance_m": {"available": True, "value": 0.1},
        "slip_velocity_m_s": {"available": True, "value": 0.1},
        "stance_stable_duration_s": {"available": True, "value": 1.0},
    }
    od_metrics = {
        "completed": {"available": True, "value": True},
        "normal_reaction_n": {"available": True, "value": 1.0},
        "tangential_reaction_n": {"available": True, "value": 1.0},
        "slip_distance_m": {"available": True, "value": 0.1},
        "slip_velocity_m_s": {"available": True, "value": 0.1},
        "stance_stable_duration_s": {"available": True, "value": 1.0},
    }
    mj_receipt = {"status": "pass", "data_source": "backend", "load_path": "gravity_coupled", "load_path_detail": "boundary helper", "blocked_by_finding": []}
    od_receipt = {"status": "partial", "data_source": "placeholder", "load_path": "gravity_coupled", "load_path_detail": "placeholder boundary helper", "blocked_by_finding": ["Finding-ODE-runtime-blocked"]}

    summary = _build_summary(mj_metrics, od_metrics, mj_receipt, od_receipt)

    assert summary["evidence_label"] == "comparative"
    assert summary["evidence_pass"] is False
    assert summary["backend_data_sources"]["ode"] == "placeholder"
    assert summary["backend_load_paths"]["mujoco"] == "gravity_coupled"
    assert summary["backend_load_paths"]["ode"] == "gravity_coupled"
    assert "Finding-ODE-runtime-blocked" in summary["blocked_by_finding"]["ode"]
