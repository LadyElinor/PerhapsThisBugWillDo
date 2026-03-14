#!/usr/bin/env python3
"""Regolith burrow concept profile checks (v0.1)."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml


CFG_PATH = Path("configs/regolith_burrow_variants_2026-03-14.yaml")


def evaluate_variant(v: dict) -> tuple[bool, dict[str, bool]]:
    checks = {
        "leading_profile_ok": str(v.get("leading_profile", "")) in {"wedge_shovel", "wedge", "shovel"},
        "propulsion_mode_ok": str(v.get("propulsion_mode", "")) == "rotational_coupled_translation",
        "phase_sequence_ok": list(v.get("phases", [])) == ["entry", "translate", "resurface"],
        "depth_budget_ok": 0 < float(v.get("max_target_depth_m", 0.0)) <= 1.0,
        "disturbance_cap_ok": 0.0 < float(v.get("disturbance_index_cap", 0.0)) < 1.0,
        "collapse_abort_ok": float(v.get("collapse_risk_abort_threshold", 0.0)) > float(v.get("disturbance_index_cap", 1.0)),
        "resurfacing_margin_ok": float(v.get("resurfacing_margin_min", 0.0)) >= 1.0,
        "energy_reserve_ok": 0.05 <= float(v.get("min_energy_reserve_fraction", 0.0)) <= 0.5,
        "thermal_cap_ok": 20.0 <= float(v.get("max_component_temp_c", 0.0)) <= 120.0,
        "sensing_stack_ok": bool(v.get("sensing", {}).get("thermal"))
        and bool(v.get("sensing", {}).get("volatile_proxy"))
        and bool(v.get("sensing", {}).get("load_trend")),
    }
    return all(checks.values()), checks


def main() -> None:
    assert CFG_PATH.exists(), f"missing config: {CFG_PATH}"
    data = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))
    assert "variants" in data and isinstance(data["variants"], dict)

    rows = []
    for name, variant in data["variants"].items():
        ok, checks = evaluate_variant(variant)
        row = {
            "variant": name,
            "leading_profile": variant.get("leading_profile"),
            "propulsion_mode": variant.get("propulsion_mode"),
            "phases": "|".join(variant.get("phases", [])),
            "max_target_depth_m": variant.get("max_target_depth_m"),
            "disturbance_index_cap": variant.get("disturbance_index_cap"),
            "collapse_risk_abort_threshold": variant.get("collapse_risk_abort_threshold"),
            "resurfacing_margin_min": variant.get("resurfacing_margin_min"),
            "min_energy_reserve_fraction": variant.get("min_energy_reserve_fraction"),
            "max_component_temp_c": variant.get("max_component_temp_c"),
            **checks,
            "pass": ok,
        }
        rows.append(row)

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "regolith_burrow_profile.csv"
    md_path = report_dir / "regolith_burrow_profile.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    passed = sum(1 for r in rows if r["pass"])
    status = "pass" if passed == total else "fail"

    lines = [
        "# Regolith Burrow Profile Test",
        "",
        "Concept-level safety and structure checks for Crover-like lunar subsurface variant configs.",
        "",
        f"- total: {total}",
        f"- passed: {passed}",
        f"- status: **{status.upper()}**",
        "",
        "| variant | phases_ok | disturbance_ok | collapse_abort_ok | resurfacing_ok | pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['variant']} | {int(bool(r['phase_sequence_ok']))} | {int(bool(r['disturbance_cap_ok']))} "
            f"| {int(bool(r['collapse_abort_ok']))} | {int(bool(r['resurfacing_margin_ok']))} | {int(bool(r['pass']))} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
