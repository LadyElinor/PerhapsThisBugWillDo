# Perception Evaluation Protocol (Illumination x Terrain Bins) v0.1

Date: 2026-03-23  
Scope: Lunar-weevil perception stack readiness under lighting and terrain variability.

## Objective
Provide a reproducible, governance-ready evaluation protocol for hazard detection, traversability estimation, and localization confidence under controlled scenario bins.

## Primary metrics
- Hazard detection F1 (binary hazard mask)
- Traversability calibration error (ECE or Brier)
- Localization confidence calibration (confidence vs empirical success)
- Stop-now safety recall (must prioritize recall over precision)
- End-to-end inference latency (P50/P95)

## Bin definitions

### Illumination bins
- `I0_shadow`: low signal / deep shadow
- `I1_grazing`: low sun angle, high cast-shadow complexity
- `I2_nominal`: moderate angle, nominal albedo contrast
- `I3_high_glare`: high specular-like glare / saturation risk

### Terrain bins
- `T0_compacted_flat`: low roughness, low slope
- `T1_loose_fine`: loose regolith-like texture, moderate sink risk
- `T2_rocky_mixed`: rocks/clutter with discontinuities
- `T3_steep_sloped`: high slope with directional slip risk

### Cross-product test matrix
- Required cells: all 16 combinations of `I* x T*`
- Minimum samples per cell: 50 frames for static metrics, 10 short sequences for temporal metrics
- Optional stress extension: add `dust_occlusion` modifier (none/light/heavy)

## Dataset/control requirements
- Fix camera intrinsics/extrinsics per run family.
- Capture sun angle, camera pose, and terrain tag in per-sample metadata.
- Maintain deterministic split manifests with stable IDs.
- Version all generated data and scenario config files.

## Execution procedure
1. Select frozen model/config artifact IDs.
2. Run inference across all required bin cells.
3. Compute per-cell metrics and pooled macro-averages.
4. Run calibration analysis for traversability + localization confidence.
5. Produce safety-focused confusion summaries (`stop_now` path).
6. Emit signed evaluation receipt with hashes of inputs/outputs.

## Acceptance thresholds (initial draft)
- Stop-now recall >= 0.98 in every cell.
- Hazard F1 >= 0.85 in each cell, macro >= 0.90.
- Traversability calibration error <= 0.08 macro.
- Localization confidence over-confidence gap <= 0.10 macro.
- P95 latency <= 120 ms for safety-relevant outputs.

## Reporting format (required)
- Per-cell table with N, metric values, pass/fail.
- Worst-cell analysis narrative (root-cause hypotheses).
- Drift comparison vs last accepted baseline.
- Explicit go/no-go recommendation.

## Governance checks
- No threshold changes in the same run as model changes.
- Any failed safety threshold blocks promotion.
- Waivers must include owner, rationale, expiration, and mitigation plan.
- Bohmian scope must remain untouched for this protocol branch.

## Suggested artifact paths
- `results/verification/perception_eval/<run_id>/per_cell_metrics.csv`
- `results/verification/perception_eval/<run_id>/calibration_summary.md`
- `results/verification/perception_eval/<run_id>/safety_confusion.csv`
- `results/verification/perception_eval/<run_id>/evaluation_receipt.json`
