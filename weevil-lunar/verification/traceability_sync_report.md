# Traceability Sync Report

Status column is derived from executed receipts (commit 0121c80bdde70416d86738a60da490637b04b335, 2026-07-16T16:18:30+00:00).

- Requirements found in docs/specs: 38
- Rows in traceability CSV: 40
- Harnesses pending requirement linkage (declared debt): 5
- Requirements with no traceability row: 0

## Derived statuses

| requirement | test | derived status | data_source | evidence_pass | blocked_by_finding | detail |
|---|---|---|---|---|---|---|
| REQ-MOB-002 | slope_rescue_sweep | pass | model_coupled | false |  | 4/4 gates pass under 'rescue/*' |
| REQ-FOOT-001 | test_twist_settle_gain | pass | model_coupled | false |  | gate 'mare/twist_settle_gain' passed |
| REQ-FOOT-002 | test_directional_slope_margin_45deg | expected-fail | model_coupled | false |  | gate 'mare/directional_slope_margin_45deg' failing as documented (baseline design gap) |
| REQ-FOOT-003 | test_directional_slope_margin_45deg | expected-fail | model_coupled | false |  | gate 'mare/directional_slope_margin_45deg' failing as documented (baseline design gap) |
| REQ-FOOT-002 | slope_rescue_sweep | pass | model_coupled | false |  | 4/4 gates pass under 'rescue/*' |
| REQ-FOOT-003 | slope_rescue_sweep | pass | model_coupled | false |  | 4/4 gates pass under 'rescue/*' |
| REQ-FOOT-004 | test_sinkage_limit | pass | model_coupled | false |  | gate 'mare/sinkage_limit' passed |
| REQ-AUTO-001 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-DUST-001 | test_dust_ingress_endurance | pass | model_coupled | false |  | harness 'dust_ingress_endurance' combined status |
| REQ-THERM-001 | test_thermal_vac_cycle | pass | model_coupled | false |  | harness 'thermal_vac_cycle' combined status |
| REQ-ACT-001 | test_actuation_bench | pass | model_coupled | false |  | harness 'actuation_bench' combined status |
| REQ-ACT-002 | test_actuation_bench | pass | model_coupled | false |  | harness 'actuation_bench' combined status |
| REQ-ACT-003 | test_actuation_bench | pass | model_coupled | false |  | harness 'actuation_bench' combined status |
| REQ-ACT-004 | test_actuation_bench | pass | model_coupled | false |  | harness 'actuation_bench' combined status |
| REQ-AUTO-002 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-AUTO-003 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-AUTO-004 | test_autonomy_health_planner | pass | model_coupled | false |  | harness 'autonomy_health_planner' combined status |
| REQ-AUTO-005 | test_autonomy_health_planner | pass | model_coupled | false |  | harness 'autonomy_health_planner' combined status |
| REQ-COMMS-001 | test_power_comms_profile | pass | model_coupled | false |  | harness 'power_comms_profile' combined status |
| REQ-COMMS-002 | test_power_comms_profile | pass | model_coupled | false |  | harness 'power_comms_profile' combined status |
| REQ-DUST-002 | test_dust_ingress_endurance | pass | model_coupled | false |  | harness 'dust_ingress_endurance' combined status |
| REQ-DUST-003 | test_dust_ingress_endurance | pass | model_coupled | false |  | harness 'dust_ingress_endurance' combined status |
| REQ-LOCO-001 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-LOCO-002 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-LOCO-003 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-LOCO-004 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-MOB-001 | test_steep_slope_state_machine | pass | model_coupled | false |  | harness 'steep_slope_state_machine' combined status |
| REQ-PWR-001 | test_power_comms_profile | pass | model_coupled | false |  | harness 'power_comms_profile' combined status |
| REQ-PWR-002 | test_power_comms_profile | pass | model_coupled | false |  | harness 'power_comms_profile' combined status |
| REQ-THERM-002 | test_thermal_vac_cycle | pass | model_coupled | false |  | harness 'thermal_vac_cycle' combined status |
| REQ-THERM-003 | test_thermal_vac_cycle | pass | model_coupled | false |  | harness 'thermal_vac_cycle' combined status |
| REQ-LOCO-005 | test_rover_informed_profile | pass | model_coupled | false |  | harness 'rover_informed_profile' combined status |
| REQ-LOCO-006 | test_rover_informed_profile | pass | model_coupled | false |  | harness 'rover_informed_profile' combined status |
| REQ-THERM-004 | test_rover_informed_profile | pass | model_coupled | false |  | harness 'rover_informed_profile' combined status |
| REQ-THERM-005 | test_rover_informed_profile | pass | model_coupled | false |  | harness 'rover_informed_profile' combined status |
| REQ-PWR-003 | test_rover_informed_profile | pass | model_coupled | false |  | harness 'rover_informed_profile' combined status |
| REQ-PWR-004 | test_rover_informed_profile | pass | model_coupled | false |  | harness 'rover_informed_profile' combined status |
| REQ-COMMS-003 | test_rover_informed_profile | pass | model_coupled | false |  | harness 'rover_informed_profile' combined status |
| REQ-CAD-001 | test_phase2_cad_artifacts | pass | placeholder | false |  | harness 'phase2_cad_artifacts' combined status |
| REQ-CAD-002 | test_phase2_export_bundle | pass | placeholder | false |  | harness 'phase2_export_bundle' combined status |

## Harnesses pending requirement linkage

- axis_orthogonality_sensitivity: needs REQ-LOCO/REQ-FOOT id for axis-orthogonality envelope
- duty_cycle_cadence_envelope: needs REQ-LOCO id for cadence/duty-cycle envelope
- offplane_coupling_index: needs REQ-LOCO/REQ-FOOT id for off-plane coupling limit
- offplane_impulse_recovery: needs REQ-LOCO id for impulse-recovery time/slip
- stance_phase_detection: needs REQ-AUTO id for stance-phase detection

## Requirements with no traceability row

- none
