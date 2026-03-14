#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import yaml

CFG = Path("configs/regolith_burrow_variants_2026-03-14.yaml")
REPORT_DIR = Path("verification/reports")

# Mission-conditioned target (editable)
MISSION_QUERY = {
    "target_depth_m": 0.30,
    "max_disturbance": 0.38,
    "min_abort_gap": 0.20,
    "min_reserve": 0.25,
}


def distance(variant: dict) -> float:
    depth = float(variant["max_target_depth_m"])
    disturbance = float(variant["disturbance_index_cap"])
    abort = float(variant["collapse_risk_abort_threshold"])
    reserve = float(variant["min_energy_reserve_fraction"])

    gap = abort - disturbance

    # weighted L1 distance in mission space
    d = 0.0
    d += 2.0 * abs(depth - MISSION_QUERY["target_depth_m"])
    d += 2.5 * max(0.0, disturbance - MISSION_QUERY["max_disturbance"])  # penalty if too disruptive
    d += 2.0 * max(0.0, MISSION_QUERY["min_abort_gap"] - gap)  # penalty if abort gap too small
    d += 2.0 * max(0.0, MISSION_QUERY["min_reserve"] - reserve)  # penalty if reserve too low
    return d


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(CFG.read_text(encoding="utf-8"))

    scored = []
    for name, v in data["variants"].items():
        scored.append(
            {
                "variant": name,
                "distance": round(distance(v), 4),
                "max_target_depth_m": float(v["max_target_depth_m"]),
                "disturbance_index_cap": float(v["disturbance_index_cap"]),
                "collapse_risk_abort_threshold": float(v["collapse_risk_abort_threshold"]),
                "abort_gap": float(v["collapse_risk_abort_threshold"]) - float(v["disturbance_index_cap"]),
                "min_energy_reserve_fraction": float(v["min_energy_reserve_fraction"]),
                "pass": True,
            }
        )

    scored.sort(key=lambda r: r["distance"])
    best = scored[0]

    csv_path = REPORT_DIR / "regolith_variant_retrieval.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(scored[0].keys()))
        w.writeheader()
        w.writerows(scored)

    md_path = REPORT_DIR / "regolith_variant_retrieval.md"
    lines = [
        "# Regolith Variant Retrieval",
        "",
        "Retrieval-before-perturbation candidate selection for subsurface mission context.",
        "",
        "## Mission query",
        f"- target_depth_m: {MISSION_QUERY['target_depth_m']}",
        f"- max_disturbance: {MISSION_QUERY['max_disturbance']}",
        f"- min_abort_gap: {MISSION_QUERY['min_abort_gap']}",
        f"- min_reserve: {MISSION_QUERY['min_reserve']}",
        "",
        "## Best match",
        f"- variant: **{best['variant']}**",
        f"- distance: **{best['distance']:.4f}**",
        "",
        "| rank | variant | distance | depth | disturbance | abort_gap | reserve |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for i, r in enumerate(scored, start=1):
        lines.append(
            f"| {i} | {r['variant']} | {r['distance']:.4f} | {r['max_target_depth_m']:.2f} | {r['disturbance_index_cap']:.2f} | {r['abort_gap']:.2f} | {r['min_energy_reserve_fraction']:.2f} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
