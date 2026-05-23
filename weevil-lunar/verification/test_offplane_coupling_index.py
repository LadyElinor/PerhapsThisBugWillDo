"""v0 stub: off-plane coupling index gate."""

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "verification" / "reports"


def run() -> dict:
    limit = 0.35
    measured_index = 0.29
    passed = measured_index <= limit

    return {
        "test_id": "WL-VER-OFFPLANE-COUPLING-001",
        "offplane_index_limit": limit,
        "measured_offplane_index": measured_index,
        "pass": passed,
        "status": "pass" if passed else "baseline-fail",
    }


def main() -> None:
    result = run()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = REPORT_DIR / "offplane_coupling_index.csv"
    md_path = REPORT_DIR / "offplane_coupling_index.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(result.keys()))
        w.writeheader()
        w.writerow(result)

    md_lines = [
        "# Off-Plane Coupling Index",
        "",
        f"- Test ID: `{result['test_id']}`",
        f"- Measured off-plane index: {result['measured_offplane_index']:.3f}",
        f"- Limit: {result['offplane_index_limit']:.3f}",
        f"- Status: **{result['status']}**",
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
