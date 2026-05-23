#!/usr/bin/env python3
"""Tests for the weevil_leg_params.yaml validator.

Phase 3 extended the validator to cover the eight subsystem sections that
were previously unchecked (tfj_compliance, gait_phase, coupling, mobility,
thermal, power, sensing, urdf_defaults). These tests confirm the real YAML
passes and that representative malformed inputs are rejected.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cad" / "scripts"))

from validate_weevil_leg_params import (  # noqa: E402
    ValidationError,
    validate,
)

YAML_PATH = ROOT / "cad" / "weevil_leg_params.yaml"


@pytest.fixture(scope="module")
def base_data():
    return yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))


def test_real_yaml_is_valid(base_data):
    # The committed parameter file must always pass validation.
    validate(base_data)


def test_tilt_warn_must_be_below_hard_limit(base_data):
    bad = copy.deepcopy(base_data)
    bad["mobility"]["tilt_warn_deg"] = bad["mobility"]["tilt_hard_limit_deg"] + 5.0
    with pytest.raises(ValidationError, match="tilt_warn"):
        validate(bad)


def test_power_budget_must_close(base_data):
    bad = copy.deepcopy(base_data)
    bad["power"]["night_survival_load_Wh"] = (
        bad["power"]["day_energy_available_Wh"] + 100.0
    )
    with pytest.raises(ValidationError, match="day_energy_available"):
        validate(bad)


def test_boolean_field_rejects_non_bool(base_data):
    bad = copy.deepcopy(base_data)
    bad["sensing"]["watchdog_enabled"] = "yes"
    with pytest.raises(ValidationError, match="boolean"):
        validate(bad)


def test_enum_field_rejects_unknown_value(base_data):
    bad = copy.deepcopy(base_data)
    bad["mobility"]["mode_default"] = "turbo"
    with pytest.raises(ValidationError, match="must be one of"):
        validate(bad)


def test_stance_fractions_must_be_ordered(base_data):
    bad = copy.deepcopy(base_data)
    bad["gait_phase"]["min_stance_fraction"] = (
        bad["gait_phase"]["max_stance_fraction"] + 0.1
    )
    with pytest.raises(ValidationError, match="min_stance_fraction"):
        validate(bad)


def test_urdf_mass_out_of_range_rejected(base_data):
    bad = copy.deepcopy(base_data)
    bad["urdf_defaults"]["mass_kg"]["coxa"] = 999.0
    with pytest.raises(ValidationError, match="mass_kg.coxa"):
        validate(bad)


def test_missing_optional_section_is_allowed(base_data):
    # Subsystem sections are optional; dropping one must not fail validation.
    reduced = copy.deepcopy(base_data)
    del reduced["thermal"]
    validate(reduced)


def test_missing_required_field_in_section_rejected(base_data):
    # ... but if a section IS present, its required fields must exist.
    bad = copy.deepcopy(base_data)
    del bad["power"]["dust_derate_factor"]
    with pytest.raises(ValidationError, match="power.dust_derate_factor"):
        validate(bad)
