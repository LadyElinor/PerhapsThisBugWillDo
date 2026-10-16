"""Inventory every modeled solid overlap without promoting envelope contacts to clearance.

The legacy CAD gate only checked actuator pairs and actuator/frame/equipment.
This experiment keeps that claim separate from full mechanical release.
"""

from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from models.cots_rover import gait_samples, load_config, nominal_feet
from run_tranche_02 import SPEC, frozen_spec, sha256


def overlaps(parts, tolerance=1e-5):
    found = []
    boxes = {p["name"]: p["shape"].BoundingBox() for p in parts}
    for a, b in itertools.combinations(parts, 2):
        aa, bb = boxes[a["name"]], boxes[b["name"]]
        if any(
            getattr(aa, v + "max") < getattr(bb, v + "min") or getattr(bb, v + "max") < getattr(aa, v + "min")
            for v in "xyz"
        ):
            continue
        v = a["shape"].intersect(b["shape"]).Volume()
        if v > tolerance:
            la, lb = re.match(r"L(\d+)_", a["name"]), re.match(r"L(\d+)_", b["name"])
            same_leg = bool(la and lb and la.group(1) == lb.group(1))
            frame_joint = a["kind"] == b["kind"] == "frame"
            kind = "unresolved_interface_overlap" if same_leg or frame_joint else "packaging_conflict"
            found.append(
                {
                    "a": a["name"],
                    "b": b["name"],
                    "a_kind": a["kind"],
                    "b_kind": b["kind"],
                    "volume_mm3": v,
                    "classification": kind,
                }
            )
    return found


def controls():
    import cadquery as cq

    a = {"name": "a", "kind": "test", "shape": cq.Workplane("XY").box(10, 10, 10).val()}
    outcomes = {}
    for x, label, expected in [(9, "penetrating", 100), (10, "touching", 0), (11, "separated", 0)]:
        b = {"name": "b", "kind": "test", "shape": a["shape"].translate((x, 0, 0))}
        result = overlaps([a, b])
        measured = sum(r["volume_mm3"] for r in result)
        outcomes[label] = abs(measured - expected) < 1e-6
    if not all(outcomes.values()):
        raise ValueError(f"Geometry controls failed: {outcomes}")
    return outcomes


def run(spec_path, output):
    spec = frozen_spec(spec_path)
    c = load_config()
    module_spec = importlib.util.spec_from_file_location("cots_packaging", ROOT / "cad/scripts/build_cots_rover.py")
    cad = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(cad)
    samples = [("nominal", nominal_feet(c), tuple(range(6)))]
    samples += list(gait_samples(c, spec["geometry"]["subdivisions"]))
    pairs = {}
    pose_count = 0
    solid_count = None
    counts = Counter()
    for name, feet, _ in samples:
        parts = cad.packaging(c, feet)
        if any(not p["shape"].isValid() or len(p["shape"].Solids()) != 1 for p in parts):
            raise ValueError(f"Invalid solid in {name}")
        solid_count = len(parts)
        for row in overlaps(parts, spec["geometry"]["overlap_tolerance_mm3"]):
            key = (row["a"], row["b"])
            counts[row["classification"]] += 1
            if key not in pairs:
                pairs[key] = {
                    **row,
                    "first_pose": name,
                    "poses_with_overlap": 1,
                    "maximum_volume_mm3": row["volume_mm3"],
                }
            else:
                pairs[key]["poses_with_overlap"] += 1
                pairs[key]["maximum_volume_mm3"] = max(pairs[key]["maximum_volume_mm3"], row["volume_mm3"])
        pose_count += 1
        if pose_count % 5 == 0:
            print("geometry poses", pose_count, "unique pairs", len(pairs), flush=True)
    report = {
        "experiment_id": spec["id"],
        "spec_sha256": sha256(spec_path),
        "runner_sha256": sha256(Path(__file__)),
        "controls": controls(),
        "baseline_commit": spec["baseline_commit"],
        "solid_count": solid_count,
        "pose_count": pose_count,
        "pair_checks": pose_count * solid_count * (solid_count - 1) // 2,
        "overlap_occurrences_by_class": dict(counts),
        "unique_overlapping_pairs": len(pairs),
        "unique_pairs_by_class": dict(Counter(r["classification"] for r in pairs.values())),
        "all_modeled_solids_clear": not pairs,
        "fabrication_released": False,
        "pairs": list(pairs.values()),
        "limitations": [
            "Same-leg and frame overlaps are reported as unresolved interfaces, not accepted waivers.",
            "Many solids are envelopes. An overlap is a missing-detail or clearance blocker, not proof two finished parts collide.",
            "No cables, connectors, complete carriers, couplers, fasteners or continuous-motion collision proof exist.",
            "Removing envelopes or suppressing pairs cannot close M2; detailed geometry and independent verification are required.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {k: report[k] for k in ("pose_count", "pair_checks", "unique_overlapping_pairs", "unique_pairs_by_class")}
        )
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=SPEC)
    parser.add_argument("--output", type=Path, default=SPEC.with_name("geometry.json"))
    args = parser.parse_args()
    run(args.spec, args.output)
