# Phase 2 FreeCAD Import + Rebuild Procedure

## Goal
Turn MRover examples into parameterized Weevil template parts while preserving current leg-module conventions.

## Steps
1. Open FreeCAD 1.0+ and load Weevil workspace docs:
   - `cad/freecad_build_steps.md`
   - `cad/freecad_expression_bindings.md`
   - `cad/rover_freecad_mapping_phase2.md`
2. Create new doc `Phase2_Templates.FCStd`.
3. Add Spreadsheet named `Params`.
4. Import aliases from:
   - `cad/freecad_spreadsheet_template.csv`
   - `cad/phase2_template_aliases.csv`
5. For each template spec, rebuild geometry from reference examples:
   - `cad/adapters/spline_20T_adapter_template.md`
   - `cad/interfaces/pivot_flange_template.md`
   - `cad/fixtures/servo_mount_template.md`
   - `cad/fixtures/right_angle_mount_template.md`
   - `cad/fixtures/actuation_lever_25mm_template.md`
6. Recompute after each template and run parameter sweep check (±10% on key dims).
7. Insert templates into leg assembly as optional fixtures only.
8. Validate no collisions in neutral pose and preserve joint limits from YAML.
9. Export artifacts:
   - AP242: fixture/template subset + leg assembly with datums visible
   - URDF unchanged unless intentional version bump
10. Record export receipt details in commit notes.

## Quality gates
- All template dimensions are expression-bound (no hard-coded production dimensions).
- Datum naming remains stable.
- Regeneration has zero errors in Report view.
