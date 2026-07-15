from __future__ import annotations

from simulators.common.metrics import BackendMetricValue, CommonMetrics, unavailable_metric


def test_common_metrics_shape_smoke():
    metrics = CommonMetrics(
        completed=BackendMetricValue(True),
        failure_mode=BackendMetricValue(""),
        normal_reaction_n=unavailable_metric("stub"),
        tangential_reaction_n=unavailable_metric("stub"),
        slip_distance_m=unavailable_metric("stub"),
        slip_velocity_m_s=unavailable_metric("stub"),
        stance_stable_duration_s=unavailable_metric("stub"),
        peak_body_pitch_deg=unavailable_metric("stub"),
        peak_body_roll_deg=unavailable_metric("stub"),
        foot_penetration_proxy_m=unavailable_metric("stub"),
        control_effort_proxy=unavailable_metric("stub"),
        anchor_state_confirmed=unavailable_metric("stub"),
    )
    data = metrics.to_dict()
    assert "completed" in data
    assert data["normal_reaction_n"]["available"] is False
