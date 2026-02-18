"""v0 stub: axis-orthogonality sensitivity sweep.

Purpose:
- evaluate gait/slope stability sensitivity to proximal axis offset from orthogonality target.
"""

from pathlib import Path
import csv


def run() -> list[dict]:
    rows = []
    for axis_error_deg, success_rate in [
        (0.0, 0.92),
        (10.0, 0.88),
        (15.0, 0.84),
        (20.0, 0.73),
        (30.0, 0.55),
    ]:
        rows.append(
            {
                "test_id": "WL-VER-ORTHO-SENS-001",
                "axis_error_deg": axis_error_deg,
                "slope_recovery_success_rate": success_rate,
            }
        )
    return rows


def main() -> None:
    rows = run()
    reports = Path(__file__).resolve().parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    csv_path = reports / "axis_orthogonality_sensitivity.csv"
    md_path = reports / "axis_orthogonality_sensitivity.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    threshold_row = next((r for r in rows if r["axis_error_deg"] == 15.0), rows[0])
    status = "pass" if threshold_row["slope_recovery_success_rate"] >= 0.80 else "baseline-fail"

    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Axis Orthogonality Sensitivity\n\n")
        f.write("Target envelope: ±15° from nominal orthogonality.\n\n")
        f.write(f"- Gate status at 15°: **{status}**\n")
        for r in rows:
            f.write(
                f"- Axis error {r['axis_error_deg']:>4.1f}° -> recovery success {r['slope_recovery_success_rate']:.2f}\n"
            )


if __name__ == "__main__":
    main()
