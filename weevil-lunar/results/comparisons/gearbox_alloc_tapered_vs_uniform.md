# Gearbox Allocation Comparison (APEX AE050/070/090)

Evidence tier: `geometry_only` (CAD-derived; partial-model risk flagged).

## Configs compared

- **Tapered**: Hip AE090 / Knee AE070 / Ankle AE050
- **Uniform**: Hip/Knee/Ankle all AE070

## Current extracted geometry summary

- AE050: volume 13149.93, bbox [57.2, 8.0, 57.2]
- AE070: volume 32749.44, bbox [80.0, 11.0, 80.0]
- AE090: volume 47313.89, bbox [92.0, 12.5, 92.0]

## Interpretation (provisional)

- Tapered likely lowers distal reflected inertia and cycle energy.
- Uniform likely simplifies control/integration but penalizes distal inertia.
- Absolute package depth appears under-represented in all 3 models; treat absolute fit/mass as provisional.

## Next simulation hooks

1. Load `weevil-lunar/configs/gearbox_allocations.yaml`.
2. For each configuration, run same mission profiles (mare traverse + slope rescue).
3. Report deltas on:
   - reachability margin
   - reflected inertia penalty
   - peak torque margin
   - energy per gait cycle

## Pass/fail suggestion

- Prefer configuration that preserves required torque margin while minimizing distal inertia and per-cycle energy.
- Block hardware packaging decisions until model completeness check (full-body depth confirmation).
