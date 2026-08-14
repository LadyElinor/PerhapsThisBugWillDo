#!/usr/bin/env python3
"""Smoke tests for the consolidated contact sub-package.

These guard the Phase 2 consolidation: they confirm the contact model is
importable as a package module (``models.contact``) and that the core
calculations run end-to-end. They are intentionally lightweight -- the
detailed physics gates live in ``models/contact/weevil_lunar_tests.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from models.contact import (  # noqa: E402
    FootGeometry,
    RegolithContactModel,
    RegolithProperties,
    RegolithType,
)


@pytest.fixture
def model():
    reg = RegolithProperties.from_type(RegolithType.MARE)
    foot = FootGeometry.circular(radius=0.05)
    return RegolithContactModel(reg, foot)


def test_contact_package_imports():
    # The package-level re-export must expose the public API.
    from models.contact import regolith_contact_model  # noqa: F401


def test_bearing_capacity_monotonic(model):
    shallow = model.bearing_capacity(0.01)
    deep = model.bearing_capacity(0.05)
    assert 0.0 <= shallow < deep


def test_depth_round_trips_with_normal_load(model):
    # depth -> load -> depth should be self-consistent.
    depth = 0.03
    load = model.normal_load_from_depth(depth)
    recovered = model.depth_from_normal_load(load)
    assert recovered == pytest.approx(depth, rel=1e-3)


def test_body_normal_load_helper(model):
    assert model.body_normal_load(30.0, stance_legs=1, gravity=1.62) == pytest.approx(48.6)
    assert model.body_normal_load(30.0, stance_legs=6, gravity=1.62) == pytest.approx(8.1)


def test_total_normal_load_helper(model):
    total = model.total_normal_load(30.0, stance_legs=6, preload_normal=20.0, gravity=1.62)
    assert total == pytest.approx(28.1)


def test_contact_forces_nonnegative(model):
    forces = model.compute_contact_forces(normal_load=120.0)
    assert forces.max_shear_force >= 0.0
    assert forces.penetration_depth >= 0.0
    assert 0.0 <= forces.friction_cone_angle <= 90.0


def test_preload_anchoring_engages(model):
    """Preload at or above the engage threshold marks the foot anchored."""
    below = model.compute_contact_forces_with_preload(
        body_normal_load=50.0, preload_normal=5.0
    )
    above = model.compute_contact_forces_with_preload(
        body_normal_load=50.0, preload_normal=30.0
    )
    assert below.anchored is False
    assert above.anchored is True


def test_directional_preload_changes_forward_shear():
    reg = RegolithProperties.from_type(RegolithType.MARE)
    foot = FootGeometry.circular(
        radius=0.08,
        cleat_gain_forward=1.5,
        cleat_gain_lateral=1.0,
        cleat_engage_threshold_preload=50.0,
    )
    model = RegolithContactModel(reg, foot)

    low = model.compute_contact_forces_with_preload(
        body_normal_load=50.0,
        preload_normal=30.0,
    )
    high = model.compute_contact_forces_with_preload(
        body_normal_load=50.0,
        preload_normal=50.0,
    )

    assert low.anchored is False
    assert high.anchored is True
    assert high.max_shear_forward > low.max_shear_forward
