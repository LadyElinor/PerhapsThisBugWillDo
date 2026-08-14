#!/usr/bin/env python3
"""Regression tests for the reduced-order lunar weevil leg model."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "cad" / "scripts"))

from models.lunar_integrated_weevil_leg import (  # noqa: E402
    MOON_G,
    ContactModel,
    LegState,
    axis_is_within_tolerance,
    body_normal_load_n,
    evaluate_leg_state,
    helical_displacement_mm,
    load_params,
)


@pytest.fixture(scope="module")
def params():
    return load_params()


@pytest.fixture(scope="module")
def contact():
    return ContactModel()


def test_helical_displacement_zero():
    assert helical_displacement_mm(0.0, 13.5) == 0.0


def test_helical_displacement_full_revolution():
    assert helical_displacement_mm(360.0, 13.5) == pytest.approx(13.5)


def test_helical_displacement_sign():
    assert helical_displacement_mm(-180.0, 13.5) == pytest.approx(-6.75)


def test_tibia_neutral_is_half_stroke(params, contact):
    state = LegState(coxa_yaw_deg=0.0, femur_pitch_deg=0.0, tibia_theta_deg=0.0)
    result = evaluate_leg_state(state, params, contact)
    expected_tip_x = params.femur_link_mm + params.tibia_stroke_mm / 2.0
    assert result.tip_x_mm == pytest.approx(expected_tip_x)
    assert result.tip_x_mm != pytest.approx(params.femur_link_mm + params.tibia_stroke_mm)


def test_tibia_extension_symmetric_about_neutral(params, contact):
    neutral = evaluate_leg_state(LegState(0.0, 0.0, 0.0), params, contact).tip_x_mm
    plus = evaluate_leg_state(LegState(0.0, 0.0, 40.0), params, contact).tip_x_mm
    minus = evaluate_leg_state(LegState(0.0, 0.0, -40.0), params, contact).tip_x_mm
    assert (plus - neutral) == pytest.approx(neutral - minus)


def test_coxa_yaw_rotates_tip_about_vertical_axis(params, contact):
    state0 = LegState(coxa_yaw_deg=0.0, femur_pitch_deg=45.0, tibia_theta_deg=0.0)
    state1 = LegState(coxa_yaw_deg=30.0, femur_pitch_deg=45.0, tibia_theta_deg=0.0)

    r0 = evaluate_leg_state(state0, params, contact)
    r1 = evaluate_leg_state(state1, params, contact)

    assert (r1.tip_x_mm, r1.tip_y_mm) != pytest.approx((r0.tip_x_mm, r0.tip_y_mm))
    assert r0.tip_y_mm == pytest.approx(0.0, abs=1e-9)

    horizontal0 = (r0.tip_x_mm**2 + r0.tip_y_mm**2) ** 0.5
    horizontal1 = (r1.tip_x_mm**2 + r1.tip_y_mm**2) ** 0.5
    assert horizontal1 == pytest.approx(horizontal0)
    assert r1.tip_z_mm == pytest.approx(r0.tip_z_mm)


def test_traction_no_double_gravity_scaling(params):
    contact = ContactModel(regolith_mu=0.55, internal_mu=0.004)
    result = evaluate_leg_state(LegState(0.0, 0.0, 0.0), params, contact)
    expected_normal = body_normal_load_n(30.0, MOON_G, 1) + params.preload_n
    expected = (
        contact.regolith_mu
        * expected_normal
        * params.cleat_forward_gain
        * (1.0 - contact.internal_mu)
    )
    assert result.traction_n == pytest.approx(expected)
    buggy = expected * (MOON_G / 9.81)
    assert result.traction_n != pytest.approx(buggy)


def test_traction_scales_with_preload(params):
    contact = ContactModel()
    low = evaluate_leg_state(LegState(0.0, 0.0, 0.0), params, contact, commanded_preload_n=0.0).traction_n
    high = evaluate_leg_state(LegState(0.0, 0.0, 0.0), params, contact, commanded_preload_n=50.0).traction_n
    assert low > 0.0
    assert high > low


def test_body_normal_load_helper():
    assert body_normal_load_n(30.0, MOON_G, 1) == pytest.approx(48.6)
    assert body_normal_load_n(30.0, MOON_G, 6) == pytest.approx(8.1)


def test_normal_force_is_body_load_plus_preload(params, contact):
    result = evaluate_leg_state(LegState(0.0, 0.0, 0.0), params, contact)
    assert result.body_normal_n == pytest.approx(body_normal_load_n(30.0, MOON_G, 1))
    assert result.preload_n == pytest.approx(params.preload_n)
    assert result.normal_n == pytest.approx(result.body_normal_n + result.preload_n)


def test_axis_tolerance_basic():
    assert axis_is_within_tolerance(actual_deg=88.0, target_deg=90.0, tol_deg=15.0)
    assert not axis_is_within_tolerance(actual_deg=50.0, target_deg=90.0, tol_deg=15.0)


def test_axis_guard_checks_design_target(params):
    assert axis_is_within_tolerance(params.axis_target_deg, 90.0, params.axis_tol_deg)
    drifted = 90.0 + params.axis_tol_deg + 5.0
    assert not axis_is_within_tolerance(drifted, 90.0, params.axis_tol_deg)


def test_out_of_range_state_not_reachable(params, contact):
    over = params.coxa_range[1] + 30.0
    result = evaluate_leg_state(LegState(over, 0.0, 0.0), params, contact)
    assert result.reachable is False


def test_in_range_state_reachable(params, contact):
    result = evaluate_leg_state(LegState(0.0, 0.0, 0.0), params, contact)
    assert result.reachable is True
