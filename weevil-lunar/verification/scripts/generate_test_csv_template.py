#!/usr/bin/env python3
"""Generate bench-test CSV template from bench_test_data_v0.yaml required fields."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "verification" / "data_schema" / "bench_test_data_v0.yaml"
OUT = ROOT / "verification" / "templates" / "bench_test_data_template.csv"


def main() -> int:
    # Keep this lightweight and dependency-free for CI portability.
    required = [
        "run_id",
        "timestamp_utc",
        "soil_type",
        "strategy",
        "cleat_variant",
        "preload_N",
        "cycle_num",
        "pull_rate_mm_per_s",
        "sample_rate_hz",
        "delta_z_init_mm",
        "delta_z_engage_mm",
        "f_peak_N",
        "k_t_N_per_mm",
        "x_slip_mm",
        "e_diss_N_mm",
        "slip_detected",
        "notes",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(",".join(required) + "\n", encoding="utf-8")
    print(f"Read schema: {SCHEMA}")
    print(f"Wrote template: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
