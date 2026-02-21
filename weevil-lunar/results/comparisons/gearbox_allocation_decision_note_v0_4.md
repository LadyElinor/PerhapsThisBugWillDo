# Gearbox Allocation Decision Note (v0.4)

## Run context
- Runner: `weevil-lunar/tools/compare_gearbox_allocations.py`
- Mode: `real_sim`
- Stress knobs:
  - `derate=0.55`
  - `ankle_demand_mult=1.5`
  - `slopes=35,45`
- Output CSV:
  - `weevil-lunar/results/comparisons/gearbox_comparison_derate055_ankle15_s35_45.csv`

## Decision
- **Default configuration (v0.4): `uniform_ae070`**
- **Fallback configuration (stress/robustness): `hybrid_b`** (`AE090 hip + AE070 knee + AE070 ankle`)

## Why
- `uniform_ae070` remains the best energy performer while maintaining strong positive torque margins in both 35° and 45° stress runs.
- `hybrid_b` provides slightly stronger torque headroom than uniform but with a notable energy penalty; keep as fallback where torque reserve dominates mission goals.
- `tapered` and `hybrid_a` are both ankle-limited relative to alternatives under current stress assumptions.

## Key evidence (from stress CSV)
At 45° slope (real_sim):
- `uniform_ae070`: energy `1.6522 J`, overall margin `74.1429 Nm`, status `PASS`
- `hybrid_b`: energy `2.0938 J`, overall margin `75.1429 Nm`, status `PASS`
- `hybrid_a`: energy `1.9258 J`, overall margin `52.1250 Nm`, status `PASS`
- `tapered`: energy `1.7577 J`, overall margin `28.7500 Nm`, status `PASS`

## Assumptions / caveats
- CAD evidence tier is currently `geometry_only`; some APEX models appear partial/interface-heavy.
- Absolute packaging and mass should be treated as provisional until full-body CAD validation.
- Torque mapping uses simplified catalog bins and global derate.

## Trigger to revisit
Re-run allocation decision if any of these occur:
1. higher-stress mission envelope (e.g., slope >45°, ankle mult >1.7)
2. updated full-detail CAD or measured hardware inertia/torque
3. new drivetrain ratio mapping by joint
4. failures/marginals in bench validation
