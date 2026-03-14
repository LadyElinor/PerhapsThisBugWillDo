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
