from __future__ import annotations

from pathlib import Path

from simulators.common.scenario_schema import SimulationScenario


def scenario_to_config_path(scenario: SimulationScenario) -> Path:
    config_name = "single_leg_incline.yaml" if scenario.slope_deg > 0 else "single_leg_basic.yaml"
    return Path(__file__).resolve().parent / "configs" / config_name
