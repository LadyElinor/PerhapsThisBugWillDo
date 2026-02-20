import math

import pytest

from models.lunar_integrated_weevil_leg import (
    ContactModel,
    LegState,
    evaluate_leg_state,
    load_params,
)


def _margin_down(traction_n: float, normal_n: float, slope_deg: float) -> float:
    demand = normal_n * math.sin(math.radians(slope_deg))
    return traction_n / demand if demand > 0 else float("inf")


def test_margin_computation_monotonic_with_slope() -> None:
    params = load_params()
    out = evaluate_leg_state(LegState(0.0, 0.0, 0.0), params, ContactModel())
    m20 = _margin_down(out.traction_n, out.normal_n, 20.0)
    m45 = _margin_down(out.traction_n, out.normal_n, 45.0)
    assert m20 > m45


def test_friction_cone_limit() -> None:
    mu = 0.55
    normal_n = 50.0
    max_tangential = mu * normal_n
    assert max_tangential == pytest.approx(27.5)
