from __future__ import annotations

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
    mujoco_metrics, mujoco_receipt = run_mujoco(scenario)
    ode_metrics, ode_receipt = run_ode(scenario)
    assert mujoco_metrics.exists()
    assert mujoco_receipt.exists()
    assert ode_metrics.exists()
    assert ode_receipt.exists()
