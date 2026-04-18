#!/usr/bin/env python3
"""Verify fresh-crater preset generation and materialization artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PRESET_JSON = ROOT / "configs" / "fresh_crater_build_presets_2026-04-18.json"
OVERLAY_YAML = ROOT / "cad" / "fresh_crater_leg_params_overlay_2026-04-18.yaml"
MATERIALIZED_YAML = ROOT / "cad" / "generated" / "weevil_leg_params_fresh_crater_2026-04-18.yaml"
SELECTION_CSV = ROOT / "verification" / "reports" / "fresh_crater_variant_selection.csv"


def main() -> None:
    for path in [PRESET_JSON, OVERLAY_YAML, MATERIALIZED_YAML, SELECTION_CSV]:
        assert path.exists(), f"missing required artifact: {path}"

    preset = json.loads(PRESET_JSON.read_text(encoding="utf-8"))
    overlay = yaml.safe_load(OVERLAY_YAML.read_text(encoding="utf-8"))
    materialized = yaml.safe_load(MATERIALIZED_YAML.read_text(encoding="utf-8"))

    with SELECTION_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows, "selection csv is empty"
    selected_variant = rows[0]["selected_variant"]
    selected_actuator = rows[0]["recommended_actuator"]
    selected_geometry = rows[0]["recommended_geometry_profile"]

    preset_entry = preset["presets"][selected_variant]
    overlay_integration = overlay["fresh_crater_overlay"]["integration"]
    materialized_integration = materialized["integration"]

    checks = {
        "preset_selected_variant_ok": preset["meta"]["default_recommended"] == selected_variant,
        "preset_actuator_ok": preset_entry["recommended_actuator"] == selected_actuator,
        "preset_geometry_ok": preset_entry["recommended_geometry_profile"] == selected_geometry,
        "overlay_actuator_ok": overlay_integration["recommended_actuator"] == selected_actuator,
        "overlay_geometry_ok": overlay_integration["recommended_geometry_profile"] == selected_geometry,
        "materialized_actuator_ok": materialized_integration["recommended_actuator"] == selected_actuator,
        "materialized_geometry_ok": materialized_integration["recommended_geometry_profile"] == selected_geometry,
        "materialized_profile_ok": materialized["meta"].get("materialized_profile") == "fresh_crater",
    }
    passed = all(checks.values())

    report_dir = ROOT / "verification" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "fresh_crater_preset_integrity.csv"
    md_path = report_dir / "fresh_crater_preset_integrity.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["check", "pass"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for k, v in checks.items():
            w.writerow({"check": k, "pass": v})

    lines = [
        "# Fresh Crater Preset Integrity Check",
        "",
        f"- selected variant: `{selected_variant}`",
        f"- status: **{'PASS' if passed else 'FAIL'}**",
        "",
        "| check | pass |",
        "|---|---:|",
    ]
    for k, v in checks.items():
        lines.append(f"| {k} | {int(bool(v))} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={'pass' if passed else 'fail'}")


if __name__ == "__main__":
    main()
