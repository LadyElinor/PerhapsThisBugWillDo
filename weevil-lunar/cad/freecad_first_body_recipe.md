# FreeCAD First-Body Recipe (No FEM)

This creates a deterministic starter part path and avoids FEM YAML/JSON import entirely.

## 1) Create document + parameter table
1. File → New.
2. Add Spreadsheet, rename to `Params`.
3. Import/copy rows from `freecad_spreadsheet_template.csv`.
4. Set aliases for each value cell (e.g., `coxa_shaft_diameter_mm`).

## 2) Build Coxa starter body
1. Switch to Part Design.
2. Create Body → rename `Body_Coxa`.
3. Create Sketch on XY plane.
4. Draw shaft bore/profile circles and constrain with expressions:
   - Diameter = `Spreadsheet.coxa_shaft_diameter_mm`
5. Pad to your initial width target (fixed for now or add new alias).

## 3) Add reference datums
1. Create Datum plane at foot contact reference target (later used as Datum A).
2. Create Datum axis along coxa yaw axis (Datum B reference).
3. Name them:
   - `Datum_A_FootPlane`
   - `Datum_B_CoxaAxis`

## 4) Create Femur starter body
1. New Body → `Body_Femur`.
2. Sketch centerline-driven profile.
3. Set center-to-center length by expression:
   - `Spreadsheet.femur_link_length_mm`
4. Pad/Pocket as needed for first solid.

## 5) Create Foot starter body
1. New Body → `Body_Foot`.
2. Sketch base circle radius:
   - `Spreadsheet.foot_radius_mm`
3. Pad thickness:
   - `Spreadsheet.foot_pad_thickness_mm`
4. Add construction lines for cleat rake references:
   - `Spreadsheet.cleat_rake_forward_deg`
   - `Spreadsheet.cleat_rake_lateral_deg`

## 6) Save + export baseline
1. Save as `cad/weevil_lunar_v0.3_leg_module.FCStd`.
2. Export selected assembly/body as STEP AP242:
   - `weevil_leg_module_ap242.step`
3. Record export metadata in commit message (tool/version/schema/hash).

## Notes
- Do not use FEM Import for parameter YAML files.
- Keep `weevil_leg_params.yaml` as source-of-truth and mirror key values in `Params`.
- Add URDF only after body names/frames are stable.
