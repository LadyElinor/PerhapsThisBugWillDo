#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import yaml

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None

CFG = Path("configs/fresh_crater_explorer_variants_2026-04-18.yaml")
CAD_CFG = Path("cad/assets/fresh_crater_candidates.yaml")
REPORT_DIR = Path("verification/reports")

SCHEMA = {
    "type": "object",
    "required": ["meta", "variants"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["version", "date", "purpose", "default_recommended"],
        },
        "variants": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": {
                "type": "object",
                "required": [
                    "description",
                    "mission_phases",
                    "approach_slope_limit_deg",
                    "edge_standoff_m",
                    "partial_descent_limit_deg",
                    "egress_reserve_fraction",
                    "telemetry_buffer_min_s",
                    "disturbance_index_cap",
                    "slip_abort_threshold",
                    "preferred_actuator_candidate",
                    "leg_module_profile",
                    "evidence_tier",
                ],
                "properties": {
                    "mission_phases": {"type": "array", "items": {"type": "string"}, "minItems": 4},
                    "approach_slope_limit_deg": {"type": "number", "minimum": 0.0, "maximum": 45.0},
                    "edge_standoff_m": {"type": "number", "exclusiveMinimum": 0.0},
                    "partial_descent_limit_deg": {"type": "number", "minimum": 0.0, "maximum": 45.0},
                    "egress_reserve_fraction": {"type": "number", "minimum": 0.20, "maximum": 0.60},
                    "telemetry_buffer_min_s": {"type": "number", "minimum": 30.0},
                    "disturbance_index_cap": {"type": "number", "exclusiveMinimum": 0.0, "exclusiveMaximum": 1.0},
                    "slip_abort_threshold": {"type": "number", "exclusiveMinimum": 0.0, "exclusiveMaximum": 1.0},
                    "preferred_actuator_candidate": {"type": "string"},
                    "leg_module_profile": {"type": "string"},
                    "evidence_tier": {"type": "string", "const": "geometry_only"},
                },
            },
        },
    },
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    cad = yaml.safe_load(CAD_CFG.read_text(encoding="utf-8"))
    admitted = {a["asset_id"] for a in cad.get("assets", [])}

    errs = []
    if Draft202012Validator is not None:
        validator = Draft202012Validator(SCHEMA)
        errs = sorted(validator.iter_errors(data), key=lambda e: e.path)

    cross_errors: list[str] = []
    for name, v in data.get("variants", {}).items():
        required = [
            "description",
            "mission_phases",
            "approach_slope_limit_deg",
            "edge_standoff_m",
            "partial_descent_limit_deg",
            "egress_reserve_fraction",
            "telemetry_buffer_min_s",
            "disturbance_index_cap",
            "slip_abort_threshold",
            "preferred_actuator_candidate",
            "leg_module_profile",
            "evidence_tier",
        ]
        missing = [k for k in required if k not in v]
        if missing:
            cross_errors.append(f"{name}: missing required keys {missing}")
            continue
        if float(v.get("partial_descent_limit_deg", 0.0)) > float(v.get("approach_slope_limit_deg", 0.0)):
            cross_errors.append(f"{name}: partial_descent_limit_deg must be <= approach_slope_limit_deg")
        if float(v.get("egress_reserve_fraction", 0.0)) < 0.20:
            cross_errors.append(f"{name}: egress_reserve_fraction must be >= 0.20")
        if float(v.get("slip_abort_threshold", 0.0)) >= float(v.get("disturbance_index_cap", 1.0)):
            cross_errors.append(f"{name}: slip_abort_threshold should remain below disturbance_index_cap for conservative crater operations")
        if str(v.get("preferred_actuator_candidate")) not in admitted:
            cross_errors.append(f"{name}: preferred_actuator_candidate not found in admitted CAD asset manifest")
        if str(v.get("leg_module_profile")) not in admitted:
            cross_errors.append(f"{name}: leg_module_profile not found in admitted CAD asset manifest")

    passed = not errs and not cross_errors

    csv_path = REPORT_DIR / "fresh_crater_variant_validation.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["check", "message", "pass"])
        w.writeheader()
        if passed:
            w.writerow({"check": "schema_and_cross_rules", "message": "all checks passed", "pass": True})
        else:
            for e in errs:
                w.writerow({"check": "schema", "message": f"{list(e.path)}: {e.message}", "pass": False})
            for ce in cross_errors:
                w.writerow({"check": "cross_rule", "message": ce, "pass": False})

    md_path = REPORT_DIR / "fresh_crater_variant_validation.md"
    lines = [
        "# Fresh Crater Variant Validation",
        "",
        f"- status: **{'PASS' if passed else 'FAIL'}**",
        f"- config: `{CFG}`",
        "",
    ]
    if passed:
        lines.append("All schema and cross-field checks passed.")
    else:
        lines.append("## Errors")
        for e in errs:
            lines.append(f"- schema: `{list(e.path)}` -> {e.message}")
        for ce in cross_errors:
            lines.append(f"- cross-rule: {ce}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={'pass' if passed else 'fail'}")


if __name__ == "__main__":
    main()
