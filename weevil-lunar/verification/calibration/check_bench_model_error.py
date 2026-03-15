#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REPORT_DIR = Path("verification/reports")
FIT_CSV = REPORT_DIR / "bench_model_fit.csv"
PARAMS_JSON = REPORT_DIR / "bench_model_params.json"


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
    args = p.parse_args()

    if not FIT_CSV.exists() or not PARAMS_JSON.exists():
        raise FileNotFoundError("run fit_bench_to_model.py first")

    with FIT_CSV.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    with PARAMS_JSON.open("r", encoding="utf-8") as f:
        params = json.load(f)

    out_rows = []
    overall_pass = True
    for r in rows:
        force_mae = _f(r.get("force_mae_N"))
        slip_mae = _f(r.get("slip_mae_mm"))
        stiff_mae = _f(r.get("stiffness_mae_N_per_mm"))
        force_ci95 = _f(r.get("force_ci95_N"))
        slip_ci95 = _f(r.get("slip_ci95_mm"))
        stiff_ci95 = _f(r.get("stiffness_ci95_N_per_mm"))
        n_samples = int(float(r.get("n_samples", "0")))

        row_pass = (
            n_samples >= 2
            and force_mae <= args.max_force_mae
            and slip_mae <= args.max_slip_mae
            and stiff_mae <= args.max_stiffness_mae
            and force_ci95 <= args.max_force_ci95
            and slip_ci95 <= args.max_slip_ci95
            and stiff_ci95 <= args.max_stiffness_ci95
        )
        overall_pass = overall_pass and row_pass
        out_rows.append(
            {
                "group_key": r.get("group_key", ""),
                "strategy_id": r.get("strategy_id", ""),
                "regolith_class": r.get("regolith_class", ""),
                "temperature_bucket": r.get("temperature_bucket", ""),
                "n_samples": n_samples,
                "force_mae_N": force_mae,
                "slip_mae_mm": slip_mae,
                "stiffness_mae_N_per_mm": stiff_mae,
                "force_ci95_N": force_ci95,
                "slip_ci95_mm": slip_ci95,
                "stiffness_ci95_N_per_mm": stiff_ci95,
                "pass": row_pass,
            }
        )

    out_csv = REPORT_DIR / "bench_model_error.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "group_key",
                "strategy_id",
                "regolith_class",
                "temperature_bucket",
                "n_samples",
                "force_mae_N",
                "slip_mae_mm",
                "stiffness_mae_N_per_mm",
                "force_ci95_N",
                "slip_ci95_mm",
                "stiffness_ci95_N_per_mm",
                "pass",
            ],
        )
        w.writeheader()
        w.writerows(out_rows)

    out_md = REPORT_DIR / "bench_model_error.md"
    lines = [
        "# Bench Model Error Check",
        "",
        f"- max force MAE (N): {args.max_force_mae}",
        f"- max slip MAE (mm): {args.max_slip_mae}",
        f"- max stiffness MAE (N/mm): {args.max_stiffness_mae}",
        f"- max force CI95 (N): {args.max_force_ci95}",
        f"- max slip CI95 (mm): {args.max_slip_ci95}",
        f"- max stiffness CI95 (N/mm): {args.max_stiffness_ci95}",
        f"- calibrated grouped models: {len(params.get('models', {}))}",
        f"- calibrated strategy fallbacks: {len(params.get('global_by_strategy', {}))}",
        f"- status: **{'PASS' if overall_pass else 'FAIL'}**",
        "",
        "| group | n | force MAE | slip MAE | stiffness MAE | force CI95 | slip CI95 | stiffness CI95 | pass |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in out_rows:
        lines.append(
            f"| {r['group_key']} | {r['n_samples']} | {r['force_mae_N']} | {r['slip_mae_mm']} | {r['stiffness_mae_N_per_mm']} | {r['force_ci95_N']} | {r['slip_ci95_mm']} | {r['stiffness_ci95_N_per_mm']} | {r['pass']} |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print(f"STATUS={'pass' if overall_pass else 'fail'}")


if __name__ == "__main__":
    main()
