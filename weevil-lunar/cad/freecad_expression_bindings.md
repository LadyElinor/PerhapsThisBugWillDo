# FreeCAD Expression Bindings (Starter)

Use a Spreadsheet object named `Params`.
Set aliases exactly as listed in `freecad_spreadsheet_template.csv`.

## Suggested model dimensions

- Coxa shaft sketch diameter:
  - `Spreadsheet.coxa_shaft_diameter_mm`

- Femur extrusion length:
  - `Spreadsheet.femur_link_length_mm`

- Tibia helical lead (if using additive helix/sweep helpers):
  - `Spreadsheet.tibia_pitch_mm_per_rev`

- Tibia travel limit parameter:
  - `Spreadsheet.tibia_stroke_mm`

- Foot base circle radius:
  - `Spreadsheet.foot_radius_mm`

- Foot pad thickness:
  - `Spreadsheet.foot_pad_thickness_mm`

- Forward cleat rake construction angle:
  - `Spreadsheet.cleat_rake_forward_deg`

- Lateral cleat rake construction angle:
  - `Spreadsheet.cleat_rake_lateral_deg`

## Joint limit references (for docs/constraints)

- Coxa yaw limits:
  - min: `Spreadsheet.coxa_yaw_min_deg`
  - max: `Spreadsheet.coxa_yaw_max_deg`

- Femur pitch limits:
  - min: `Spreadsheet.femur_pitch_min_deg`
  - max: `Spreadsheet.femur_pitch_max_deg`

## Naming conventions

- Bodies: `Body_Coxa`, `Body_Femur`, `Body_Tibia`, `Body_Foot`
- Datums: `Datum_A_FootPlane`, `Datum_B_CoxaAxis`
- Master spreadsheet: `Params`

This naming scheme keeps AP242 export references and later URDF mapping stable.
