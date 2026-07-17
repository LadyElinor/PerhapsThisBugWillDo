from __future__ import annotations

import pytest

from simulators.common.scenario_schema import SimulationScenario


def test_scenario_defaults_to_gravity_coupled_load_path():
    scenario = SimulationScenario(
        scenario_id="test_default_load_path",
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
    assert scenario.load_path == "gravity_coupled"
    scenario.validate()


def test_scenario_rejects_unknown_load_path():
    scenario = SimulationScenario(
        scenario_id="test_bad_load_path",
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
        load_path="mystery_mode",
    )
    with pytest.raises(ValueError):
        scenario.validate()
