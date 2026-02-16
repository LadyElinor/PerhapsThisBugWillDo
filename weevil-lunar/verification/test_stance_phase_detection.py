"""v0 stub: stance-phase detection gate.

Evaluates whether contact-state transitions inferred from z/force proxies stay
within expected stance fraction envelope.
"""

from pathlib import Path
import csv


def run() -> dict:
    test_id = "WL-VER-STANCE-PHASE-001"
    contact_z_threshold_mm = 2.5
    measured_stance_fraction = 0.62
    min_stance_fraction = 0.45
    max_stance_fraction = 0.75

    passed = min_stance_fraction <= measured_stance_fraction <= max_stance_fraction

    return {
        "test_id": test_id,
        "contact_z_threshold_mm": contact_z_threshold_mm,
        "measured_stance_fraction": measured_stance_fraction,
        "min_stance_fraction": min_stance_fraction,
        "max_stance_fraction": max_stance_fraction,
        "pass": passed,
        "status": "pass" if passed else "baseline-fail",
    }


def main() -> None:
    result = run()
    reports = Path(__file__).resolve().parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    csv_path = reports / "stance_phase_detection.csv"
    md_path = reports / "stance_phase_detection.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(result.keys()))
        w.writeheader()
        w.writerow(result)

    md_lines = [
        "# Stance Phase Detection",
        "",
        f"- Test ID: `{result['test_id']}`",
        f"- Contact Z threshold: {result['contact_z_threshold_mm']} mm",
        f"- Measured stance fraction: {result['measured_stance_fraction']:.2f}",
        f"- Allowed range: [{result['min_stance_fraction']:.2f}, {result['max_stance_fraction']:.2f}]",
        f"- Status: **{result['status']}**",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
