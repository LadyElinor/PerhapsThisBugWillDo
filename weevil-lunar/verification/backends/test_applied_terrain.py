from dataclasses import replace
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from simulators.common.scenario_schema import SimulationScenario
from simulators.mujoco.adapters import materialize_scenario_model


def scenario(slope):
    return SimulationScenario("slope_case", "mujoco", 30, 1.62, 6, 1, 0.05, "sphere",
                              "mare", slope, 20, duration_s=0.02)


@pytest.mark.parametrize("slope", [-12, 0, 10, 25, 40])
def test_resolved_model_records_signed_angle_and_integration_settings(tmp_path, slope):
    case = replace(scenario(slope), gravity_m_s2=3.71, timestep_s=0.002)
    path = materialize_scenario_model(case, tmp_path)
    xml = ET.parse(path)
    assert xml.find("./worldbody/geom").get("euler") == f"0 {slope} 0"
    assert xml.find("option").get("gravity") == "0 0 -3.71"
    assert float(xml.find("option").get("timestep")) == 0.002
    assert hashlib.sha256(path.read_bytes()).hexdigest() in path.name


def test_model_trace_and_receipt_share_applied_plane(tmp_path):
    mujoco = pytest.importorskip("mujoco")
    import math
    from simulators.mujoco.runner import run_scenario

    slopes = (-12.0, 0.0, 10.0, 25.0, 40.0)
    hashes = set()
    histories = []
    for slope in slopes:
        metrics, receipt_path = run_scenario(scenario(slope), tmp_path)
        receipt = json.loads(receipt_path.read_text())
        trace = json.loads((metrics.parent / "slope_case_trace.json").read_text())
        state = trace["metadata"]
        assert state["applied_slope_deg"] == pytest.approx(slope, abs=1e-10)
        assert state["applied_gravity_m_s2"] == [0, 0, -1.62]
        assert state["model_artifact"] == receipt["model_artifact"]
        digest = hashlib.sha256(Path(state["model_artifact"]).read_bytes()).hexdigest()
        assert digest == receipt["model_hash"]
        hashes.add(digest)
        model = mujoco.MjModel.from_binary_path(str(metrics.parent / "slope_case.mjb"))
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        name = "slope" if slope > 0 else "ground"
        normal = data.geom(name).xmat.reshape(3, 3)[:, 2]
        assert normal[0] == pytest.approx(math.sin(math.radians(slope)), abs=1e-12)
        assert normal[2] == pytest.approx(math.cos(math.radians(slope)), abs=1e-12)
        histories.append(trace["steps"])
    assert len(hashes) == len(slopes)
    assert histories[2] != histories[3]
