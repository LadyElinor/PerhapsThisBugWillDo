from __future__ import annotations

from dataclasses import dataclass

REGIME_OPTIONS = ["quasi_static", "dynamic_placeholder"]


@dataclass(frozen=True)
class GaitCommand:
    phase: str
    duty_factor: float
    cadence_hz: float


class GaitPlanner:
    """Initial multi-leg coordination scaffold.

    This placeholder intentionally keeps policy simple while defining API shape
    for later tripod and recovery gait implementations.
    """

    def __init__(self, regime: str = "quasi_static") -> None:
        if regime not in REGIME_OPTIONS:
            raise ValueError(f"Unsupported regime: {regime}")
        self.regime = regime

    def tripod_gait(self, slope_deg: float, traction_margin: float) -> GaitCommand:
        if self.regime == "dynamic_placeholder":
            return GaitCommand(phase="dynamic_stub", duty_factor=0.55, cadence_hz=0.9)
        if slope_deg >= 25 or traction_margin < 1.2:
            return GaitCommand(phase="stability_tripod", duty_factor=0.68, cadence_hz=0.45)
        return GaitCommand(phase="nominal_tripod", duty_factor=0.58, cadence_hz=0.65)
