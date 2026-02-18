# Servo Mount Template (FreeCAD Build Spec)

## Purpose
Parameterized bracket template from MRover servo mount examples for bench fixtures and leg-joint characterization rigs.

## Source references
- `results/GPT/Robotics/MRover/FreeCAD/makerbeam_end_mount_20T_micro_servo.FCStd`
- `results/GPT/Robotics/MRover/FreeCAD/makerbeam_micro_servo_end_mount.FCStd`

## Output target
- `cad/fixtures/servo_mount_template.FCStd`

## New aliases to add (template-specific)
- `servo_mount_width_mm` = 28.0
- `servo_mount_height_mm` = 32.0
- `servo_mount_thickness_mm` = 3.0
- `servo_hole_pitch_x_mm` = 23.0
- `servo_hole_pitch_y_mm` = 10.0
- `servo_hole_d_mm` = 2.2
- `servo_axis_offset_mm` = 8.0

## Build procedure
1. Create base plate sketch and pad.
2. Add mounting ears/gussets.
3. Drill servo pattern with alias-bound constraints.
4. Add beam-side pattern (optional variant).
5. Add datum axis for servo shaft alignment.

## Validation
- Hole pattern regenerates under alias sweep.
- Bracket remains manifold.
- Servo-axis offset preserved.

## Notes
Fixture-only geometry; not a lunar environment qualified component.
