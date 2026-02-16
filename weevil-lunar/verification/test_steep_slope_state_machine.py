#!/usr/bin/env python3
"""Steep-slope state machine validation harness (v0.1)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Scenario:
    name: str
    slope_deg: float
    anchored: bool
    margin_down: float
    margin_lat: float


def push_off_allowed(slope_deg: float, anchored: bool, margin_down: float, margin_lat: float) -> bool:
    if slope_deg > 25.0 and not anchored:
        return False
    if margin_down < 1.05:
        return False
    if margin_lat < 1.20:
        return False
    return True


def main() -> None:
    scenarios = [
        Scenario("nominal_flat", 5.0, False, 1.30, 1.40),
        Scenario("steep_unanchored", 32.0, False, 1.20, 1.30),
        Scenario("steep_anchored_good", 32.0, True, 1.10, 1.25),
        Scenario("steep_anchored_bad_margin", 32.0, True, 0.98, 1.30),
        Scenario("extreme_anchored_good", 45.0, True, 1.08, 1.22),
    ]

    expected = {
        "nominal_flat": True,
        "steep_unanchored": False,
        "steep_anchored_good": True,
        "steep_anchored_bad_margin": False,
        "extreme_anchored_good": True,
    }

    out_rows = []
    passes = 0
    for s in scenarios:
        allowed = push_off_allowed(s.slope_deg, s.anchored, s.margin_down, s.margin_lat)
        ok = allowed == expected[s.name]
        passes += int(ok)
        out_rows.append(
            {
                "scenario": s.name,
                "slope_deg": s.slope_deg,
                "anchored": s.anchored,
                "margin_down": s.margin_down,
                "margin_lat": s.margin_lat,
                "expected_push_off": expected[s.name],
                "actual_push_off": allowed,
                "pass": ok,
            }
        )

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "steep_slope_state_machine.csv"
    md_path = report_dir / "steep_slope_state_machine.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    summary = "pass" if passes == len(scenarios) else "fail"
    md_lines = [
        "# Steep Slope State Machine Test",
        "",
        f"- total: {len(scenarios)}",
        f"- passed: {passes}",
        f"- status: **{summary.upper()}**",
        "",
        "| scenario | expected | actual | pass |",
        "|---|---:|---:|---:|",
    ]
    for r in out_rows:
        md_lines.append(f"| {r['scenario']} | {int(r['expected_push_off'])} | {int(r['actual_push_off'])} | {int(r['pass'])} |")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={summary}")


if __name__ == "__main__":
    main()
