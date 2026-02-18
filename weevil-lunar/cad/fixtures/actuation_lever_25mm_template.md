# Actuation Lever 25mm Template (FreeCAD Build Spec)

## Purpose
Removable lever template derived from MRover 25mm arm example for benchtop femur/tibia stroke and torque characterization.

## Source reference
- `results/GPT/Robotics/MRover/FreeCAD/makerbeam_end_mount_20T_micro_servo_25mm_arm.FCStd`

## Output target
- `cad/fixtures/actuation_lever_25mm_template.FCStd`

## New aliases to add (template-specific)
- `lever_length_mm` = 25.0
- `lever_width_mm` = 8.0
- `lever_thickness_mm` = 3.0
- `lever_hub_d_mm` = 10.0
- `lever_hub_thickness_mm` = 4.0
- `lever_tip_hole_d_mm` = 2.0

## Build procedure
1. Build hub profile and pad.
2. Create lever arm from tangent profile and pad/pocket as needed.
3. Add tip hole and optional slot variant.
4. Add datum axis through hub center.

## Validation
- Lever length tracks alias exactly.
- Hub concentricity maintained with spline adapter mating face.
- No interference in expected sweep envelope.
