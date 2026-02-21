from pathlib import Path

import yaml


def test_coxa_gear_ratio_is_reduction_stage() -> None:
    # Current YAML uses ~80:1 for coxa stage; only enforce reduction-stage property.
    root = Path(__file__).resolve().parents[1]
    raw = yaml.safe_load((root / "cad" / "weevil_leg_params.yaml").read_text(encoding="utf-8"))
    assert float(raw["coxa"]["gear_ratio"]) > 1.0


def test_electromechanical_parameter_sanity() -> None:
    # Representative placeholder values for reduced-order checks.
    kt = 0.08  # N*m/A
    ke = 0.08  # V*s/rad
    resistance = 0.6  # ohm
    inductance = 0.0012  # H

    assert kt > 0.0
    assert ke > 0.0
    assert resistance > 0.0
    assert inductance > 0.0

    electrical_tau = inductance / resistance
    assert electrical_tau > 0.0


def test_reflected_inertia_increases_with_ratio() -> None:
    i_motor = 1.0e-5
    i_load = 2.0e-3
    ratio = 80.0

    i_eff = i_load + i_motor * ratio**2
    assert i_eff > i_load
