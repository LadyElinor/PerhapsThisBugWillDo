"""COTS-1.1 chassis corrections; all unfinished joint envelopes remain explicit.

This is a separate candidate, not a rewrite of the frozen COTS-1 baseline.
The deck passages do not constitute designed guide mounts.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from models.cots_rover import load_config, nominal_feet

SPEC = ROOT / "verification/cots/tranche_03/spec.json"


def baseline_cad():
    spec = importlib.util.spec_from_file_location("cots_original_cad", ROOT / "cad/scripts/build_cots_rover.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def revision_config():
    c = copy.deepcopy(load_config())
    candidate = json.loads(SPEC.read_text())["candidate"]
    c["design_id"] = candidate["id"]
    c["com_m"][2] += candidate["com_z_increment_m"]
    return c


def packaging(c, feet):
    import cadquery as cq

    candidate = json.loads(SPEC.read_text())["candidate"]
    parts = baseline_cad().packaging(c, feet)
    deck_z = (c["chassis_center_z_m"] - c["chassis_size_m"][2] / 2) * 1000
    for part in parts:
        if part["name"] == "Deck":
            for x in (-270, 270):
                for y in (-145, 145):
                    passage = cq.Solid.makeCylinder(
                        candidate["deck_opening_radius_mm"], 5, cq.Vector(x, y, deck_z - 2.5)
                    )
                    part["shape"] = part["shape"].cut(passage)
        elif part["name"].startswith("Rail_"):
            part["shape"] = part["shape"].translate((0, 0, candidate["rail_raise_mm"]))
        elif part["name"].startswith("Electronics_allowance_"):
            part["shape"] = part["shape"].translate((0, 0, candidate["electronics_raise_mm"]))
    return parts


def build(output):
    import cadquery as cq

    output.mkdir(parents=True, exist_ok=False)
    c = revision_config()
    parts = packaging(c, nominal_feet(c))
    if len(parts) != 86 or any(not p["shape"].isValid() or len(p["shape"].Solids()) != 1 for p in parts):
        raise ValueError("Candidate changed the component inventory or produced invalid geometry")
    assembly = cq.Assembly(name="COTS1_1_packaging_UNRELEASED")
    for p in parts:
        assembly.add(p["shape"], name=p["name"], color=cq.Color(*p["color"]))
    step = output / "rover_packaging.step"
    assembly.save(str(step))
    baseline_cad().normalize_exchange_text(step)
    imported = cq.importers.importStep(str(step)).val()
    volume = sum(p["shape"].Volume() for p in parts)
    error = abs(imported.Volume() - volume) / volume
    if not imported.isValid() or len(imported.Solids()) != len(parts) or error > 1e-8:
        raise ValueError("Candidate STEP roundtrip failed")
    report = {
        "design_id": c["design_id"],
        "status": "CHASSIS_CORRECTION_ONLY_UNRELEASED",
        "solid_count": len(parts),
        "step_roundtrip_relative_volume_error": error,
        "roundtrip_valid": True,
        "fabrication_released": False,
        "unresolved": ["joint and sensor interfaces", "guide mounts and park stops", "cables and fasteners"],
    }
    (output / "cad_checks.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2))
