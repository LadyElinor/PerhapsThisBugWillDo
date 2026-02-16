#!/usr/bin/env python3
"""Power + comms profile validation harness (v0.1 placeholders)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProfileRun:
    name: str
    mobility_wh: float
    thermal_survival_wh: float
    available_wh: float
    telemetry_loss_pct: float
    autonomous_continue_ok: bool


def evaluate(r: ProfileRun) -> bool:
    reserve_ok = (r.mobility_wh + r.thermal_survival_wh) <= r.available_wh
    comms_ok = r.telemetry_loss_pct <= 1.0 and r.autonomous_continue_ok
    return reserve_ok and comms_ok


def main() -> None:
    runs = [
        ProfileRun("nominal_day", 320, 60, 500, 0.2, True),
        ProfileRun("steep_slope", 360, 70, 520, 0.5, True),
        ProfileRun("dropout_window", 300, 80, 500, 0.9, True),
    ]

    out = []
    passes = 0
    for r in runs:
        ok = evaluate(r)
        passes += int(ok)
        out.append(
            {
                "name": r.name,
                "mobility_wh": r.mobility_wh,
                "thermal_survival_wh": r.thermal_survival_wh,
                "available_wh": r.available_wh,
                "telemetry_loss_pct": r.telemetry_loss_pct,
                "autonomous_continue_ok": r.autonomous_continue_ok,
                "pass": ok,
            }
        )

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "power_comms_profile.csv"
    md_path = report_dir / "power_comms_profile.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    status = "pass" if passes == len(out) else "fail"
    md = [
        "# Power + Comms Profile Test (v0.1)",
        "",
        "Model-based placeholder pending full mission hardware profile.",
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
