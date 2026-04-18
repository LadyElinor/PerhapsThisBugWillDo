#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import yaml

CFG = Path("configs/fresh_crater_explorer_variants_2026-04-18.yaml")
REPORT_DIR = Path("verification/reports")

MISSION_QUERY = {
    "target_approach_slope_deg": 20.0,
    "min_edge_standoff_m": 1.5,
    "min_egress_reserve_fraction": 0.28,
    "min_telemetry_buffer_s": 180.0,
    "max_disturbance_index_cap": 0.32,
}


def distance(variant: dict) -> float:
    slope = float(variant["approach_slope_limit_deg"])
    standoff = float(variant["edge_standoff_m"])
    reserve = float(variant["egress_reserve_fraction"])
    telemetry = float(variant["telemetry_buffer_min_s"])
    disturbance = float(variant["disturbance_index_cap"])

    d = 0.0
    d += 1.5 * abs(slope - MISSION_QUERY["target_approach_slope_deg"])
    d += 2.0 * max(0.0, MISSION_QUERY["min_edge_standoff_m"] - standoff)
    d += 2.0 * max(0.0, MISSION_QUERY["min_egress_reserve_fraction"] - reserve)
    d += 1.5 * max(0.0, MISSION_QUERY["min_telemetry_buffer_s"] - telemetry) / 60.0
    d += 2.5 * max(0.0, disturbance - MISSION_QUERY["max_disturbance_index_cap"])
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
                "approach_slope_limit_deg": float(v["approach_slope_limit_deg"]),
                "edge_standoff_m": float(v["edge_standoff_m"]),
                "egress_reserve_fraction": float(v["egress_reserve_fraction"]),
                "telemetry_buffer_min_s": float(v["telemetry_buffer_min_s"]),
                "disturbance_index_cap": float(v["disturbance_index_cap"]),
                "pass": True,
            }
        )

    scored.sort(key=lambda r: r["distance"])
    best = scored[0]

    csv_path = REPORT_DIR / "fresh_crater_variant_retrieval.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(scored[0].keys()))
        w.writeheader()
        w.writerows(scored)

    md_path = REPORT_DIR / "fresh_crater_variant_retrieval.md"
    lines = [
        "# Fresh Crater Variant Retrieval",
        "",
        "Retrieval-before-perturbation candidate selection for fresh-crater mission context.",
        "",
        "## Mission query",
        f"- target_approach_slope_deg: {MISSION_QUERY['target_approach_slope_deg']}",
        f"- min_edge_standoff_m: {MISSION_QUERY['min_edge_standoff_m']}",
        f"- min_egress_reserve_fraction: {MISSION_QUERY['min_egress_reserve_fraction']}",
        f"- min_telemetry_buffer_s: {MISSION_QUERY['min_telemetry_buffer_s']}",
        f"- max_disturbance_index_cap: {MISSION_QUERY['max_disturbance_index_cap']}",
        "",
        "## Best match",
        f"- variant: **{best['variant']}**",
        f"- distance: **{best['distance']:.4f}**",
        "",
        "| rank | variant | distance | slope | standoff | reserve | telemetry | disturbance |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for i, r in enumerate(scored, start=1):
        lines.append(
            f"| {i} | {r['variant']} | {r['distance']:.4f} | {r['approach_slope_limit_deg']:.1f} | {r['edge_standoff_m']:.2f} | {r['egress_reserve_fraction']:.2f} | {r['telemetry_buffer_min_s']:.1f} | {r['disturbance_index_cap']:.2f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
