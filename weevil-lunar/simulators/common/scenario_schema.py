from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SimulationScenario:
    """Engine-agnostic scenario contract for all simulation backends.

    This schema is intentionally modest in v0. It exists to keep MuJoCo, ODE,
    and reduced-order runs aligned at the input layer before backend-specific
    sophistication grows.
    """

    scenario_id: str
    backend: str
    body_mass_kg: float
    gravity_m_s2: float
    leg_count: int
    stance_legs: int
    foot_radius_m: float
    foot_geometry_kind: str
    terrain_class: str
    slope_deg: float
    preload_normal_n: float
    twist_settle_gain_assumed: float = 1.0
    cleat_gain_forward_assumed: float = 1.0
    cleat_gain_lateral_assumed: float = 1.0
    control_mode: str = "quasi_static"
    maneuver: str = "single_leg_incline_hold"
    duration_s: float = 2.0
    timestep_s: float = 0.001
    notes: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")
        if self.body_mass_kg <= 0:
            raise ValueError("body_mass_kg must be > 0")
        if self.gravity_m_s2 <= 0:
            raise ValueError("gravity_m_s2 must be > 0")
        if self.leg_count <= 0:
            raise ValueError("leg_count must be > 0")
        if self.stance_legs <= 0 or self.stance_legs > self.leg_count:
            raise ValueError("stance_legs must be in [1, leg_count]")
        if self.foot_radius_m <= 0:
            raise ValueError("foot_radius_m must be > 0")
        if self.duration_s <= 0:
            raise ValueError("duration_s must be > 0")
        if self.timestep_s <= 0:
            raise ValueError("timestep_s must be > 0")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
