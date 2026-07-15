from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from simulators.common.metrics import BackendMetricValue, CommonMetrics, unavailable_metric
from simulators.common.scenario_schema import SimulationScenario


def _extract_geom_radius(model_path: Path, fallback_radius: float) -> float:
    tree = ET.parse(model_path)
    root = tree.getroot()
    foot_geom = root.find(".//geom[@name='foot_geom']")
    if foot_geom is not None:
        size = foot_geom.attrib.get("size", "").strip().split()
        if size:
            try:
                return float(size[0])
            except ValueError:
                pass
    return fallback_radius


def trace_backed_metrics(
    scenario: SimulationScenario,
    model_path: Path,
    compiled_model_path: Path,
    trace_data: dict,
) -> CommonMetrics:
    """Extract metrics from a custom per-step MuJoCo trace artifact."""
    foot_radius = _extract_geom_radius(model_path, scenario.foot_radius_m)

    steps = trace_data.get("steps", [])
    metadata = trace_data.get("metadata", {})
    summary = trace_data.get("summary", {})

    completed = bool(summary.get("completed", False))
    slip_distance = float(summary.get("slip_distance_m", 0.0))
    max_slip_velocity = float(summary.get("max_slip_velocity_m_s", 0.0))
    contact_steps = int(summary.get("contact_steps", 0))
    total_steps = int(summary.get("total_steps", 0))
    contact_persistence_ratio = float(summary.get("contact_persistence_ratio", 0.0))
    max_contact_force_proxy = float(summary.get("max_contact_force_proxy_n", 0.0))
    mean_contact_force_proxy = float(summary.get("mean_contact_force_proxy_n", 0.0))
    final_foot_x = float(summary.get("final_foot_x_m", 0.0))
    initial_foot_x = float(summary.get("initial_foot_x_m", 0.0))

    stance_stable_duration = contact_steps * scenario.timestep_s
    peak_pitch = abs(float(summary.get("max_body_pitch_deg", scenario.slope_deg)))
    peak_roll = abs(float(summary.get("max_body_roll_deg", 0.0)))

    return CommonMetrics(
        completed=BackendMetricValue(completed, note="custom Python MuJoCo trace completed"),
        failure_mode=BackendMetricValue("", note="no Python MuJoCo trace failure recorded"),
        normal_reaction_n=BackendMetricValue(
            mean_contact_force_proxy,
            note="contact-force proxy from summed contact-frame normal components across active contacts",
        ),
        tangential_reaction_n=BackendMetricValue(
            max_contact_force_proxy,
            note="contact-force proxy upper envelope from active contact frames; still proxy-level, not full wrench decomposition",
        ),
        slip_distance_m=BackendMetricValue(
            slip_distance,
            note=f"foot x-displacement traced from {initial_foot_x:.6f} m to {final_foot_x:.6f} m",
        ),
        slip_velocity_m_s=BackendMetricValue(
            max_slip_velocity,
            note="maximum finite-difference foot x velocity from per-step trace",
        ),
        stance_stable_duration_s=BackendMetricValue(
            stance_stable_duration,
            note=f"contact present for {contact_steps}/{total_steps} steps ({contact_persistence_ratio:.3f} persistence)",
        ),
        peak_body_pitch_deg=BackendMetricValue(peak_pitch, note="max traced body pitch proxy from root orientation"),
        peak_body_roll_deg=BackendMetricValue(peak_roll, note="max traced body roll proxy from root orientation"),
        foot_penetration_proxy_m=BackendMetricValue(
            foot_radius,
            note="geometry proxy from MJCF foot radius; direct penetration depth extraction still pending",
        ),
        control_effort_proxy=BackendMetricValue(
            float(metadata.get("solver_iterations", 0.0)),
            note="solver iteration setting used in traced MuJoCo rollout",
        ),
        anchor_state_confirmed=BackendMetricValue(False, note="anchoring state not modeled in current MuJoCo scaffold"),
        notes=[
            "custom Python MuJoCo trace path active",
            f"compiled model exists at {compiled_model_path}",
            f"trace captured {total_steps} steps",
            f"contact persistence ratio={contact_persistence_ratio:.3f}",
            "slip/contact metrics now come from per-step trace artifact rather than testspeed summary",
        ],
    )
