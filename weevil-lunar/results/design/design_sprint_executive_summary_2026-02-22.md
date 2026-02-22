# Weevil-Lunar Autonomous Design Sprint — Executive Summary (2026-02-22)

## What was executed
- Unpaused from prior checkpoint (`gearbox_comparison_hybridA_derate055_ankle15_s35.csv`) and ran integrated realism sweeps with:
  - slopes: **35°, 45°**
  - ankle multiplier: **1.5, 1.7, 1.9**
  - **size-dependent derate** (AE090 0.60, AE070 0.56, AE060 0.53, AE050 0.50)

## Key outcomes
- All four existing allocation configs stayed `PASS` in this reduced-order model.
- Ranking by robust-efficiency score (`min_margin - 10*mean_energy`):
  1. **uniform_ae070** (score **59.0209**) — best energy with strong margin floor.
  2. **hybrid_b** (score **55.5620**) — best margin floor, higher energy.
  3. hybrid_a
  4. tapered

## Candidates selected today
- **Hip candidate(s):**
  - Primary: **AE070 hip** (system-level efficiency winner)
  - Fallback: **AE090 hip** (extra headroom if shocks/thermal margins dominate)
- **Leg candidate(s):**
  - Primary: **LEG-C1 / uniform_ae070**
  - Robustness fallback: **LEG-C2 / hybrid_b**
- **Cleat candidate(s):**
  - Primary: **CLEAT-C1 asymmetric chevron paddle**
  - Secondary: CLEAT-C2 split-V + center keel
  - Hold: CLEAT-C3 helical micro-rib wrap

## Go / No-Go recommendation
- **Recommendation now: GO (Continue)** with `uniform_ae070 + CLEAT-C1` as baseline build/test pair.
- **Pivot rule:** pivot to `hybrid_b` if any validation run shows overall torque margin proxy < **20 Nm** OR sustained climb slip > **25%** at 35–45° equivalent loading.
- **Stop rule:** stop current architecture if two independent repeats show inability to maintain positive climb progress at 35° despite cleat swap + control retune.

## Cheapest next validation test (within 72h)
- **Test:** benchtop incline traction A/B on 3D printed cleats (C1 vs C2) using current leg module and ballast-equivalent normal load.
- **Instrumentation:** phone video + inline current logger + slope board + simple slip-distance markups.
- **Success gate:** C1 demonstrates >=15% lower slip ratio than baseline cleat at matched incline/load with no structural damage after 30 min cumulative stepping.
- **Why cheapest:** requires only printed cleats + existing hardware; no drivetrain redesign needed.

## Artifacts produced
- Assumptions update: `weevil-lunar/results/comparisons/model_assumptions_update_2026-02-22.md`
- Integrated sweep (full): `weevil-lunar/results/comparisons/gearbox_comparison_sprint_2026-02-22_size_derate.csv`
- Scenario winner summary: `weevil-lunar/results/comparisons/gearbox_comparison_sprint_2026-02-22_summary.csv`
- Ranked comparison rollup: `weevil-lunar/results/comparisons/gearbox_comparison_sprint_2026-02-22_ranked.csv`
- Hip candidates: `weevil-lunar/results/design/hip_design_candidates_2026-02-22.csv`
- Leg candidates: `weevil-lunar/results/design/leg_design_candidates_2026-02-22.csv`
- Cleat candidates: `weevil-lunar/results/design/cleat_design_candidates_2026-02-22.csv`
