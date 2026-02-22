# No-Hardware-Yet Validation Plan (Pre-Bench)

**Date:** 2026-02-22  
**Goal:** De-risk first physical build by validating assumptions, interfaces, and data pipeline before hardware arrives.

## A. Simulation/CAD checks to run now

### A1) Baseline configuration consistency check
- Confirm digital baseline is still `uniform_ae070 + CLEAT-C1` with `hybrid_b` fallback.
- Re-run comparison script with latest assumptions if any model file changed.

**Pass criteria:** ranked output still shows LEG-C1 as efficiency-leading pass and clear pivot trigger definition.

### A2) CAD integrity and packaging checks
Using digital baseline workflow (`verification/digital_baseline_v0_4.md`):
- invalid/colliding shapes = 0
- verify bbox and COM frame consistency (foot-plane frame)
- document any interface-only/placeholder geometry

**Pass criteria:** no collisions, interface dimensions frozen for first article, COM frame anchored to test rig convention.

### A3) Cleat geometry manufacturability screen
For C1/C2 STL/CAD drafts:
- minimum feature size vs nozzle/tool capability
- print orientation and support risk
- mounting flatness and hole alignment

**Pass criteria:** both candidates printable in <6h each and mount without rework geometry edits.

### A4) Test matrix/data pipeline dry-run
- Use template CSV and run-order CSV to generate synthetic runs.
- Run:
  - `03_quick_analysis_2026-02-22.py`
  - `09_matrix_completeness_check_2026-02-22.py`

**Pass criteria:** scripts execute cleanly; completeness status reaches `MATRIX_READY` with synthetic minimum matrix.

## B. Acceptance criteria (pre-hardware readiness gate)

Pre-hardware package is READY only if all are true:
1. Design baseline + fallback mapping documented and traceable.
2. CAD collision/integrity check recorded with zero blocking issues.
3. Cleat candidates pass manufacturability screen.
4. Logging schema validated end-to-end by script dry-run.
5. Procurement plan includes lead-time mitigation for AE070/AE090 path.

## C. Script/data schema alignment with future bench tests

### Required schema contract
Future bench logs must preserve exact field names in:
- `results/validation/2026-02-22/03_data_logging_template_2026-02-22.csv`

Minimum high-risk fields to lock now:
- `run_id`, `candidate_id`, `slope_deg`
- `commanded_distance_mm`, `progress_distance_mm`, `slip_ratio_pct`
- `mean_current_a`, `peak_current_a`, `input_energy_wh`
- `damage_flag`, `stall_events`, `overcurrent_events`

### Alignment controls
- Freeze a `schema_version` note in test log headers.
- Reject rows missing must-have columns before analysis.
- Keep run IDs consistent with `08_run_order_2026-02-22.csv` pattern.

## D. Pre-bench checklist (execution order)
1. Run digital consistency + CAD checks.
2. Freeze interface drawing/rev for cleat mount and gearbox output.
3. Run synthetic CSV through analysis scripts.
4. Sign off readiness gate with date/owner.

## E. Ready-to-run command snippets
```powershell
python weevil-lunar/results/validation/2026-02-22/09_matrix_completeness_check_2026-02-22.py <filled_or_synthetic.csv>
python weevil-lunar/results/validation/2026-02-22/03_quick_analysis_2026-02-22.py <filled_or_synthetic.csv> --out-prefix weevil-lunar/results/validation/2026-02-22/prebench_check
```
