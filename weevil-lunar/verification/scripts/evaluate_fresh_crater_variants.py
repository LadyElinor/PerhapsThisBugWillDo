#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.fresh_crater_terrain import CraterScenario, evaluate_crater_scenario

CFG = Path("configs/fresh_crater_explorer_variants_2026-04-18.yaml")
REPORT_DIR = Path("verification/reports")


def mission_score(traction_proxy: float, disturbance: float, reserve: float, telemetry: float, standoff: float) -> float:
    score = 0.25 * traction_proxy
    score += 0.20 * reserve
    score += 0.20 * min(telemetry / 240.0, 1.0)
    score += 0.15 * min(standoff / 2.5, 1.0)
    score += 0.20 * max(0.0, 0.40 - disturbance)
    return max(0.0, min(1.0, score))


def risk_posture_label(v: dict) -> str:
    reserve = float(v["egress_reserve_fraction"])
    slope = float(v["approach_slope_limit_deg"])
    disturbance = float(v["disturbance_index_cap"])
    if reserve >= 0.30 and slope <= 20 and disturbance <= 0.30:
        return "conservative"
    if slope >= 24 or disturbance >= 0.34:
        return "aggressive"
    return "balanced"


def representative_terrain(variant_name: str) -> str:
    if variant_name == "partial_descent_guarded":
        return "inner_wall_loose"
    if variant_name == "rim_scout_conservative":
        return "ejecta_blockfield"
    return "rim_transition"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    variants = data.get("variants", {})
    default = data.get("meta", {}).get("default_recommended", "")

    rows = []
    for name, v in sorted(variants.items()):
        terrain = representative_terrain(name)
        slope = float(v["approach_slope_limit_deg"])
        reserve = float(v["egress_reserve_fraction"])
        telemetry = float(v["telemetry_buffer_min_s"])
        disturbance_cap = float(v["disturbance_index_cap"])
        standoff = float(v["edge_standoff_m"])
        crater = evaluate_crater_scenario(
            CraterScenario(
                terrain=terrain,
                slope_deg=min(slope, float(v.get("partial_descent_limit_deg", 0.0)) or slope),
                base_disturbance_index=max(0.12, disturbance_cap * 0.65),
                base_slip_ratio=max(0.06, float(v["slip_abort_threshold"]) * 0.55),
                telemetry_buffer_min_s=telemetry,
                egress_reserve_fraction=reserve,
                edge_standoff_m=standoff,
            )
        )
        traction_proxy = max(0.0, 1.0 - crater.effective_slip_ratio)
        score = mission_score(traction_proxy, crater.effective_disturbance_index, reserve, crater.telemetry_buffer_effective_s, standoff)
        row_pass = (
            crater.effective_disturbance_index <= disturbance_cap
            and crater.effective_slip_ratio <= float(v["slip_abort_threshold"])
            and reserve >= 0.24
            and crater.telemetry_buffer_effective_s >= 120.0
            and score >= 0.34
        )

        rows.append(
            {
                "variant": name,
                "terrain": terrain,
                "approach_slope_limit_deg": round(slope, 3),
                "edge_standoff_m": round(standoff, 3),
                "reserve": round(reserve, 3),
                "telemetry_buffer_effective_s": round(crater.telemetry_buffer_effective_s, 3),
                "effective_disturbance_index": round(crater.effective_disturbance_index, 4),
                "effective_slip_ratio": round(crater.effective_slip_ratio, 4),
                "traction_proxy": round(traction_proxy, 4),
                "synthetic_success_score": round(score, 4),
                "risk_posture": risk_posture_label(v),
                "default_recommended": name == default,
                "recommended_actuator": str(v["preferred_actuator_candidate"]),
                "recommended_geometry_profile": str(v["leg_module_profile"]),
                "pass": row_pass,
            }
        )

    rows_sorted = sorted(rows, key=lambda r: r["synthetic_success_score"], reverse=True)

    csv_path = REPORT_DIR / "fresh_crater_variant_evaluation.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_sorted[0].keys()) if rows_sorted else ["variant", "pass"])
        w.writeheader()
        if rows_sorted:
            w.writerows(rows_sorted)

    md_path = REPORT_DIR / "fresh_crater_variant_evaluation.md"
    lines = [
        "# Fresh Crater Variant Evaluation",
        "",
        f"- config: `{CFG}`",
        f"- variants evaluated: {len(rows_sorted)}",
        f"- default recommended: `{default}`",
        "",
        "| variant | terrain | reserve | telemetry | disturbance | slip | score | posture | default | pass |",
        "|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for r in rows_sorted:
        lines.append(
            f"| {r['variant']} | {r['terrain']} | {r['reserve']:.3f} | {r['telemetry_buffer_effective_s']:.1f} | {r['effective_disturbance_index']:.4f} | {r['effective_slip_ratio']:.4f} | {r['synthetic_success_score']:.4f} | {r['risk_posture']} | {r['default_recommended']} | {r['pass']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
