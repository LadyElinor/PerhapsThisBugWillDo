from __future__ import annotations

import json

import pytest

pytest.importorskip("mujoco")

from simulators.common.scenario_schema import SimulationScenario
from simulators.mujoco.runner import run_scenario as run_mujoco
from simulators.ode.runner import run_scenario as run_ode


def test_backend_parity_smoke_runs_receipt_paths(tmp_path):
    scenario = SimulationScenario(
        scenario_id="test_backend_parity_smoke",
        backend="comparative",
        body_mass_kg=30.0,
        gravity_m_s2=1.62,
        leg_count=6,
        stance_legs=1,
        foot_radius_m=0.05,
        foot_geometry_kind="sphere",
        terrain_class="mare",
        slope_deg=25.0,
        preload_normal_n=20.0,
    )
    output_root = tmp_path / "simulation"
    mujoco_metrics, mujoco_receipt = run_mujoco(scenario, output_root=output_root)
    ode_metrics, ode_receipt = run_ode(scenario, output_root=output_root)
    assert mujoco_metrics.exists()
    assert mujoco_receipt.exists()
    assert ode_metrics.exists()
    assert ode_receipt.exists()
    assert str(mujoco_metrics).startswith(str(output_root))
    assert str(ode_metrics).startswith(str(output_root))

    mj = json.loads(mujoco_receipt.read_text(encoding="utf-8"))
    od = json.loads(ode_receipt.read_text(encoding="utf-8"))
    assert mj["load_path"] == "gravity_coupled"
    assert od["load_path"] == "gravity_coupled"
