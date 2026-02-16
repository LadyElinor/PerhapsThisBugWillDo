# FreeCAD Build Steps (Leg Module v0.3)

## Prerequisites
- FreeCAD 1.0+ recommended
- Assembly4 or equivalent assembly workflow

## Step-by-step

1. **Create master parameter sheet**
   - Import values from `weevil_leg_params.yaml`
   - Define aliases for pitch, stroke, radius, cleat angles, etc.

2. **Build coxa part**
   - Create mount interface and shaft bore
   - Annotate critical dimensions (PMI top items)

3. **Build femur part**
   - Set link length and bearing seats
   - Add mounting interfaces to coxa/tibia

4. **Build tibia screw assembly**
   - Model screw axis and travel envelope
   - Implement stroke limits and neutral pose markers

5. **Build foot + cleat pattern**
   - Start pad base with target radius/thickness
   - Create cleat seed profile
   - Polar pattern by quadrant with directional rake/count

6. **Assemble leg module**
   - Apply local frames and constraints
   - Set neutral export pose:
     - coxa=0°, femur=0°, tibia mid-stroke

7. **Export AP242 STEP**
   - Filename: `weevil_leg_module_ap242.step`
   - Include visible mating datums and key annotations

8. **Export URDF assets**
   - Use mesh simplifications as needed
   - Approximate helical with prismatic+revolute for v0.3

9. **Record export receipt**
   - tool/version/date
   - commit hash
   - schema/version notes

## Validation checks before export
- No collisions in neutral pose
- Joint limits match YAML
- Foot plane at Z=0 in nominal stance frame
- Critical PMI dimensions present
