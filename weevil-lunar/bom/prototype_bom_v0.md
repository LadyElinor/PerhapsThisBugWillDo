# Prototype BOM v0 (first physical-leg handoff)

Source assumptions: `cad/weevil_leg_params.yaml` and `bom/prototype_bom_v0.csv`.

## Notes
- This is a **prototype-only** BOM tier (not flight-intent hardware).
- Costs and vendor PNs are placeholders until sourcing pass completes.
- Keep this BOM aligned with interface freeze (`cad/interfaces/v0.4_freeze.md`).

## Category summary
- Structure: coxa + femur mechanical bodies
- Actuation: 50W-class motor, 80:1 reduction, helical tibia drive
- Bearings/Fasteners: angular contact + metric hardware
- Footing: 80 mm radius pad + directional cleats
- Instrumentation/Sealing: preload/slip sensing + dust ingress mitigation

## Exit criteria for v0 BOM
- [ ] All critical parts have at least one real vendor PN
- [ ] Lead-time risk >21 days flagged with alternates
- [ ] Unit cost fields filled for rough prototype budget
- [ ] Any changes that affect interfaces reflected in v0.4 freeze + ICD
