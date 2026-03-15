# Minimal Bench Data Protocol: Foot Anchoring (v0.1)

## Purpose
Provide the smallest credible hardware data anchor for preload/twist/slip behavior.

## Canonical template
- Input template: `verification/templates/minimal_hardware_trials.csv`
- Schema: `icd/bench_foot_anchor_contract.schema.json`

## Required fields per trial
- `run_id`, `timestamp_utc`, `soil_id`, `strategy_id`
- `preload_N`, `cycle_index`, `pull_rate_mm_per_s`, `sample_rate_hz`

## Optional measured fields (recommended)
- `F_peak_N`, `k_t_N_per_mm`, `x_slip_mm`, `E_diss_Nmm`, `sinkage_delta_mm`

## Strategy IDs (suggested)
- `S0`: press-only baseline
- `S1`: press + twist
- `S2`: press + twist + vibration

## Ingestion command
```bash
python verification/scripts/ingest_minimal_hardware_trials.py
```

Outputs:
- `verification/reports/minimal_hardware_ingest.csv`
- `verification/reports/minimal_hardware_ingest.md`

## Interpretation rule (initial)
- Any ingest report indicates data successfully parsed and summarized.
- Physics confidence only increases when measured fields are populated with repeatable values.

## Bench-to-Model calibration kit (v0)
Use measured trials to fit lightweight preload->force/slip and stiffness parameters.

Inputs:
- `verification/templates/bench_calibration_trials.csv`
- `icd/bench_calibration_contract.schema.json`

Commands:
```bash
python verification/calibration/fit_bench_to_model.py
python verification/calibration/check_bench_model_error.py
```

Outputs:
- `verification/reports/bench_model_fit.{csv,md}`
- `verification/reports/bench_model_params.json`
- `verification/reports/bench_model_error.{csv,md}`
- `verification/reports/bench_model_error_trend_history.csv`
- `verification/reports/bench_model_error_trend_check.{csv,md}`
- `verification/reports/bench_model_threshold_tuning.{csv,md}`

Default gate thresholds (per strategy):
- samples >= 3
- force MAE <= 1.2 N
- slip MAE <= 0.5 mm
- stiffness MAE <= 0.40 N/mm
- stiffness CI95 <= 0.65 N/mm
