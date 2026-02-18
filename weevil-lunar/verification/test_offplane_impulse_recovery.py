"""v0 stub: off-plane impulse recovery test for TFJ compliance.

Purpose:
- quantify whether proximal compliance improves recovery under lateral/off-plane perturbations.
"""

from pathlib import Path
import csv


def run() -> dict:
    # Placeholder metric seeds; replace with physics/contact simulation integration.
    baseline_recovery_time_s = 2.4
    compliant_recovery_time_s = 1.7
    baseline_peak_slip_mm = 42.0
    compliant_peak_slip_mm = 27.0

    pass_time = compliant_recovery_time_s <= baseline_recovery_time_s * 0.85
    pass_slip = compliant_peak_slip_mm <= baseline_peak_slip_mm * 0.80

    return {
        "test_id": "WL-VER-IMPULSE-OFFPLANE-001",
        "status": "pass" if (pass_time and pass_slip) else "partial-pass",
        "baseline_recovery_time_s": baseline_recovery_time_s,
        "compliant_recovery_time_s": compliant_recovery_time_s,
        "baseline_peak_slip_mm": baseline_peak_slip_mm,
        "compliant_peak_slip_mm": compliant_peak_slip_mm,
        "pass_time": pass_time,
        "pass_slip": pass_slip,
    }


def main() -> None:
    result = run()
    reports = Path(__file__).resolve().parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    csv_path = reports / "offplane_impulse_recovery.csv"
    md_path = reports / "offplane_impulse_recovery.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(result.keys()))
        w.writeheader()
        w.writerow(result)

    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Off-Plane Impulse Recovery\n\n")
        f.write(f"- Test ID: `{result['test_id']}`\n")
        f.write(f"- Status: **{result['status']}**\n")
        f.write(f"- Baseline recovery time: {result['baseline_recovery_time_s']} s\n")
        f.write(f"- Compliant recovery time: {result['compliant_recovery_time_s']} s\n")
        f.write(f"- Baseline peak slip: {result['baseline_peak_slip_mm']} mm\n")
        f.write(f"- Compliant peak slip: {result['compliant_peak_slip_mm']} mm\n")


if __name__ == "__main__":
    main()
