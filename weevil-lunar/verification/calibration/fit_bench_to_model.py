#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

TEMPLATE = Path("verification/templates/bench_calibration_trials.csv")
REPORT_DIR = Path("verification/reports")

REQUIRED = [
    "run_id",
    "timestamp_utc",
    "regolith_class",
    "strategy_id",
    "preload_N",
    "pull_rate_mm_per_s",
    "sample_rate_hz",
    "temperature_C",
    "F_peak_N",
    "k_t_N_per_mm",
    "x_slip_mm",
]


def _f(v: str) -> float | None:
    s = (v or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _fit_line(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    if n < 2:
        return 0.0, sum(ys) / n if n else 0.0
    xbar = sum(xs) / n
    ybar = sum(ys) / n
    num = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    den = sum((x - xbar) ** 2 for x in xs)
    if den == 0:
        return 0.0, ybar
    a = num / den
    b = ybar - a * xbar
    return a, b


def _mae(y_true: list[float], y_pred: list[float]) -> float:
    if not y_true:
        return 0.0
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true)


def _std(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _ci95(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    return 1.96 * _std(vals) / math.sqrt(len(vals))


def _bucket_temp(temp_c: float | None) -> str:
    if temp_c is None:
        return "T_UNKNOWN"
    if temp_c < 15.0:
        return "T_LOW"
    if temp_c <= 25.0:
        return "T_NOMINAL"
    return "T_HIGH"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with TEMPLATE.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        cols = rdr.fieldnames or []
        missing = [c for c in REQUIRED if c not in cols]
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        rows = list(rdr)

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    global_groups: dict[str, list[dict[str, str]]] = defaultdict(list)

    for r in rows:
        temp = _f(r.get("temperature_C"))
        temp_bucket = _bucket_temp(temp)
        key = f"{r['strategy_id']}|{r['regolith_class']}|{temp_bucket}"
        groups[key].append(r)
        global_groups[r["strategy_id"]].append(r)

    out_rows = []
    params = {
        "source": str(TEMPLATE),
        "grouping": "strategy_id + regolith_class + temperature_bucket",
        "models": {},
        "global_by_strategy": {},
    }

    for group_key, rs in sorted(groups.items()):
        strategy_id, regolith_class, temp_bucket = group_key.split("|")
        xs, yf, ys, yk = [], [], [], []
        for r in rs:
            p = _f(r.get("preload_N"))
            fpk = _f(r.get("F_peak_N"))
            slip = _f(r.get("x_slip_mm"))
            kt = _f(r.get("k_t_N_per_mm"))
            if None in {p, fpk, slip, kt}:
                continue
            xs.append(p)
            yf.append(fpk)
            ys.append(slip)
            yk.append(kt)

        a_f, b_f = _fit_line(xs, yf)
        a_s, b_s = _fit_line(xs, ys)

        pred_f = [a_f * x + b_f for x in xs]
        pred_s = [a_s * x + b_s for x in xs]
        mean_k = sum(yk) / len(yk) if yk else 0.0
        pred_k = [mean_k for _ in yk]

        force_mae = _mae(yf, pred_f)
        slip_mae = _mae(ys, pred_s)
        stiff_mae = _mae(yk, pred_k)

        force_resid = [t - p for t, p in zip(yf, pred_f)]
        slip_resid = [t - p for t, p in zip(ys, pred_s)]
        stiff_resid = [t - p for t, p in zip(yk, pred_k)]

        force_ci95 = _ci95(force_resid)
        slip_ci95 = _ci95(slip_resid)
        stiff_ci95 = _ci95(stiff_resid)
        n = len(xs)
        row_pass = n >= 2

        params["models"][group_key] = {
            "strategy_id": strategy_id,
            "regolith_class": regolith_class,
            "temperature_bucket": temp_bucket,
            "n": n,
            "force_model": {"alpha": a_f, "beta": b_f},
            "slip_model": {"alpha": a_s, "beta": b_s},
            "stiffness_model": {"mean_k_t_N_per_mm": mean_k},
            "fit_error": {
                "force_mae_N": force_mae,
                "slip_mae_mm": slip_mae,
                "stiffness_mae_N_per_mm": stiff_mae,
            },
            "confidence_95": {
                "force_ci95_N": force_ci95,
                "slip_ci95_mm": slip_ci95,
                "stiffness_ci95_N_per_mm": stiff_ci95,
            },
        }

        out_rows.append(
            {
                "group_key": group_key,
                "strategy_id": strategy_id,
                "regolith_class": regolith_class,
                "temperature_bucket": temp_bucket,
                "n_samples": n,
                "force_alpha": round(a_f, 6),
                "force_beta": round(b_f, 6),
                "slip_alpha": round(a_s, 6),
                "slip_beta": round(b_s, 6),
                "mean_k_t_N_per_mm": round(mean_k, 6),
                "force_mae_N": round(force_mae, 6),
                "slip_mae_mm": round(slip_mae, 6),
                "stiffness_mae_N_per_mm": round(stiff_mae, 6),
                "force_ci95_N": round(force_ci95, 6),
                "slip_ci95_mm": round(slip_ci95, 6),
                "stiffness_ci95_N_per_mm": round(stiff_ci95, 6),
                "pass": row_pass,
            }
        )

    # Global fallback models per strategy (used when sparse per-bucket data)
    for strategy_id, rs in sorted(global_groups.items()):
        xs, yf, ys, yk = [], [], [], []
        for r in rs:
            p = _f(r.get("preload_N"))
            fpk = _f(r.get("F_peak_N"))
            slip = _f(r.get("x_slip_mm"))
            kt = _f(r.get("k_t_N_per_mm"))
            if None in {p, fpk, slip, kt}:
                continue
            xs.append(p)
            yf.append(fpk)
            ys.append(slip)
            yk.append(kt)
        a_f, b_f = _fit_line(xs, yf)
        a_s, b_s = _fit_line(xs, ys)
        mean_k = sum(yk) / len(yk) if yk else 0.0
        params["global_by_strategy"][strategy_id] = {
            "n": len(xs),
            "force_model": {"alpha": a_f, "beta": b_f},
            "slip_model": {"alpha": a_s, "beta": b_s},
            "stiffness_model": {"mean_k_t_N_per_mm": mean_k},
        }

    csv_path = REPORT_DIR / "bench_model_fit.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(out_rows[0].keys()) if out_rows else ["group_key", "strategy_id", "n_samples", "pass"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        if out_rows:
            w.writerows(out_rows)

    json_path = REPORT_DIR / "bench_model_params.json"
    json_path.write_text(json.dumps(params, indent=2), encoding="utf-8")

    md_path = REPORT_DIR / "bench_model_fit.md"
    lines = [
        "# Bench-to-Model Calibration Fit",
        "",
        f"- source: `{TEMPLATE}`",
        f"- groups fit: {len(out_rows)}",
        "",
        "| group | n | force MAE (N) | slip MAE (mm) | stiffness MAE (N/mm) | force CI95 | slip CI95 | stiff CI95 | pass |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in out_rows:
        lines.append(
            f"| {r['group_key']} | {r['n_samples']} | {r['force_mae_N']} | {r['slip_mae_mm']} | {r['stiffness_mae_N_per_mm']} | {r['force_ci95_N']} | {r['slip_ci95_mm']} | {r['stiffness_ci95_N_per_mm']} | {r['pass']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
