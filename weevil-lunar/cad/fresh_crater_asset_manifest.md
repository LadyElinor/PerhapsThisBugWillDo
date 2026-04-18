# Fresh Crater CAD Asset Manifest (v0.1)

## Purpose
Human-readable admission log for CAD assets used by the fresh-crater explorer mission thread.

## Admitted asset classes
- leg module baseline geometry
- actuator / gearbox candidate geometry
- assembly snapshot geometry for interface review

## Admitted assets
- `weevil_leg_module_ap242`
- `apex_AE050_nema23_p1110100002`
- `apex_AE070_metric_p1110200001`
- `apex_AE090_dt90_px90_p1110300004`
- `Attempt1_solids`
- `Phase2_Templates_solids`

## Analysis-only asset
- `apex_AE060_equiv_blend`
  - synthetic candidate manifest only
  - no normalized STEP backing artifact
  - not admitted as a buildable source asset in v0.1

## Governance rule
All admitted fresh-crater CAD assets shall preserve:
- provenance source path
- normalized STEP path when present
- intended role
- evidence tier
- synthetic flag

The canonical machine-readable source for this set is `cad/assets/fresh_crater_candidates.yaml`.
