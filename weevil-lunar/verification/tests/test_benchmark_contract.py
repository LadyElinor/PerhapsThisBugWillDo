"""The benchmark must reject missing directional capacity, not invent a value."""

from dataclasses import replace

import pytest

from benchmark_runner import scenario_contact_traction
from models.contact import RegolithContactModel
from models.lunar_integrated_weevil_leg import ContactModel, LegState, load_params


def test_benchmark_rejects_missing_forward_shear(monkeypatch):
    compute = RegolithContactModel.compute_contact_forces_with_preload

    def missing_forward_shear(self, *args, **kwargs):
        return replace(compute(self, *args, **kwargs), max_shear_forward=None)

    monkeypatch.setattr(RegolithContactModel, "compute_contact_forces_with_preload", missing_forward_shear)

    with pytest.raises(ValueError, match="did not provide forward shear capacity"):
        scenario_contact_traction(load_params(), LegState(0.0, 0.0, 0.0), ContactModel())
