# Bench-to-Model Calibration Kit (v0)

Purpose: convert minimal bench trials into fitted model parameters and a gateable model-vs-bench error check.

## Inputs
- Trial template: `verification/templates/bench_calibration_trials.csv`
- Contract schema: `icd/bench_calibration_contract.schema.json`

## Run
```bash
python verification/calibration/fit_bench_to_model.py
python verification/calibration/check_bench_model_error.py
python verification/calibration/trend_bench_model_error.py
python verification/calibration/suggest_threshold_tuning.py
```

## Outputs
- `verification/reports/bench_model_fit.csv`
- `verification/reports/bench_model_fit.md`
- `verification/reports/bench_model_params.json`
- `verification/reports/bench_model_error.csv`
- `verification/reports/bench_model_error.md`
- `verification/reports/bench_model_error_trend_history.csv`
- `verification/reports/bench_model_error_trend_check.{csv,md}`
- `verification/reports/bench_model_threshold_tuning.{csv,md}`

## Pass criteria (default)
Per grouped model (strategy + regolith + temperature bucket):
- samples >= 2
- force MAE <= 1.2 N
- slip MAE <= 0.5 mm
- stiffness MAE <= 0.40 N/mm
- force CI95 <= 2.0 N
- slip CI95 <= 1.0 mm
- stiffness CI95 <= 0.65 N/mm

Trend check flags regressions when MAE deltas spike or fail-count increases vs prior run.
