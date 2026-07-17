from __future__ import annotations

import json
from pathlib import Path


def test_reference_comparative_artifact_has_honest_semantics():
    artifact = (
        Path(__file__).resolve().parents[1]
        / "reference_artifacts"
        / "demo_single_leg_incline_hold_comparative_report.json"
    )
    assert artifact.exists()

    data = json.loads(artifact.read_text(encoding="utf-8"))
    summary = data["summary"]

    assert summary["evidence_label"] == "comparative"
    assert summary["data_source"] == "placeholder"
    assert summary["evidence_pass"] is False
    assert summary["backend_data_sources"]["mujoco"] == "backend"
    assert summary["backend_data_sources"]["ode"] == "placeholder"
    assert summary["backend_load_paths"]["mujoco"] == "gravity_coupled"
    assert summary["backend_load_paths"]["ode"] == "gravity_coupled"
    assert "ODE remains partial / blocked-runtime" in summary["disagreement_flags"]
