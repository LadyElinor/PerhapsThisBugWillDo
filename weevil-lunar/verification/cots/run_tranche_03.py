"""Verify the explicit COTS-1.1 corrections, without releasing unfinished hardware."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from models.cots_rover import gait_samples, nominal_feet
from models.cots_support_guard import phase_preflight

SPEC = Path(__file__).with_name("tranche_03") / "spec.json"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry_report(spec, cad, c):
    # Reuse the exact all-pairs detector; no candidate-specific collision waivers.
    sys.path.insert(0, str(Path(__file__).parent))
    checker = module("original_overlap_checker", Path(__file__).with_name("check_all_geometry.py"))
    controls = checker.controls()
    base = json.loads((SPEC.parent.parent / "tranche_02/geometry.json").read_text())
    old_pairs = {tuple(sorted((p["a"], p["b"]))): p for p in base["pairs"]}
    targets = {tuple(sorted(pair)) for pair in spec["geometry"]["required_resolved_pairs"]}
    nominal = nominal_feet(c)
    old_parts = {p["name"]: p for p in cad.baseline_cad().packaging(c, nominal)}
    original_names = set(old_parts)
    original_volumes = {name: p["shape"].Volume() for name, p in old_parts.items()}
    samples = [("nominal", nominal, tuple(range(6))), *gait_samples(c, spec["geometry"]["subdivisions"])]
    pairs = {}
    count = 0
    equipment_gaps = []
    deck_guide_gaps = []
    roof_gaps = []
    for pose, feet, _ in samples:
        parts = cad.packaging(c, feet)
        by_name = {p["name"]: p for p in parts}
        if len(parts) != spec["geometry"]["expected_component_count"] or set(by_name) != original_names:
            raise ValueError("Missing, duplicate or added component: an inventory change needs its own review")
        for p in parts:
            if not p["shape"].isValid() or len(p["shape"].Solids()) != 1:
                raise ValueError(f"Invalid shape at {pose}: {p['name']}")
            removed = original_volumes[p["name"]] - p["shape"].Volume()
            expected = 4 * math.pi * spec["candidate"]["deck_opening_radius_mm"] ** 2 * 3 if p["name"] == "Deck" else 0
            if abs(removed - expected) > 1e-5:
                raise ValueError(f"Unexpected material/envelope change: {p['name']}")
        for x in (-270, 270):
            for y in (-145, 145):
                guide = by_name[f"LandingGuide_{x}_{y}"]["shape"]
                equipment = by_name[f"Electronics_allowance_{-1 if x < 0 else 1}"]["shape"]
                equipment_gaps.append(guide.distance(equipment))
                deck_guide_gaps.append(guide.distance(by_name["Deck"]["shape"]))
                roof_gaps.append(1000 * (c["chassis_center_z_m"] + c["chassis_size_m"][2] / 2) - equipment.BoundingBox().zmax)
        for row in checker.overlaps(parts, spec["geometry"]["overlap_tolerance_mm3"]):
            key = tuple(sorted((row["a"], row["b"])))
            if key not in pairs:
                pairs[key] = {**row, "first_pose": pose, "poses_with_overlap": 0, "maximum_volume_mm3": 0.0}
            pairs[key]["poses_with_overlap"] += 1
            pairs[key]["maximum_volume_mm3"] = max(pairs[key]["maximum_volume_mm3"], row["volume_mm3"])
        count += 1
        if count % 5 == 0:
            print("candidate geometry", count, "poses; unresolved pairs", len(pairs), flush=True)
    current = set(pairs)
    checks = {
        "all_components_retained": True,
        "all_commercial_envelope_volumes_preserved": True,
        "only_declared_deck_material_removed": True,
        "all_ten_target_pairs_resolved": not targets & current,
        "no_new_overlap_pairs": not current - set(old_pairs),
        "untouched_interface_findings_retained": current == set(old_pairs) - targets,
        "guide_deck_clearance": min(deck_guide_gaps) >= spec["geometry"]["minimum_guide_radial_clearance_mm"] - 1e-6,
        "guide_equipment_clearance": min(equipment_gaps) >= spec["geometry"]["minimum_guide_equipment_clearance_mm"] - 1e-6,
        "equipment_roof_clearance": min(roof_gaps) >= spec["geometry"]["minimum_equipment_roof_clearance_mm"] - 1e-6,
    }
    ledger = []
    for key, old in old_pairs.items():
        ledger.append({
            "a": old["a"], "b": old["b"],
            "status": "MODELED_OVERLAP_RESOLVED_INTERFACE_REVIEW_OPEN" if key in targets and key not in current else "UNRESOLVED_INTERFACE",
            "action": (
                "Review deck/rail joints, guide mounts, stiffness and tolerance stack before fabrication"
                if key in targets else
                "Supply complete bearing/shaft/coupler/clevis/sensor adapter geometry and load path; retain envelope until replaced"
            ),
        })
    return {
        "checks": checks, "controls": controls, "pose_count": count, "solid_count": len(original_names),
        "pair_checks": count * len(original_names) * (len(original_names) - 1) // 2,
        "baseline_overlapping_pairs": len(old_pairs), "resolved_modeled_pairs": len(set(old_pairs) - current),
        "remaining_overlapping_pairs": len(pairs), "new_pairs": [list(p) for p in sorted(current - set(old_pairs))],
        "minimum_guide_deck_clearance_mm": min(deck_guide_gaps),
        "minimum_guide_equipment_clearance_mm": min(equipment_gaps),
        "minimum_equipment_roof_clearance_mm": min(roof_gaps),
        "removed_deck_mass_kg_at_assumed_2700kg_m3": 4 * math.pi * 20**2 * 3 * 1e-9 * 2700,
        "all_modeled_solids_clear": not pairs, "fabrication_released": False,
        "pairs": list(pairs.values()), "baseline_issue_ledger": ledger,
    }


def run(output, *, include_geometry=True):
    spec = json.loads(SPEC.read_text())
    for path, expected in spec["frozen_inputs_sha256"].items():
        if sha256(ROOT / path) != expected:
            raise ValueError(f"Frozen COTS-1 baseline changed: {path}")
    cad = module("candidate_cad", ROOT / "cad/scripts/build_cots_revision.py")
    c = cad.revision_config()
    results = []
    for phase in range(6):
        result = phase_preflight(c, phase, spec["statics"]["subdivisions"], spec["statics"]["slope_deg"])
        results.append(result)
        print("phase", phase, "nominal rejects", result["nominal_rejected"], "loss rejects", result["loss_rejected"], flush=True)
    report = {
        "experiment_id": spec["id"], "spec_sha256": sha256(SPEC),
        "input_sha256": {p: sha256(ROOT / p) for p in [
            "cad/scripts/build_cots_revision.py", "models/cots_support_guard.py", "verification/cots/run_tranche_03.py"
        ]},
        "config": c, "phases": results,
        "counts": dict(Counter({k: sum(r[k] for r in results) for k in (
            "nominal_cases", "nominal_rejected", "loss_cases", "loss_rejected"
        )})),
        "hardware_motion_allowed": False, "fabrication_released": False, "dynamic_recovery_proven": False,
    }
    if include_geometry:
        report["geometry"] = geometry_report(spec, cad, c)
    checks = {"revised_nominal_statics_pass": all(r["nominal_static_pass"] for r in results)}
    if include_geometry:
        checks.update(report["geometry"]["checks"])
    report["correction_checks"] = checks
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    if not all(checks.values()):
        raise ValueError("Declared correction failed; inspect report. Hardware remains blocked.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=SPEC.with_name("results.json"))
    parser.add_argument("--statics-only", action="store_true")
    args = parser.parse_args()
    run(args.output, include_geometry=not args.statics_only)
