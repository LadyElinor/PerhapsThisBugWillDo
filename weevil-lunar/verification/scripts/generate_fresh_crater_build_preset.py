#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "verification" / "reports"
SELECTED_CSV = REPORT_DIR / "fresh_crater_variant_selection.csv"
CFG = ROOT / "configs" / "fresh_crater_explorer_variants_2026-04-18.yaml"
OUT_JSON = ROOT / "configs" / "fresh_crater_build_presets_2026-04-18.json"
OUT_YAML = ROOT / "cad" / "fresh_crater_leg_params_overlay_2026-04-18.yaml"


def main() -> None:
    if not SELECTED_CSV.exists():
        raise FileNotFoundError(f"missing selection file: {SELECTED_CSV}")
    if not CFG.exists():
        raise FileNotFoundError(f"missing config file: {CFG}")

    with SELECTED_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("selection file is empty")
    chosen = rows[0]

    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    variant_name = str(chosen["selected_variant"])
    variant = cfg["variants"][variant_name]

    preset = {
        "meta": {
            "version": "v0.1",
            "date": "2026-04-18",
            "source_selection": str(SELECTED_CSV.relative_to(ROOT)),
            "default_recommended": variant_name,
        },
        "presets": {
            variant_name: {
                "mission_thread": "fresh_crater_explorer",
                "selected_variant": variant_name,
                "recommended_actuator": chosen.get("recommended_actuator", "unknown"),
                "recommended_geometry_profile": chosen.get("recommended_geometry_profile", "unknown"),
                "build_profile": "fresh_crater",
                "approach_slope_limit_deg": float(variant["approach_slope_limit_deg"]),
                "edge_standoff_m": float(variant["edge_standoff_m"]),
                "partial_descent_limit_deg": float(variant["partial_descent_limit_deg"]),
                "egress_reserve_fraction": float(variant["egress_reserve_fraction"]),
                "telemetry_buffer_min_s": float(variant["telemetry_buffer_min_s"]),
                "disturbance_index_cap": float(variant["disturbance_index_cap"]),
                "slip_abort_threshold": float(variant["slip_abort_threshold"]),
            }
        },
    }

    overlay = {
        "meta": {
            "version": "v0.1",
            "date": "2026-04-18",
            "base_file": "cad/weevil_leg_params.yaml",
            "source_variant": variant_name,
        },
        "fresh_crater_overlay": {
            "mobility": {
                "tilt_warn_deg": min(25.0, float(variant["approach_slope_limit_deg"]) - 2.0),
                "tilt_hard_limit_deg": float(variant["approach_slope_limit_deg"]),
            },
            "power": {
                "fresh_crater_egress_reserve_fraction": float(variant["egress_reserve_fraction"]),
            },
            "sensing": {
                "fresh_crater_telemetry_buffer_min_s": float(variant["telemetry_buffer_min_s"]),
            },
            "foot": {
                "fresh_crater_disturbance_index_cap": float(variant["disturbance_index_cap"]),
                "fresh_crater_slip_abort_threshold": float(variant["slip_abort_threshold"]),
            },
            "integration": {
                "recommended_actuator": chosen.get("recommended_actuator", "unknown"),
                "recommended_geometry_profile": chosen.get("recommended_geometry_profile", "unknown"),
            },
        },
    }

    OUT_JSON.write_text(json.dumps(preset, indent=2) + "\n", encoding="utf-8")
    OUT_YAML.write_text(yaml.safe_dump(overlay, sort_keys=False), encoding="utf-8")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_YAML}")
    print(f"PRESET={variant_name}")


if __name__ == "__main__":
    main()
