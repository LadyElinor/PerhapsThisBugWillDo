# Lunar-Weevil Build Checklist (Rover-Informed)

## A. Scope + Baseline
- [x] Freeze v0.3 baseline artifacts (`docs/baselines/v0.3_freeze_2026-02-17_1911.md`)
- [x] Work on branch `feature/rover-informed-upgrade`
- [x] Confirm acceptance gates for mobility, thermal, power, autonomy

## B. Mobility / Stability
- [x] Implement virtual rocker-bogie gait coordination mode (config + profile harness)
- [x] Enforce slope push-off gating + traction margin thresholds
- [x] Sweep cleat geometry + compliance parameters (model-based)
- [x] Validate on flat/10°/20°/30°/45° scenarios (existing and rover-informed verification evidence)

## C. Thermal
- [x] Define warm-electronics core assumptions and limits
- [x] Add insulation + radiator area parameters
- [x] Validate thermal-vac profile for day/night envelopes

## D. Power
- [x] Add hybrid day/night power budget model
- [x] Include dust derate and recovery reserve
- [x] Validate comm-dropout energy continuity window

## E. Autonomy + Health
- [x] Verify mode transitions: nominal -> steep-slope -> recovery -> safe
- [x] Validate health telemetry buffering during link dropouts
- [x] Validate watchdog/failover behavior assumptions

## F. Integration / Traceability
- [x] Update specs and parameter YAML
- [x] Update verification matrix + requirements traceability
- [x] Run gate check and capture report artifacts

## G. Phase 2 (MRover FreeCAD Example Integration)
- [x] Map MRover example files to Weevil subassemblies (`cad/rover_freecad_mapping_phase2.md`)
- [x] Create parameterized template FCStd scaffolding (macro + per-template build specs)
- [x] Define/bind template dimensions to `Params` spreadsheet aliases (`cad/phase2_template_aliases.csv`)
- [x] Integrate templates into leg assembly as optional fixtures (integration manifest + datums/hooks)
- [x] Re-export AP242/URDF with receipt update (`cad/export/weevil_leg_module_ap242.step`, `cad/export/weevil_leg_module.urdf`, `cad/export/phase2_export_receipt.md`)

## H. Phase 2 Authoring Assets Added
- [x] `cad/adapters/spline_20T_adapter_template.md`
- [x] `cad/interfaces/pivot_flange_template.md`
- [x] `cad/fixtures/servo_mount_template.md`
- [x] `cad/fixtures/right_angle_mount_template.md`
- [x] `cad/fixtures/actuation_lever_25mm_template.md`
- [x] `cad/phase2_freecad_import_rebuild.md`
- [x] `cad/Phase2_Templates.FCMacro`
- [x] `cad/Phase2_Export.FCMacro`
- [x] `cad/phase2_integration_manifest.yaml`
- [x] `verification/test_phase2_cad_artifacts.py`
