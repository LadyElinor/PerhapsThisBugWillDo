# Pivot Flange Template (FreeCAD Build Spec)

## Purpose
Parameterized pivot flange derived from MRover `makerbeam_end_mount_pivot_flange.FCStd` for coxa-root and proximal gimbal packaging studies.

## Source reference
- `results/GPT/Robotics/MRover/FreeCAD/makerbeam_end_mount_pivot_flange.FCStd`

## Output target
- `cad/interfaces/pivot_flange_template.FCStd`

## Required Params aliases
- `coxa_shaft_diameter_mm`
- `coxa_yaw_min_deg`
- `coxa_yaw_max_deg`

## New aliases to add (template-specific)
- `flange_od_mm` = 28.0
- `flange_id_mm` = 12.2
- `flange_thickness_mm` = 4.5
- `flange_bcd_mm` = 22.0
- `flange_hole_count` = 4
- `flange_hole_d_mm` = 3.2

## Build procedure
1. Sketch annulus (OD/ID) and pad to `flange_thickness_mm`.
2. Add bolt-circle holes with polar pattern.
3. Add key datum axis `Datum_B_CoxaAxis`.
4. Add mounting face datum `Datum_FlangeMountFace`.

## Validation
- Hole count and BCD update with aliases.
- ID clearance preserves coxa shaft interface.
- No interference in yaw sweep envelope.
- Exports with visible mating datums (AP242).
