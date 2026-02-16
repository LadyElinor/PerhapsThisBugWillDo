# Lunar morphology tradeoffs — POC (contact-constrained locomotion)

This is a comparative *architecture* analysis (not a biological reconstruction).

**Model:** Bekker pressure–sinkage + Mohr–Coulomb shear envelope, evaluated per-leg load under lunar gravity.

## Setup

- Body mass: **30.0 kg**
- Gravity: **0.165× Earth** (Moon)
- Terrains: mare, highland, mixed, compacted

## Recommended role assignments

- **Ant-like** → *fast scouts / logistics* on modest slopes; traction is usually the bottleneck on steep terrain.
- **Beetle/Weevil-like** → *generalist traverser / workhorse*; screw coupling favors smooth force routing under uncertainty.
- **Arachnid-like** → *precision reach / probing / edge work*; extra legs reduce load per contact and tend to reduce sinkage.
- **Crab-like** → *stabilizer / lateral push / anchoring*; reduced ROM trades reach for predictable contact stability.

## Full metric table

| Morphology | Terrain | Workspace vol (m³, hull proxy) | Sinkage (cm) | Cone (deg) | Max shear (N) | 45° margin | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| Ant (speed/throughput) | mare | 9.313e-04 | 0.14 | 36.8 | 6.1 | 0.82 | 45° slope likely unstable |
| Ant (speed/throughput) | highland | 9.220e-04 | 0.43 | 38.8 | 6.5 | 0.86 | 45° slope likely unstable |
| Ant (speed/throughput) | mixed | 9.207e-04 | 0.10 | 39.5 | 6.7 | 0.88 | 45° slope likely unstable |
| Ant (speed/throughput) | compacted | 9.111e-04 | 0.01 | 45.8 | 8.3 | 1.02 | — |
| Beetle/Weevil (durability) | mare | 1.465e-03 | 0.07 | 38.6 | 6.5 | 0.86 | screw coupling (robust routing); 45° slope likely unstable |
| Beetle/Weevil (durability) | highland | 1.473e-03 | 0.23 | 39.7 | 6.7 | 0.88 | screw coupling (robust routing); 45° slope likely unstable |
| Beetle/Weevil (durability) | mixed | 1.465e-03 | 0.05 | 42.0 | 7.3 | 0.93 | screw coupling (robust routing); 45° slope likely unstable |
| Beetle/Weevil (durability) | compacted | 1.467e-03 | 0.00 | 50.8 | 9.9 | 1.13 | screw coupling (robust routing) |
| Arachnid (reach/precision) | mare | 3.354e-03 | 0.08 | 38.1 | 4.8 | 0.85 | more legs → lower load/leg; 45° slope likely unstable |
| Arachnid (reach/precision) | highland | 3.380e-03 | 0.26 | 39.4 | 5.0 | 0.88 | more legs → lower load/leg; 45° slope likely unstable |
| Arachnid (reach/precision) | mixed | 3.397e-03 | 0.06 | 41.3 | 5.3 | 0.92 | more legs → lower load/leg; 45° slope likely unstable |
| Arachnid (reach/precision) | compacted | 3.381e-03 | 0.00 | 49.5 | 7.1 | 1.10 | more legs → lower load/leg |
| Crab (lateral force/stability) | mare | 3.624e-04 | 0.03 | 41.6 | 5.4 | 0.92 | more legs → lower load/leg; reduced ROM (stable contact); 45° slope likely unstable |
| Crab (lateral force/stability) | highland | 3.588e-04 | 0.13 | 41.2 | 5.3 | 0.91 | more legs → lower load/leg; reduced ROM (stable contact); 45° slope likely unstable |
| Crab (lateral force/stability) | mixed | 3.494e-04 | 0.03 | 45.9 | 6.3 | 1.02 | more legs → lower load/leg; reduced ROM (stable contact) |
| Crab (lateral force/stability) | compacted | 3.562e-04 | 0.00 | 57.7 | 9.6 | 1.28 | more legs → lower load/leg; reduced ROM (stable contact) |

## Next upgrades (to make this a real design tool)

1) Replace hull volume with **ROM→accessible-set shrinkage** using torque limits ∩ contact wrench polytope.
2) Make the contact model **stance-geometry aware** (per-leg normal load varies over support polygon and slope).
3) Add **history dependence** (sinkage + shear accumulation, compaction).
4) Add **arachnid hydraulics state p** and true **hybrid mode switching** (stance/swing) for phase portraits.
