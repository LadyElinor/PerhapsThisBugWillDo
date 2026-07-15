from __future__ import annotations

from pathlib import Path

from simulators.common.scenario_schema import SimulationScenario


def scenario_to_model_path(scenario: SimulationScenario) -> Path:
    """Map a canonical scenario to the current placeholder MJCF artifact path."""
    model_name = "single_leg_incline.xml" if scenario.slope_deg > 0 else "single_leg_basic.xml"
    return Path(__file__).resolve().parent / "models" / model_name
