from __future__ import annotations

import hashlib
import math
from pathlib import Path
from tempfile import NamedTemporaryFile
import xml.etree.ElementTree as ET

from simulators.common.artifact_paths import backend_results_dir

from simulators.common.scenario_schema import SimulationScenario


def scenario_to_model_path(scenario: SimulationScenario) -> Path:
    """Map a canonical scenario to the current placeholder MJCF artifact path."""
    model_name = "single_leg_incline.xml" if scenario.slope_deg > 0 else "single_leg_basic.xml"
    return Path(__file__).resolve().parent / "models" / model_name


def materialize_scenario_model(scenario: SimulationScenario, output_root: Path | None) -> Path:
    """Bind the terrain and integration settings into the exact MJCF used for the run."""
    scenario.validate()
    if not all(math.isfinite(x) for x in
               (scenario.slope_deg, scenario.gravity_m_s2, scenario.timestep_s)):
        raise ValueError("slope, gravity and timestep must be finite")
    template = scenario_to_model_path(scenario)
    root = ET.parse(template).getroot()
    plane = root.find("./worldbody/geom[@type='plane']")
    option = root.find("option")
    if plane is None or option is None:
        raise ValueError(f"missing terrain or simulation options in {template.name}")
    plane.set("euler", f"0 {scenario.slope_deg} 0")
    option.set("gravity", f"0 0 {-scenario.gravity_m_s2}")
    option.set("timestep", str(scenario.timestep_s))
    payload = ET.tostring(root, encoding="utf-8")
    directory = backend_results_dir("mujoco", output_root)
    path = directory / ("terrain-" + hashlib.sha256(payload).hexdigest() + ".xml")
    if not path.exists() or path.read_bytes() != payload:
        with NamedTemporaryFile(dir=directory, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
        try:
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return path
