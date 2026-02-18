# Spline 20T Adapter Template (FreeCAD Build Spec)

## Purpose
Parameterized adapter profile derived from MRover `20T_spline.FCStd` reference for bench-level actuator interface studies.

## Source reference
- `results/GPT/Robotics/MRover/FreeCAD/20T_spline.FCStd`

## Output target
- `cad/adapters/spline_20T_adapter.FCStd`

## Required Params aliases
- `coxa_shaft_diameter_mm` (base bore guidance)
- `femur_link_length_mm` (optional context for lever clearance)

## New aliases to add in local Params sheet (template-specific)
- `spline_tooth_count` = 20
- `spline_major_d_mm` = 4.90
- `spline_minor_d_mm` = 3.80
- `spline_hub_thickness_mm` = 4.00
- `spline_adapter_od_mm` = 10.00
- `spline_bolt_circle_mm` = 8.00
- `spline_bolt_d_mm` = 2.00

## Build procedure
1. Create sketch `Sketch_SplineBase` on XY.
2. Add construction circles for major/minor diameters bound to aliases.
3. Add one tooth profile and polar pattern by `spline_tooth_count`.
4. Pad to `spline_hub_thickness_mm`.
5. Add adapter OD boss and bore using `coxa_shaft_diameter_mm` where needed.
6. Add bolt circle holes if fixture variant needed.
7. Create datum axis `Datum_B_SplineAxis`.

## Validation
- Tooth count = 20.
- Hub thickness matches alias.
- Axis concentricity within sketch constraints.
- Recompute cleanly after ±10% diameter sweep.

## Notes
Template is not flight-rated; it is an interface study artifact for packaging/prototyping.
