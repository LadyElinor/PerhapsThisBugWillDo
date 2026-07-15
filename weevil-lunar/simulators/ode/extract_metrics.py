from __future__ import annotations

from simulators.common.metrics import BackendMetricValue, CommonMetrics, unavailable_metric


def placeholder_metrics() -> CommonMetrics:
    return CommonMetrics(
        completed=BackendMetricValue(True, note="placeholder ODE scaffold run"),
        failure_mode=BackendMetricValue("", note="no runtime failure in placeholder path"),
        normal_reaction_n=unavailable_metric("not yet extracted from ODE"),
        tangential_reaction_n=unavailable_metric("not yet extracted from ODE"),
        slip_distance_m=unavailable_metric("not yet extracted from ODE"),
        slip_velocity_m_s=unavailable_metric("not yet extracted from ODE"),
        stance_stable_duration_s=unavailable_metric("not yet extracted from ODE"),
        peak_body_pitch_deg=unavailable_metric("not yet extracted from ODE"),
        peak_body_roll_deg=unavailable_metric("not yet extracted from ODE"),
        foot_penetration_proxy_m=unavailable_metric("not yet extracted from ODE"),
        control_effort_proxy=unavailable_metric("not yet extracted from ODE"),
        anchor_state_confirmed=unavailable_metric("not yet extracted from ODE"),
        notes=["placeholder metrics only", "ODE runtime integration not yet wired"],
    )
