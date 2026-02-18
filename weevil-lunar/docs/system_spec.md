# Weevil-Lunar System Specification (v0.3)

## 1. Mission objectives

### Primary
- Traverse mixed mare/highland terrain with robust quasi-static locomotion.
- Maintain mobility on slopes up to 45° using active foot anchoring.
- Operate under lunar dust, vacuum, and thermal constraints with delayed comms.

### Secondary
- Approach and inspect rough terrain edges (e.g., tube entrances).
- Build data products for morphology and foothold optimization.

## 2. Environment assumptions
- Gravity: 1.62 m/s²
- Atmosphere: vacuum
- Terrain: mare/highland/mixed/compacted regolith classes
- Thermal: large diurnal swings; active thermal control required

## 3. Architecture summary
- Platform: weevil/beetle-inspired hexapod
- Mobility mode: quasi-static first, dynamic later
- Foot strategy: directional cleats + twist-settle anchoring + preload scheduling
- Autonomy: onboard foothold scoring and slip-aware gait adaptation

## 4. Top-level requirements

- REQ-MOB-001: System shall preserve stable quasi-static gait under nominal traverses.
- REQ-MOB-002: System shall support slope operations to 45° with directional traction margins.
- REQ-FOOT-001: Foot subsystem shall support active anchoring with twist-settle routine.
- REQ-FOOT-002: On 45° slope, downslope margin shall be >= 1.05.
- REQ-FOOT-003: On 45° slope, lateral margin shall be >= 1.20.
- REQ-FOOT-004: Sinkage shall remain under configured limit in validation tests.
- REQ-AUTO-001: Controller shall gate push-off behind anchoring state confirmation for steep slopes.
- REQ-DUST-001: Interfaces shall be dust-hardened for repeated regolith contact cycles.
- REQ-THERM-001: Thermal architecture shall keep critical electronics/actuators in operating band.
- REQ-CAD-001: CAD package shall include parameterized phase-2 fixture integration artifacts and export scaffolding for reproducible AP242/URDF bundle generation.
- REQ-CAD-002: Export bundle shall include FCStd/AP242/receipt artifacts with freshness evidence for release closeout.

## 5. Current evidence baseline
From v0.3 directional rescue sweep:
- Mare can be rescued in-model with geometry + directional anchoring:
  - example feasible point: radius=0.08 m, preload=20 N, gains(fwd/lat)=1.50/1.80
- Baseline non-anchored directional slope test fails at 45° across terrains (expected for v0 baseline).

## 6. Open items
- Validate directional gain assumptions against higher-fidelity contact models/hardware bins.
- Add extraction/time penalties for anchoring state transitions in gait planner.
- Add thermal-vac and dust endurance evidence into requirement traceability.
