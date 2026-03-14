# Requirement Namespace Policy (v0.1)

## Purpose
Normalize requirement identifiers to reduce audit friction and improve traceability consistency.

## Canonical prefixes
- `REQ-LOCO-xxx` : locomotion/mobility behavior
- `REQ-FOOT-xxx` : foot/anchoring subsystem
- `REQ-AUTO-xxx` : autonomy/state-machine/safety policy
- `REQ-ACT-xxx`  : actuation/transmission
- `REQ-DUST-xxx` : dust/sealing/reliability-in-dust
- `REQ-THERM-xxx`: thermal architecture and controls
- `REQ-PWR-xxx`  : power generation/storage/power budget policy
- `REQ-COMMS-xxx`: communications and telemetry continuity
- `REQ-CAD-xxx`  : CAD/export reproducibility and handoff artifacts
- `REQ-BURROW-xxx`: subsurface concept profile controls

## Legacy aliases
Some historical IDs remain in reports for continuity (for example `REQ-MOB-001/002`).
These map to canonical IDs via:
- `verification/requirement_aliases.csv`

## Rules
1. New requirements must use canonical prefixes above.
2. If a legacy ID is referenced, an alias mapping is mandatory.
3. Traceability checks should fail on unknown prefixes unless explicitly aliased.
