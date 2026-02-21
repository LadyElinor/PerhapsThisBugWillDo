# FreeCAD Compile Macros

## `Compile_Rover.FCMacro`
Use for quick compile from the currently active FreeCAD document (or template fallback).

- Best for rapid iteration and template/blockout checks.
- Exports to `cad/export/rover_compiled*`.

## `Compile_Rover_Detailed.FCMacro`
Use for detail-first compile from normalized STEP candidates.

- Auto-ingests from: `cad_assets/normalized_step/lunar_weevil_candidates/*.step`
- Best for producing part-based assembly exports (not blockout boxes/templates).
- Exports to:
  - `cad/export/rover_detailed_compiled.FCStd`
  - `cad/export/rover_detailed_compiled_ap242.step`
  - detailed compile receipts (`.md` + `.json`)

## Rule of thumb
- If you see simple template geometry/boxes, use **`Compile_Rover_Detailed.FCMacro`**.
- If you need a quick snapshot of your active modeling session, use **`Compile_Rover.FCMacro`**.
