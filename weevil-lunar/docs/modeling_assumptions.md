# Modeling Assumptions and Limits

## Current model class
This repository is currently a **quasi-static / envelope-analysis** package, not a full dynamics simulator.

## Contact and soil model assumptions
- Regolith interaction uses simplified terramechanics assumptions (Bekker-Wong style pressure-sinkage + Mohr-Coulomb style shear envelope).
- Directional traction modifiers (cleat gains, preload, twist-settle) are treated as tunable control-geometry factors.
- Contact is represented as reduced-order constraints, not grain-level physics.

## What this means in practice
- Good for: trade studies, directional sensitivity, design-space filtering, requirement framing.
- Not yet sufficient for: high-fidelity slip transients, detailed granular flow effects, flight certification evidence.

## Known limits
- No DEM/FEM regolith coupling in-repo yet.
- No hardware-derived calibration curves included yet.
- Dynamics and impact transients are out of current scope.

## Planned fidelity upgrades
1. Add dynamic gait/controls loop integration.
2. Add higher-fidelity contact comparison track (including DEM-style benchmark cases).
3. Add hardware-in-the-loop calibration/validation path with traceable acceptance criteria.

## Actuator/drive appendix (MIT 2.12-aligned assumptions)
The following reduced-order relationships are used as actuator-model sanity anchors:

- Motor torque: `tau_m = Kt * i`
- Back-EMF: `E = Ke * omega_m`
- Armature dynamics: `u = R*i + L*di/dt + E`
- No-load speed approximation: `omega_nl = u / Ke`

For geared drives with ratio `r > 1` (motor speed / load speed):
- `omega_load = omega_m / r`
- `tau_load ≈ r * tau_m` (idealized, losses omitted in first-order estimate)
- Reflected inertia at load side: `I_eff = I_l + I_m * r^2`

Sanity constraints used in tests:
- positive electrical parameters (`R > 0`, `L > 0`)
- positive motor constants (`Kt > 0`, `Ke > 0`)
- `r > 1` for torque-amplifying reduction stages
- `I_eff > I_l` when motor inertia and ratio are non-zero

These are model-structure checks, not hardware calibration claims.

## External resource caveat
Educational hardware resources (e.g., Studica build guides/videos/CAD) may be used for integration workflows, actuator bring-up, and bench prototyping. They are **not** accepted as evidence for lunar terramechanics or low-gravity performance claims.

## Usage guidance
Treat generated maps/figures as **decision support artifacts**, not final truth. Use them to prioritize designs before expensive high-fidelity simulation or physical tests.
