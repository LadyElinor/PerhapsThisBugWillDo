#!/usr/bin/env python3
"""Autonomy health-aware planning harness (v0.1 placeholders)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HealthScenario:
    name: str
    torque_margin: float
    thermal_margin: float
    friction_index: float
    expected_mode: str


def decide_mode(torque_margin: float, thermal_margin: float, friction_index: float) -> str:
    if torque_margin < 0.15 or thermal_margin < 0.15:
        return "recovery"
    if friction_index > 0.75:
        return "steep_slope"
    return "nominal"


def main() -> None:
    cases = [
        HealthScenario("healthy_nominal", 0.45, 0.50, 0.30, "nominal"),
        HealthScenario("high_friction_guard", 0.35, 0.40, 0.82, "steep_slope"),
        HealthScenario("low_torque_margin", 0.10, 0.35, 0.40, "recovery"),
        HealthScenario("low_thermal_margin", 0.28, 0.10, 0.35, "recovery"),
    ]

    out = []
    passes = 0
    for c in cases:
        actual = decide_mode(c.torque_margin, c.thermal_margin, c.friction_index)
        ok = actual == c.expected_mode
        passes += int(ok)
        out.append(
            {
                "name": c.name,
                "torque_margin": c.torque_margin,
                "thermal_margin": c.thermal_margin,
                "friction_index": c.friction_index,
                "expected_mode": c.expected_mode,
                "actual_mode": actual,
                "pass": ok,
            }
        )

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "autonomy_health_planner.csv"
    md_path = report_dir / "autonomy_health_planner.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    status = "pass" if passes == len(out) else "fail"
    md = [
        "# Autonomy Health Planner Test (v0.1)",
        "",
        f"- total: {len(out)}",
        f"- passed: {passes}",
        f"- status: **{status.upper()}**",
    ]
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
