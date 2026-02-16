# Actuation Spec (v0.3)

## Purpose
Define actuator performance and transmission behavior required for low-g anchored locomotion.

## Requirements
- REQ-ACT-001: Actuators shall provide smooth torque delivery in stance phase.
- REQ-ACT-002: Transmission backlash and ripple shall remain below gait-stability limits.
- REQ-ACT-003: Screw-joint pitch and gearing shall support controlled force routing under anchoring.
- REQ-ACT-004: Actuators shall operate under vacuum-compatible tribology assumptions.

## Design notes
- Preferred: brushless motors + reduction with low backlash
- Screw joint pitch must be tunable by candidate set (e.g., low/mid/high)
- Include torque/thermal sensing for health-aware planning

## Verification
- Bench torque ripple/backlash characterization
- Stance push-off smoothness test (no force spikes above traction margin)
- Endurance run with dust-exposure proxy and torque trend monitoring
