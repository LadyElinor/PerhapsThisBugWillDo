# Rover-Informed Upgrade Plan (Weevil-Lunar)

## Objective
Apply proven Mars-rover design patterns (Perseverance + MER heritage) to strengthen Lunar-Weevil v0.3 in mobility, thermal survivability, power continuity, autonomy, and fault tolerance.

## Source Inputs
- `results/GPT/Robotics/MRover/Rover.txt`
- `results/GPT/Robotics/MRover/FreeCAD/*` (mechanical mounting examples)

## Design Translations

### 1) Mobility: Rocker-Bogie Lessons -> Hexapod Coordination
- Add a **virtual rocker-bogie mode** in gait control to coordinate left/right leg groups during obstacle and slope traversal.
- Keep steep-slope operations constrained with explicit push-off gating and traction margin checks.
- Use cleat density/rake sweeps and compliant linkage behavior inspired by rover wheel durability improvements.

### 2) Thermal: WEB Lessons -> Protected Core + Radiative Rejection
- Define a warm-electronics core equivalent with insulation-first architecture.
- Use dorsal radiator area sizing and night survival heater policy.
- Treat dust-sealed joints as thermal + reliability boundaries (labyrinth/isolated pods).

### 3) Power: MMRTG/MER Ops Lessons -> Hybrid + Budget Discipline
- Model hybrid generation/storage operation (day generation + night survival load).
- Keep explicit reserve for steep-slope, recovery, and comm dropout windows.
- Add dust derate factor to energy generation assumptions.

### 4) Sensing/Autonomy: Navcam/Hazcam + Health Monitoring
- Add mast-level nav sensing and leg-level slip/load observability requirements.
- Maintain autonomy state transitions: nominal, steep-slope, recovery, safe.
- Require health telemetry continuity during delayed/intermittent comm windows.

### 5) Fault Tolerance: Rover Redundancy Pattern
- Specify primary/backup compute behavior and watchdog policy.
- Ensure logs survive resets and comm dropouts for post-fault triage.

## Milestones
1. **M1 Mobility envelope**: virtual rocker-bogie profile + slope/obstacle validation.
2. **M2 Thermal-power envelope**: thermal-vac + energy continuity with derates.
3. **M3 Autonomy-health envelope**: state-machine + degraded comm operation.
4. **M4 Integration package**: updated YAML/specs/test matrix/traceability + gate check.

## Deliverables (this update set)
- Updated subsystem specs (`locomotion`, `thermal`, `power_comms`)
- Updated config template (`cad/weevil_leg_params.yaml`)
- New verification harness (`verification/test_rover_informed_profile.py`)
- Traceability + matrix updates linking new requirements to evidence
