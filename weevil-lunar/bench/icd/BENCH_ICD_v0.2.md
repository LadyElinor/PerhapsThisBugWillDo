# BENCH ICD v0.2

## Purpose
Define bench interfaces for repeatable Earth-analog traction/sinkage experiments.

## Mechanical interfaces
- Foot mount interface ID:
- Twist axis interface ID:
- Z-stage reference plane definition:
- Soil bin dimensions + fill volume:

## Electrical interfaces
- Tangential load-cell channel(s):
- Normal-load channel(s) (optional):
- Twist encoder channel:
- Z encoder / displacement channel:
- Sampling rate target: >=100 Hz preferred (>=50 Hz acceptable)

## Data interfaces
Each run must produce:
- `raw.csv` with time-series channels
- `metadata.json` with run config hash, git SHA, hardware ID
- `receipt.json` with calibration versions + soil SOP version

Required `raw.csv` columns:
- `t_s`
- `z_mm`
- `theta_deg`
- `f_t_n`
- `f_n_n` (if present)
- `event_label`

## Calibration interfaces
- Tangential load cell calibration curve + residuals
- Twist angle reference procedure
- Z zeroing/reference procedure

## Soil SOP linkage
- Soil prep protocol version:
- Compaction/rest timing:
- Moisture/condition notes:

## Acceptance checks
- 10-minute DAQ run without critical drops
- Timestamp monotonicity + interval sanity
- Motion command reproducibility over 100 cycles
