# Cleat Overlap Resolution Note (2026-02-22)

## Context
The compact rover layout was auto-clamping foot radius below the requested 80 mm to avoid same-side leg overlap. This reduced cleat area and changed traction intent.

## Compared variants

| Variant | Body (L x W, mm) | Side x-pitch (mm) | Foot radius used (mm) | Clearance (pitch - 2R, mm) |
|---|---:|---:|---:|---:|
| compact_auto_clamped | 260 x 170 | 95 | 39.9 (auto-clamped) | 15.2 |
| scaled_full_cleat | 420 x 230 | 170 | 80.0 (preserved) | 10.0 |

## Tradeoff summary
- **Footprint / packaging**
  - Compact is materially easier to transport, bench-test, and package in small thermal/vac fixtures.
  - Scaled variant increases planform area and shipping volume (~2x class in practical packaging).
- **Stability / traction fidelity**
  - Compact mode changes effective cleat geometry by shrinking foot radius, so CLEAT-C1 behavior is not representative of intended 80 mm contact patch.
  - Scaled full-cleat preserves intended 80 mm foot/cleat radius with positive same-side clearance (10 mm), improving confidence in traction and stance stability assessments.
- **Procurement impact**
  - Compact: no immediate change to enclosure volume or board placement constraints.
  - Scaled: likely requires larger top deck, harness length increase, and larger side panel stock; may affect crate size and fixture dimensions. Core drivetrain/candidate selection is unchanged.

## Recommendation (default going forward)
Use **`scaled_full_cleat`** as default geometry for all cleat and mobility evaluations.

Keep **`compact_auto_clamped`** as a secondary packaging/proxy mode only when the test objective is integration fit, not cleat-performance truth.

## Artifacts tied to this note
- Macro update: `cad/scripts/weevil_rover_detailed_build.FCMacro`
- Variant parameters: `configs/rover_geometry_variants_2026-02-22.yaml`
- Build presets: `configs/rover_build_presets_2026-02-22.json`
- Blueprint comparison: `results/blueprints/lunar_weevil_blueprint_v0_6_variants_2026-02-22.png`
