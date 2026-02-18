# Phase 2 — MRover FreeCAD Example Mapping to Lunar-Weevil CAD

## Intent
Map newly added MRover FreeCAD examples into practical Weevil-Lunar subassemblies so we can reuse proven mount/spline patterns instead of re-deriving from scratch.

## Input Example Set
From `results/GPT/Robotics/MRover/FreeCAD/`:
- `20T_spline.FCStd`
- `makerbeam_end_mount_20T_micro_servo.FCStd`
- `makerbeam_end_mount_20T_micro_servo_25mm_arm.FCStd`
- `makerbeam_end_mount_pivot_flange.FCStd`
- `makerbeam_micro_servo_end_mount.FCStd`
- `makerbeam_micro_servo_end_angle_mount.FCStd`
- `makerbeam_end_angle_micro_servo_mount.stl`
- corresponding STL variants for above parts

## Mapping Table (Example -> Weevil Use)

1) `20T_spline.FCStd`
- **Weevil target:** actuator output interfaces (coxa/femur/tibia drive couplers)
- **Action:** treat as reference profile for servo horn/spline adapter studies only.
- **Parametrize:** major/minor spline diameters, tooth count, hub thickness.
- **Output artifact:** `cad/adapters/spline_20T_adapter.FCStd`

2) `makerbeam_end_mount_20T_micro_servo.FCStd`
- **Weevil target:** compact servo bracket prototype for benchtop leg-joint rig.
- **Action:** convert geometry into parameterized bracket template; preserve hole pattern strategy.
- **Parametrize:** mount face width, hole pitch, bolt diameter, offset from beam datum.
- **Output artifact:** `cad/fixtures/servo_mount_template.FCStd`

3) `makerbeam_end_mount_20T_micro_servo_25mm_arm.FCStd`
- **Weevil target:** short-link actuation test fixture (for femur/tibia stroke characterization).
- **Action:** adapt arm interface pattern as removable test lever.
- **Parametrize:** arm length, hub thickness, interface hole count.
- **Output artifact:** `cad/fixtures/actuation_lever_25mm_template.FCStd`

4) `makerbeam_end_mount_pivot_flange.FCStd`
- **Weevil target:** proximal gimbal/pivot flange starter for coxa mount experiments.
- **Action:** reuse flange topology and bolt-circle logic.
- **Parametrize:** flange OD/ID, bolt circle diameter, wall thickness.
- **Output artifact:** `cad/interfaces/pivot_flange_template.FCStd`

5) `makerbeam_micro_servo_end_mount.FCStd` and `makerbeam_micro_servo_end_angle_mount.FCStd`
- **Weevil target:** orthogonal bracket concepts for packaging at leg roots and sensor mast micro-actuation.
- **Action:** import as layout references; do not directly productionize dimensions.
- **Parametrize:** right-angle offset, gusset thickness, clearance envelope.
- **Output artifact:** `cad/fixtures/right_angle_mount_template.FCStd`

## Integration Rules
- Keep `cad/weevil_leg_params.yaml` as source of truth.
- Bind all created dimensions through the `Params` spreadsheet aliases (see `freecad_expression_bindings.md`).
- Names must follow existing conventions:
  - Bodies: `Body_Coxa`, `Body_Femur`, `Body_Tibia`, `Body_Foot`
  - Datums: `Datum_A_FootPlane`, `Datum_B_CoxaAxis`

## Phase 2 Build Sequence
1. Create `cad/reference/` and copy/link MRover examples as read-only references.
2. Build parameterized templates listed above (adapter, servo mount, pivot flange, right-angle mount).
3. Insert templates into Weevil leg assembly as optional fixtures (not flight hardware).
4. Verify no collision in neutral pose and joint limits still match YAML.
5. Export AP242 + URDF bundle with receipt notes.

## Validation Checklist (Phase 2)
- [ ] Spline adapter mates to chosen actuator profile in CAD test scene.
- [ ] Pivot flange aligns with coxa datum and preserves orthogonality tolerance.
- [ ] Fixture templates regenerate correctly when Params aliases change.
- [ ] `weevil_leg_module_ap242.step` exports with mating datums visible.
- [ ] URDF approximation unchanged unless explicitly version-bumped.

## Non-goals
- No claim of direct lunar-flight readiness for MakerBeam micro-servo geometries.
- No replacement of Weevil structural leg design with COTS micro-servo assumptions.
- These are template accelerators for packaging and bench prototyping only.
