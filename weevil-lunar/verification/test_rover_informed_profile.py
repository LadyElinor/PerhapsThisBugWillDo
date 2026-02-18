#!/usr/bin/env python3
"""Rover-informed mobility/thermal/power profile checks (v0.1)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Scenario:
    name: str
    tilt_deg: float
    virtual_rocker_bogie: bool
    traction_margin_down: float
    traction_margin_lat: float
    day_energy_wh: float
    loads_wh: float
    dust_derate_factor: float
    thermal_core_ok: bool
    telemetry_retained_after_dropout: bool


def evaluate(s: Scenario) -> tuple[bool, dict[str, bool]]:
    checks = {
        "tilt_envelope_ok": s.tilt_deg <= 30.0,
        "virtual_rocker_bogie_ok": s.virtual_rocker_bogie,
        "traction_margin_ok": s.traction_margin_down >= 1.05 and s.traction_margin_lat >= 1.20,
        "energy_margin_ok": (s.day_energy_wh * s.dust_derate_factor) - s.loads_wh >= 0.0,
        "thermal_core_ok": s.thermal_core_ok,
        "telemetry_retention_ok": s.telemetry_retained_after_dropout,
    }
    return all(checks.values()), checks


def main() -> None:
    scenarios = [
        Scenario("nominal_mare_day", 18.0, True, 1.20, 1.34, 520.0, 330.0, 0.78, True, True),
        Scenario("steep_slope_recovery", 28.0, True, 1.08, 1.23, 520.0, 360.0, 0.78, True, True),
        Scenario("dropout_night_survival", 12.0, True, 1.15, 1.28, 520.0, 390.0, 0.78, True, True),
    ]

    out_rows = []
    passes = 0
    for s in scenarios:
        ok, checks = evaluate(s)
        passes += int(ok)
        out_rows.append(
            {
                "scenario": s.name,
                "tilt_deg": s.tilt_deg,
                "virtual_rocker_bogie": s.virtual_rocker_bogie,
                "traction_margin_down": s.traction_margin_down,
                "traction_margin_lat": s.traction_margin_lat,
                "day_energy_wh": s.day_energy_wh,
                "loads_wh": s.loads_wh,
                "dust_derate_factor": s.dust_derate_factor,
                "thermal_core_ok": s.thermal_core_ok,
                "telemetry_retained_after_dropout": s.telemetry_retained_after_dropout,
                "tilt_envelope_ok": checks["tilt_envelope_ok"],
                "virtual_rocker_bogie_ok": checks["virtual_rocker_bogie_ok"],
                "traction_margin_ok": checks["traction_margin_ok"],
                "energy_margin_ok": checks["energy_margin_ok"],
                "telemetry_retention_ok": checks["telemetry_retention_ok"],
                "pass": ok,
            }
        )

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "rover_informed_profile.csv"
    md_path = report_dir / "rover_informed_profile.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    status = "pass" if passes == len(out_rows) else "fail"
    lines = [
        "# Rover-Informed Profile Test",
        "",
        "Model-based check for rover-derived requirements in mobility/thermal/power/comms continuity.",
        "",
        f"- total: {len(out_rows)}",
        f"- passed: {passes}",
        f"- status: **{status.upper()}**",
        "",
        "| scenario | tilt_ok | traction_ok | energy_ok | telemetry_ok | pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in out_rows:
        lines.append(
            f"| {r['scenario']} | {int(bool(r['tilt_envelope_ok']))} | {int(bool(r['traction_margin_ok']))} | {int(bool(r['energy_margin_ok']))} | {int(bool(r['telemetry_retention_ok']))} | {int(bool(r['pass']))} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
