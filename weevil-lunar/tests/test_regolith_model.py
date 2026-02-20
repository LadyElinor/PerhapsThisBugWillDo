from models.lunar_integrated_weevil_leg import (
    ContactModel,
    LegState,
    evaluate_leg_state,
    load_params,
)


def test_traction_monotonic_with_regolith_mu() -> None:
    params = load_params()
    state = LegState(0.0, 0.0, 0.0)
    low = evaluate_leg_state(state, params, ContactModel(regolith_mu=0.2, internal_mu=0.01))
    high = evaluate_leg_state(state, params, ContactModel(regolith_mu=0.8, internal_mu=0.01))
    assert high.traction_n > low.traction_n


def test_sinkage_sanity_proxy_bounds() -> None:
    params = load_params()
    state = LegState(0.0, -10.0, 0.0)
    out = evaluate_leg_state(state, params, ContactModel())
    # Proxy sanity: normal load should remain in physically plausible preload envelope.
    assert 0.0 < out.normal_n <= 200.0
