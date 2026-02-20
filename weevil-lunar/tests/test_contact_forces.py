from models.lunar_integrated_weevil_leg import (
    ContactModel,
    LegState,
    evaluate_leg_state,
    load_params,
)


def test_internal_friction_reduces_traction() -> None:
    params = load_params()
    state = LegState(0.0, 0.0, 0.0)
    ideal = evaluate_leg_state(state, params, ContactModel(regolith_mu=0.6, internal_mu=0.0))
    lossy = evaluate_leg_state(state, params, ContactModel(regolith_mu=0.6, internal_mu=0.2))
    assert lossy.traction_n < ideal.traction_n


def test_traction_is_non_negative() -> None:
    params = load_params()
    state = LegState(0.0, 0.0, 0.0)
    out = evaluate_leg_state(state, params, ContactModel(regolith_mu=0.0, internal_mu=0.99))
    assert out.traction_n >= 0.0
