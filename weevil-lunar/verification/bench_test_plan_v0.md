# Bench Test Plan v0: Twist-Settle Traction Emergence in Low-Preload Regolith

**Version:** v0 (tied to interface freeze v0.4)  
**Date:** 2026-02-18  
**ICD tie-in:** `cad/interfaces/v0.4_freeze.md`, `icd/mechanical_icd.md`

## Objective
Validate the thesis that active engagement (twist-settle) produces force-closure under low preload by looking for lock-in signatures:
- higher `f_peak_N`
- higher `k_t_N_per_mm`
- larger `x_slip_mm`
- stable cycle retention over repeated trials

## Minimal Rig
- Z axis for preload/placement (position or force controlled)
- Twist axis for yaw engagement (encoder feedback)
- Tangential pull axis (displacement-controlled)
- Tangential load measurement
- Two soil bins (frictional vs cohesive)
- Interchangeable cleat variants

## Factors and sweep
- Strategy: `S0` press-only, `S1` press+twist, `S2` press+twist+vibration
- Preload levels: 0.1, 0.5, 1.0, 5.0 N (adjustable)
- Soil: frictional + cohesive
- Cycles: 10 per condition

## Procedure (per trial)
1. Prepare soil patch and zero sensors.
2. Placement phase: apply preload and hold 3–5 s.
3. Engagement phase:
   - S0: hold
   - S1: apply twist recipe
   - S2: twist + vibration recipe
4. Pull phase: tangential displacement at constant rate until slip.
5. Log metrics and repeat by cycle index.

## Required metrics
- `f_peak_N`
- `k_t_N_per_mm`
- `x_slip_mm`
- `e_diss_N_mm`
- `delta_z_init_mm`
- `delta_z_engage_mm`
- cycle retention ratios (`cycle10/cycle1`)

## Acceptance gates (v0)
- `f_peak(S1)` >= 1.20 × `f_peak(S0)` at low preload
- `k_t(S1)` > `k_t(S0)` at low preload
- `x_slip(S1)` > `x_slip(S0)` at low preload
- `f_peak(cycle10)/f_peak(cycle1)` >= 0.85
- Ranking consistency in at least one soil: `S2 >= S1 >= S0` for `f_peak_N` and `k_t_N_per_mm`

## Model comparison rule
Judge primarily by strategy ranking and preload trend agreement; absolute force mismatch is acceptable at this phase.

## Deliverables
- Trial CSVs based on `verification/data_schema/bench_test_data_v0.yaml`
- Filled template: `verification/templates/minimal_hardware_trials.csv`
- Analysis notebook outputs and report summary CSV

Sign-off:
- Test Lead: ___________________ Date: __________
- Reviewer: ___________________ Date: __________
