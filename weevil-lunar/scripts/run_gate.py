#!/usr/bin/env python3
"""Cross-platform integrated gate runner (make alternative)."""

from __future__ import annotations

import subprocess
import sys

COMMANDS = [
    ["verification/scripts/validate_regolith_burrow_variants.py"],
    ["verification/scripts/sweep_regolith_burrow_thresholds.py"],
    ["verification/scripts/retrieve_regolith_variant.py"],
    ["verification/scripts/evaluate_regolith_burrow_variants.py"],
    [
        "verification/scripts/select_regolith_variant.py",
        "--mission-intent",
        "adaptive",
        "--runtime-energy-reserve",
        "0.30",
        "--runtime-component-temp-c",
        "62",
    ],
    ["verification/scripts/ingest_minimal_hardware_trials.py"],
    ["verification/calibration/fit_bench_to_model.py"],
    ["verification/calibration/check_bench_model_error.py"],
    ["verification/calibration/trend_bench_model_error.py"],
    ["verification/calibration/suggest_threshold_tuning.py"],
    ["verification/scripts/check_competing_hypotheses.py"],
    ["verification/scripts/check_uncertainty_ledger.py"],
    ["scripts/run_governance_checks.py"],
    [
        "verification/copilot/run_copilot.py",
        "--stale-days",
        "14",
        "--max-weighted-score",
        "10",
        "--suppressions",
        "verification/copilot/suppressions.yaml",
    ],
    ["verification/copilot/update_trend.py"],
    ["verification/copilot/check_trend.py"],
    ["verification/check_traceability_namespace.py"],
    ["verification/run_gate_check.py"],
]


def main() -> int:
    for cmd in COMMANDS:
        full = [sys.executable, *cmd]
        print(f"[gate] running: {' '.join(full)}")
        result = subprocess.run(full, check=False)
        if result.returncode != 0:
            return result.returncode
    print("[gate] completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
