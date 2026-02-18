# Right-Angle Mount Template (FreeCAD Build Spec)

## Purpose
Orthogonal mount template from MRover angle-mount examples for coxa-root packaging and sensor-mast micro-actuation fixtures.

## Source references
- `results/GPT/Robotics/MRover/FreeCAD/makerbeam_micro_servo_end_angle_mount.FCStd`
- `results/GPT/Robotics/MRover/FreeCAD/makerbeam_end_angle_micro_servo_mount.stl`

## Output target
- `cad/fixtures/right_angle_mount_template.FCStd`

## New aliases to add (template-specific)
- `ra_leg_a_mm` = 30.0
- `ra_leg_b_mm` = 24.0
- `ra_thickness_mm` = 3.0
- `ra_gusset_thickness_mm` = 2.5
- `ra_hole_d_mm` = 2.2
- `ra_hole_pitch_mm` = 12.0

## Build procedure
1. Build orthogonal L-profile from two pads.
2. Add gusset feature for stiffness.
3. Add dual-face hole patterns bound to aliases.
4. Add datums for orthogonality checking.

## Validation
- 90° orthogonality retained under alias changes.
- Clearances maintained in local assembly envelope.
- No self-intersection/manifold issues on export.
