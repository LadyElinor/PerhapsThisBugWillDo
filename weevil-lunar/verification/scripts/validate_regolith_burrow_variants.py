#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

CFG = Path("configs/regolith_burrow_variants_2026-03-14.yaml")
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
                    "leading_profile",
                    "body_form",
                    "propulsion_mode",
                    "phases",
                    "max_target_depth_m",
                    "disturbance_index_cap",
                    "collapse_risk_abort_threshold",
                    "resurfacing_margin_min",
                    "min_energy_reserve_fraction",
                    "max_component_temp_c",
                    "sensing",
                    "integration_mode",
                ],
                "properties": {
                    "leading_profile": {"type": "string", "enum": ["wedge_shovel", "wedge", "shovel"]},
                    "propulsion_mode": {"type": "string", "const": "rotational_coupled_translation"},
                    "phases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 3,
                    },
                    "max_target_depth_m": {"type": "number", "exclusiveMinimum": 0.0, "maximum": 1.0},
                    "disturbance_index_cap": {"type": "number", "exclusiveMinimum": 0.0, "exclusiveMaximum": 1.0},
                    "collapse_risk_abort_threshold": {"type": "number", "exclusiveMinimum": 0.0, "exclusiveMaximum": 1.0},
                    "resurfacing_margin_min": {"type": "number", "minimum": 1.0},
                    "min_energy_reserve_fraction": {"type": "number", "minimum": 0.05, "maximum": 0.5},
                    "max_component_temp_c": {"type": "number", "minimum": 20.0, "maximum": 120.0},
                    "sensing": {
                        "type": "object",
                        "required": ["thermal", "volatile_proxy", "load_trend"],
                        "properties": {
                            "thermal": {"type": "boolean"},
                            "volatile_proxy": {"type": "boolean"},
                            "load_trend": {"type": "boolean"},
                        },
                    },
                },
            },
        },
    },
}


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(CFG.read_text(encoding="utf-8"))

    validator = Draft202012Validator(SCHEMA)
    errs = sorted(validator.iter_errors(data), key=lambda e: e.path)

    cross_errors: list[str] = []
    for name, v in data.get("variants", {}).items():
        if list(v.get("phases", [])) != ["entry", "translate", "resurface"]:
            cross_errors.append(f"{name}: phases must be [entry, translate, resurface]")
        if float(v.get("collapse_risk_abort_threshold", 0.0)) <= float(v.get("disturbance_index_cap", 1.0)):
            cross_errors.append(f"{name}: collapse_risk_abort_threshold must be > disturbance_index_cap")

    passed = not errs and not cross_errors

    csv_path = REPORT_DIR / "regolith_variant_schema_validation.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["check", "message", "pass"])
        w.writeheader()
        if not errs and not cross_errors:
            w.writerow({"check": "schema_and_cross_rules", "message": "all checks passed", "pass": True})
        else:
            for e in errs:
                w.writerow({"check": "schema", "message": f"{list(e.path)}: {e.message}", "pass": False})
            for ce in cross_errors:
                w.writerow({"check": "cross_rule", "message": ce, "pass": False})

    md_path = REPORT_DIR / "regolith_variant_schema_validation.md"
    lines = [
        "# Regolith Variant Schema Validation",
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
