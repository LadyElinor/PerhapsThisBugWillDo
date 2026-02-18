# FreeCAD Handoff Bundle

This bundle is intended for Phase 2 template regeneration and assembly integration.

## Files
- `freecad_spreadsheet_template.csv`
- `phase2_template_aliases.csv`
- `expected_aliases.txt`
- `mapping_checklist.md`

## Usage
1. Open `cad/Phase2_Templates.FCMacro` in FreeCAD.
2. Ensure macro CSV path points to this bundle or copy these CSV files to `cad/`.
3. Rebuild the spreadsheet aliases and update expressions.
4. Run checklist in `mapping_checklist.md` before export.

## Generation
These files are regenerated via:
- `python cad/scripts/generate_csvs_from_yaml.py`
- `python cad/scripts/validate_weevil_leg_params.py`
