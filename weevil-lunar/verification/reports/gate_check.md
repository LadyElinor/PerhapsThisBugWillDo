# Integrated Gate Check

| class | status | details |
|---|---|---|
| mobility | partial | steep_slope_state_machine.csv:pass; duty_cycle_cadence_envelope.csv:pass; offplane_impulse_recovery.csv:fail; rover_informed_profile.csv:pass |
| foot | pass | steep_slope_state_machine.csv:pass; offplane_coupling_index.csv:pass |
| autonomy | pass | steep_slope_state_machine.csv:pass; autonomy_health_planner.csv:pass; stance_phase_detection.csv:pass |
| dust | pass | dust_ingress_endurance.csv:pass |
| thermal | pass | thermal_vac_cycle.csv:pass; rover_informed_profile.csv:pass |
| actuation | pass | actuation_bench.csv:pass |
| power | pass | power_comms_profile.csv:pass; rover_informed_profile.csv:pass |
| comms | pass | power_comms_profile.csv:pass; rover_informed_profile.csv:pass |
| gait_phase | pass | stance_phase_detection.csv:pass; duty_cycle_cadence_envelope.csv:pass |
| coupling | partial | offplane_coupling_index.csv:pass; offplane_impulse_recovery.csv:fail; axis_orthogonality_sensitivity.csv:fail |
| cad_phase2 | pass | phase2_cad_artifacts.csv:pass; phase2_export_bundle.csv:pass |
| burrow_profile | pass | regolith_burrow_profile.csv:pass |
| burrow_process | partial | regolith_variant_schema_validation.csv:pass; regolith_burrow_threshold_sweep.csv:partial; regolith_variant_retrieval.csv:pass; regolith_variant_evaluation.csv:pass; regolith_variant_selection.csv:pass |
| traceability_namespace | pass | traceability_namespace_check.csv:pass |
| bench_data_ingest | pass | minimal_hardware_ingest.csv:pass |
| bench_calibration | pass | bench_model_error.csv:pass; bench_model_error_trend_check.csv:pass; bench_model_threshold_tuning.csv:pass |
| reasoning_rigor | pass | competing_hypotheses_check.csv:pass; uncertainty_ledger_check.csv:pass |
| copilot | pass | copilot_status.csv:pass; copilot_trend_check.csv:pass |
