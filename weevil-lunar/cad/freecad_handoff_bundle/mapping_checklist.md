# Phase 2 Mapping Checklist (FreeCAD Handoff)

Derived from `cad/rover_freecad_mapping_phase2.md`.

## Mapping targets
- [ ] `20T_spline.FCStd` -> `cad/adapters/spline_20T_adapter.FCStd`
- [ ] `makerbeam_end_mount_20T_micro_servo.FCStd` -> `cad/fixtures/servo_mount_template.FCStd`
- [ ] `makerbeam_end_mount_20T_micro_servo_25mm_arm.FCStd` -> `cad/fixtures/actuation_lever_25mm_template.FCStd`
- [ ] `makerbeam_end_mount_pivot_flange.FCStd` -> `cad/interfaces/pivot_flange_template.FCStd`
- [ ] `makerbeam_micro_servo_end_mount.FCStd` and `makerbeam_micro_servo_end_angle_mount.FCStd` -> `cad/fixtures/right_angle_mount_template.FCStd`

## Parameter binding
- [ ] All dimensions bound via Params aliases from the included CSVs.
- [ ] Leg geometry remains sourced by `cad/weevil_leg_params.yaml`.
- [ ] No direct hard-coded dimensions in template features.

## Bio/dynamics integration checks
- [ ] Coxa/femur/tibia limits match YAML ranges.
- [ ] Helical tibia pitch/stroke in CAD matches simulation parameters.
- [ ] Proximal axis orthogonality target/tolerance is preserved in datums.
- [ ] Internal friction assumptions are not reused as regolith contact friction.

## Export checks
- [ ] AP242 STEP export includes datum features for mating.
- [ ] URDF retains helical approximation notes (revolute + prismatic coupling).
- [ ] Export receipt captures param hash/version and date.
