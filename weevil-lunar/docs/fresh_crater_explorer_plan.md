# Fresh Crater Explorer Plan (v0.1)

## Objective
Extend Weevil-Lunar into a traceable fresh-crater exploration mission thread focused on rim approach, edge inspection, guarded partial descent, and retreat under mixed ejecta/highland/mare boundary conditions.

## Why this thread exists
Fresh craters create a mechanically interesting mission profile:
- blocky ejecta apron traversal
- increasing slip/sinkage risk near the rim
- partial line-of-sight occlusion during edge work and retreat
- higher consequence for disturbance, entrapment, and recovery failure

This plan treats fresh-crater work as a mission-profile extension of the existing quasi-static hexapod, not a separate vehicle architecture.

## Mission phases
1. **Traverse**
   - move across mixed ejecta and compacted zones with bounded slip
2. **Rim approach**
   - reduce speed, increase monitoring, maintain edge standoff
3. **Edge inspection**
   - hold stable pose with telemetry buffering and retreat readiness
4. **Guarded partial descent**
   - perform limited descent only when slope, reserve, and disturbance budgets remain within profile
5. **Retreat / egress**
   - recover to safer terrain while preserving health and mission logs

## Primary success metrics
- bounded sinkage and disturbance near the rim
- stable upslope and cross-slope traction margins
- positive energy reserve after inspection and retreat
- retained telemetry continuity across delayed/occluded communications
- controlled retreat after slip/load anomaly without unrecovered stall

## Initial variant family
- `rim_scout_conservative`
- `rim_scout_balanced`
- `partial_descent_guarded`

These variants are defined in `configs/fresh_crater_explorer_variants_2026-04-18.yaml`.

## Initial CAD admission strategy
Use a manifest-first approach.

Admitted candidate classes:
- leg module baseline geometry
- actuator / gearbox candidate geometry
- assembly snapshot geometry for interface review

Admitted assets are indexed in `cad/assets/fresh_crater_candidates.yaml` and verified by `verification/test_fresh_crater_cad_assets.py`.

## Risks
- geometry-only imported assets may overstate build readiness
- crater-edge scenarios may be more sensitive to disturbance than current reduced-order models capture
- mixed terrain transitions may create failure modes not visible in uniform-terrain sweeps

See also: `docs/fresh_crater_risk_register.md`.

## First implementation slice
- mission profile + requirements extension
- fresh-crater variant config
- executable profile test
- CAD candidate index and artifact presence test
- traceability update

## Follow-on work
- integrate crater-specific terrain bins into broader evaluator
- connect admitted CAD candidates to named chassis/actuation decisions
- add disturbance-aware and occlusion-aware mission rehearsals to gate checks
