from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class BackendMetricValue:
    """One metric value, with explicit availability and provenance notes."""

    value: float | bool | str | None
    available: bool = True
    note: str = ""


@dataclass(frozen=True)
class CommonMetrics:
    """Common metric contract for cross-backend comparison.

    Backends may leave fields unavailable, but must do so explicitly rather than
    pretending unavailable data are comparable.
    """

    completed: BackendMetricValue
    failure_mode: BackendMetricValue
    normal_reaction_n: BackendMetricValue
    tangential_reaction_n: BackendMetricValue
    slip_distance_m: BackendMetricValue
    slip_velocity_m_s: BackendMetricValue
    stance_stable_duration_s: BackendMetricValue
    peak_body_pitch_deg: BackendMetricValue
    peak_body_roll_deg: BackendMetricValue
    foot_penetration_proxy_m: BackendMetricValue
    control_effort_proxy: BackendMetricValue
    anchor_state_confirmed: BackendMetricValue
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def unavailable_metric(note: str) -> BackendMetricValue:
    return BackendMetricValue(value=None, available=False, note=note)
