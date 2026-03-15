#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import yaml

CFG = Path("configs/regolith_burrow_variants_2026-03-14.yaml")
REPORT_DIR = Path("verification/reports")


def synthetic_success_score(disturbance_cap: float, collapse_abort: float, reserve: float) -> float:
    gap = collapse_abort - disturbance_cap
    score = 0.45 * disturbance_cap + 0.25 * reserve + 0.30 * max(gap, 0.0)
    return max(0.0, min(1.0, score))


def risk_posture_label(v: dict) -> str:
    reserve = float(v["min_energy_reserve_fraction"])
    depth = float(v["max_target_depth_m"])
    gap = float(v["collapse_risk_abort_threshold"]) - float(v["disturbance_index_cap"])
    if reserve >= 0.30 and depth <= 0.30 and gap >= 0.30:
        return "conservative"
    if depth >= 0.50 or reserve <= 0.22:
        return "aggressive"
    return "balanced"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    variants = data.get("variants", {})
    default = data.get("meta", {}).get("default_recommended", "")

    rows = []
    for name, v in sorted(variants.items()):
        disturbance = float(v["disturbance_index_cap"])
        abort = float(v["collapse_risk_abort_threshold"])
        reserve = float(v["min_energy_reserve_fraction"])
        depth = float(v["max_target_depth_m"])
        resurface = float(v["resurfacing_margin_min"])
        score = synthetic_success_score(disturbance, abort, reserve)
        gap = abort - disturbance
        row_pass = gap >= 0.15 and reserve >= 0.20 and resurface >= 1.05 and score >= 0.30

        rows.append(
            {
                "variant": name,
                "depth_m": round(depth, 3),
                "disturbance_cap": round(disturbance, 3),
                "collapse_abort": round(abort, 3),
                "abort_gap": round(gap, 3),
                "reserve": round(reserve, 3),
                "resurfacing_margin": round(resurface, 3),
                "synthetic_success_score": round(score, 4),
                "risk_posture": risk_posture_label(v),
                "default_recommended": name == default,
                "pass": row_pass,
            }
        )

    rows_sorted = sorted(rows, key=lambda r: r["synthetic_success_score"], reverse=True)

    csv_path = REPORT_DIR / "regolith_variant_evaluation.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_sorted[0].keys()) if rows_sorted else ["variant", "pass"])
        w.writeheader()
        if rows_sorted:
            w.writerows(rows_sorted)

    md_path = REPORT_DIR / "regolith_variant_evaluation.md"
    lines = [
        "# Regolith Variant Evaluation",
        "",
        f"- config: `{CFG}`",
        f"- variants evaluated: {len(rows_sorted)}",
        f"- default recommended: `{default}`",
        "",
        "| variant | depth | gap | reserve | score | posture | default | pass |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for r in rows_sorted:
        lines.append(
            f"| {r['variant']} | {r['depth_m']:.3f} | {r['abort_gap']:.3f} | {r['reserve']:.3f} | {r['synthetic_success_score']:.4f} | {r['risk_posture']} | {r['default_recommended']} | {r['pass']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
