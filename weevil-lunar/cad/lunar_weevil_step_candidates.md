# Lunar-Weevil STEP Candidate Parts (v0.2)

## Candidate parts to incorporate
1. **Leg module assembly** (baseline geometry + interfaces)
2. **Foot/cleat geometry set** (traction anisotropy A/B)
3. **Ankle compliance link/bracket** (force-closure tuning)
4. **Motor + gearbox mount** (alignment/load path)
5. **Hip-knee links** (mass/inertia + reach envelope)
6. **Chassis hardpoint interface** (leg-body transfer path)
7. **Hub/shaft adapter geometry** (integration + tolerancing)

## Imported now (STEP pipeline complete)
- `weevil_leg_module_ap242.step` (existing AP242 export)
- `Attempt1_solids.step` (exported from `Attempt1.FCStd`)
- `Phase2_Templates_solids.step` (exported from `Phase2_Templates.FCStd`)
- `apex_AE070_metric_p1110200001.step` (external vendor pull from APEX AE series)

## External pull notes
- HowToMechatronics link returned HTML landing content instead of STEP in this runtime; quarantined as:
  - `cad_assets/rejected/planetary_two_stage_16to1_not_step.html`
- APEX AE series direct STP ZIP pull succeeded (`P1110200001-stp.zip`), extracted and ingested.

## Pipeline outputs
### Raw STEP
- `cad_assets/raw_step/lunar_weevil_candidates/weevil_leg_module_ap242.step`
- `cad_assets/raw_step/lunar_weevil_candidates/Attempt1_solids.step`
- `cad_assets/raw_step/lunar_weevil_candidates/Phase2_Templates_solids.step`

### Normalized STEP
- `cad_assets/normalized_step/lunar_weevil_candidates/weevil_leg_module_ap242.step`
- `cad_assets/normalized_step/lunar_weevil_candidates/Attempt1_solids.step`
- `cad_assets/normalized_step/lunar_weevil_candidates/Phase2_Templates_solids.step`

### Extracted parameter JSON
- `cad_assets/manifests/lunar_weevil_candidates/params_weevil_leg_module_ap242.json`
- `cad_assets/manifests/lunar_weevil_candidates/params_Attempt1_solids.json`
- `cad_assets/manifests/lunar_weevil_candidates/params_Phase2_Templates_solids.json`

### Manifest
- `cad_assets/manifests/lunar_weevil_candidates/step_manifest.json`

## Next sourcing queue (external/vendor)
- Helical cleat variant STEP set (A/B/C)
- Candidate gearbox housings (lightweight planetary)
- Motor mounting plates / adapter rings
- Shaft collars / hubs for foot module

Note: external library pulls were not reliable in-session; used local FCStd-to-STEP exports to keep ingest pipeline moving and reproducible.
