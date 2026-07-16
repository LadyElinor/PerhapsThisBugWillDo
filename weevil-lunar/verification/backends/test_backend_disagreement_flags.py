from __future__ import annotations

import json

from simulators.common.scenario_schema import SimulationScenario
from simulators.mujoco.runner import run_scenario as run_mujoco
from simulators.ode.runner import run_scenario as run_ode


def test_backend_placeholder_disagreement_is_explicit(tmp_path):
    scenario = SimulationScenario(
        scenario_id="test_backend_disagreement_flags",
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
    _, mujoco_receipt = run_mujoco(scenario, output_root=output_root)
    _, ode_receipt = run_ode(scenario, output_root=output_root)
    mj = json.loads(mujoco_receipt.read_text(encoding="utf-8"))
    od = json.loads(ode_receipt.read_text(encoding="utf-8"))
    assert mj["status"] == "partial"
    assert od["status"] == "partial"
    assert "custom Python MuJoCo trace path active" in mj["warnings"]
    assert "placeholder backend path" in od["warnings"]
    assert "ODE runtime execution remains blocked locally" in od["warnings"]
    assert "generated legacy Visual Studio 2008 project files are not directly consumable by current headless MSBuild flow" in od["warnings"]
