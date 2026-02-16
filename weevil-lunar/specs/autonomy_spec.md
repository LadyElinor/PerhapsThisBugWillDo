# Autonomy Spec (v0.3)

## Purpose
Define onboard autonomy behaviors for delayed-communication lunar operations.

## Requirements
- REQ-AUTO-001: Foothold scoring shall run onboard from local terrain estimates.
- REQ-AUTO-002: Planner shall enforce anchoring-before-push in steep-slope mode.
- REQ-AUTO-003: Planner shall adapt gait/footholds on slip and margin violations.
- REQ-AUTO-004: Health-aware planning shall reduce risk when torque/thermal margins degrade.
- REQ-AUTO-005: System shall provide safe posture and recovery policy under comm delay/dropout.

## Core policies
- Slip response: reduce tangential demand, increase preload (bounded), re-anchor, replan
- Margin response: if downslope<1.05 or lateral<1.20, block push-off
- Fault response: enter recovery mode and attempt controlled retreat

## Verification
- Latency/dropout simulation with waypoint completion criteria
- Fault injection (degraded leg/joint model) with graceful degradation checks
