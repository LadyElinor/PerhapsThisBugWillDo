from __future__ import annotations

from dataclasses import dataclass


TERRAIN_FACTORS = {
    "ejecta_blockfield": {"traction_multiplier": 0.90, "disturbance_multiplier": 1.20, "telemetry_occlusion_penalty_s": 15.0},
    "rim_transition": {"traction_multiplier": 0.96, "disturbance_multiplier": 1.05, "telemetry_occlusion_penalty_s": 25.0},
    "inner_wall_loose": {"traction_multiplier": 0.82, "disturbance_multiplier": 1.25, "telemetry_occlusion_penalty_s": 45.0},
    "ray_sampling_floor": {"traction_multiplier": 1.00, "disturbance_multiplier": 0.95, "telemetry_occlusion_penalty_s": 10.0},
}


@dataclass
class CraterScenario:
    terrain: str
    slope_deg: float
    base_disturbance_index: float
    base_slip_ratio: float
    telemetry_buffer_min_s: float
    egress_reserve_fraction: float
    edge_standoff_m: float


@dataclass
class CraterEvaluation:
    effective_slip_ratio: float
    effective_disturbance_index: float
    telemetry_buffer_effective_s: float


def evaluate_crater_scenario(s: CraterScenario) -> CraterEvaluation:
    factors = TERRAIN_FACTORS[s.terrain]
    slope_factor = 1.0 + max(0.0, s.slope_deg - 10.0) / 100.0

    effective_slip_ratio = s.base_slip_ratio * (1.0 / factors["traction_multiplier"]) * slope_factor
    effective_disturbance_index = s.base_disturbance_index * factors["disturbance_multiplier"] * slope_factor
    telemetry_buffer_effective_s = max(0.0, s.telemetry_buffer_min_s - factors["telemetry_occlusion_penalty_s"])

    return CraterEvaluation(
        effective_slip_ratio=round(effective_slip_ratio, 4),
        effective_disturbance_index=round(effective_disturbance_index, 4),
        telemetry_buffer_effective_s=round(telemetry_buffer_effective_s, 2),
    )
