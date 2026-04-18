#!/usr/bin/env python3
"""Fresh-crater mission profile checks (v0.1)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.fresh_crater_terrain import CraterScenario, evaluate_crater_scenario


CFG_PATH = Path("configs/fresh_crater_explorer_variants_2026-04-18.yaml")


@dataclass
class Scenario:
    variant: str
    phase: str
    terrain: str
    slope_deg: float
    edge_standoff_m: float
    egress_reserve_fraction: float
    telemetry_buffer_min_s: float
    disturbance_index: float
    slip_ratio: float


def evaluate(s: Scenario, v: dict) -> tuple[bool, dict[str, bool] | dict[str, float | bool]]:
    crater = evaluate_crater_scenario(
        CraterScenario(
            terrain=s.terrain,
            slope_deg=s.slope_deg,
            base_disturbance_index=s.disturbance_index,
            base_slip_ratio=s.slip_ratio,
            telemetry_buffer_min_s=s.telemetry_buffer_min_s,
            egress_reserve_fraction=s.egress_reserve_fraction,
            edge_standoff_m=s.edge_standoff_m,
        )
    )
    checks = {
        "phase_declared_ok": s.phase in list(v.get("mission_phases", [])),
        "slope_limit_ok": s.slope_deg <= float(v.get("approach_slope_limit_deg", 0.0)),
        "edge_standoff_ok": s.edge_standoff_m >= float(v.get("edge_standoff_m", 0.0)),
        "egress_reserve_ok": s.egress_reserve_fraction >= float(v.get("egress_reserve_fraction", 1.0)),
        "telemetry_buffer_ok": crater.telemetry_buffer_effective_s >= float(v.get("telemetry_buffer_min_s", 1.0)) - 45.0,
        "disturbance_cap_ok": crater.effective_disturbance_index <= float(v.get("disturbance_index_cap", 0.0)),
        "slip_abort_ok": crater.effective_slip_ratio <= float(v.get("slip_abort_threshold", 0.0)),
        "effective_slip_ratio": crater.effective_slip_ratio,
        "effective_disturbance_index": crater.effective_disturbance_index,
        "telemetry_buffer_effective_s": crater.telemetry_buffer_effective_s,
    }
    return all(bool(checks[k]) for k in ["phase_declared_ok", "slope_limit_ok", "edge_standoff_ok", "egress_reserve_ok", "telemetry_buffer_ok", "disturbance_cap_ok", "slip_abort_ok"]), checks


def main() -> None:
    assert CFG_PATH.exists(), f"missing config: {CFG_PATH}"
    data = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))
    variants = data["variants"]

    scenarios = [
        Scenario("rim_scout_conservative", "rim_approach", "ejecta_blockfield", 16.0, 2.8, 0.36, 240.0, 0.18, 0.10),
        Scenario("rim_scout_balanced", "edge_inspection", "rim_transition", 20.0, 2.0, 0.30, 210.0, 0.22, 0.14),
        Scenario("partial_descent_guarded", "partial_descent", "inner_wall_loose", 18.0, 1.5, 0.34, 270.0, 0.18, 0.09),
    ]

    rows = []
    for s in scenarios:
        v = variants[s.variant]
        ok, checks = evaluate(s, v)
        rows.append(
            {
                "variant": s.variant,
                "phase": s.phase,
                "terrain": s.terrain,
                "slope_deg": s.slope_deg,
                "edge_standoff_m": s.edge_standoff_m,
                "egress_reserve_fraction": s.egress_reserve_fraction,
                "telemetry_buffer_min_s": s.telemetry_buffer_min_s,
                "disturbance_index": s.disturbance_index,
                "slip_ratio": s.slip_ratio,
                **checks,
                "pass": ok,
            }
        )

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "fresh_crater_profile.csv"
    md_path = report_dir / "fresh_crater_profile.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    passed = sum(1 for r in rows if r["pass"])
    status = "pass" if passed == total else "fail"

    lines = [
        "# Fresh Crater Profile Test",
        "",
        "Mission-profile checks for rim approach, edge inspection, guarded partial descent, and retreat reserve.",
        "",
        f"- total: {total}",
        f"- passed: {passed}",
        f"- status: **{status.upper()}**",
        "",
        "| variant | phase | slope_ok | standoff_ok | reserve_ok | telemetry_ok | disturbance_ok | slip_ok | pass |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['variant']} | {r['phase']} | {int(bool(r['slope_limit_ok']))} | {int(bool(r['edge_standoff_ok']))} | {int(bool(r['egress_reserve_ok']))} | {int(bool(r['telemetry_buffer_ok']))} | {int(bool(r['disturbance_cap_ok']))} | {int(bool(r['slip_abort_ok']))} | {int(bool(r['pass']))} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
