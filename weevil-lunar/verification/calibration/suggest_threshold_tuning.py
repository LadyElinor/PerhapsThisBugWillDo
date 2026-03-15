#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPORT_DIR = Path("verification/reports")
ERROR_CSV = REPORT_DIR / "bench_model_error.csv"
FIT_CSV = REPORT_DIR / "bench_model_fit.csv"


def _f(v: str) -> float:
    return float((v or "0").strip())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--max-force-mae", type=float, default=1.2)
    p.add_argument("--max-slip-mae", type=float, default=0.5)
    p.add_argument("--max-stiffness-mae", type=float, default=0.40)
    p.add_argument("--max-force-ci95", type=float, default=2.0)
    p.add_argument("--max-slip-ci95", type=float, default=1.0)
    p.add_argument("--max-stiffness-ci95", type=float, default=0.65)
    p.add_argument("--safety-margin", type=float, default=1.1)
    args = p.parse_args()

    if not ERROR_CSV.exists() or not FIT_CSV.exists():
        raise FileNotFoundError("run bench calibration fit/check first")

    with ERROR_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    failed = [r for r in rows if str(r.get("pass", "")).lower() not in {"true", "1"}]

    out_csv = REPORT_DIR / "bench_model_threshold_tuning.csv"
    out_md = REPORT_DIR / "bench_model_threshold_tuning.md"

    fieldnames = [
        "group_key",
        "metric",
        "current_threshold",
        "observed",
        "suggested_threshold",
        "rationale",
        "pass",
    ]

    suggestions = []
    for r in failed:
        g = r.get("group_key", "")
        checks = [
            ("force_mae_N", args.max_force_mae),
            ("slip_mae_mm", args.max_slip_mae),
            ("stiffness_mae_N_per_mm", args.max_stiffness_mae),
            ("force_ci95_N", args.max_force_ci95),
            ("slip_ci95_mm", args.max_slip_ci95),
            ("stiffness_ci95_N_per_mm", args.max_stiffness_ci95),
        ]
        for metric, thr in checks:
            obs = _f(r.get(metric))
            metric_pass = obs <= thr
            if metric_pass:
                continue
            suggested = round(obs * args.safety_margin, 6)
            suggestions.append(
                {
                    "group_key": g,
                    "metric": metric,
                    "current_threshold": thr,
                    "observed": round(obs, 6),
                    "suggested_threshold": suggested,
                    "rationale": f"observed {obs:.6f} exceeds threshold {thr:.6f}; add {args.safety_margin:.2f}x buffer",
                    "pass": False,
                }
            )

    if not suggestions:
        suggestions.append(
            {
                "group_key": "-",
                "metric": "-",
                "current_threshold": "-",
                "observed": "-",
                "suggested_threshold": "-",
                "rationale": "No failed groups; no threshold tuning needed.",
                "pass": True,
            }
        )

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(suggestions)

    lines = [
        "# Bench Model Threshold Tuning Suggestions",
        "",
        f"- failed groups: {len(failed)}",
        f"- safety margin: {args.safety_margin}",
        "",
        "| group | metric | threshold | observed | suggested | rationale |",
        "|---|---|---:|---:|---:|---|",
    ]
    for s in suggestions:
        lines.append(
            f"| {s['group_key']} | {s['metric']} | {s['current_threshold']} | {s['observed']} | {s['suggested_threshold']} | {s['rationale']} |"
        )

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
