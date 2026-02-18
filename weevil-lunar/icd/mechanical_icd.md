# Mechanical ICD (v0.4 draft)

## Scope
Mechanical interfaces among chassis, legs, feet, and serviceable wear components.

Primary freeze reference: `cad/interfaces/v0.4_freeze.md`.

## Interface definitions
- Leg mount pattern and allowable tolerances
- Foot quick-swap interface geometry
- Cable/harness routing keep-out zones
- Twisting/clearance envelope for screw-joint deployment
- Datum naming and mating constraints for AP242/URDF handoff

## Critical datums (must be preserved in CAD + export)
- `Datum_0_ModuleOrigin`
- `Datum_A_FootPlane`
- `Datum_B_CoxaAxis`
- `Datum_C_CoxaMountPlane`
- `Datum_F_FemurPitchAxis`
- `Datum_T_TibiaHelicalAxis`

## Constraints
- Dust shields must not interfere with full required ROM
- Replaceable pads must be field-serviceable without full leg disassembly
- Thermal expansion effects shall be considered in tolerance stack
- Proximal axis orthogonality target/tolerance follows `weevil_leg_params.yaml`
- Helical tibia interface shall remain export-compatible with revolute+prismatic approximation
