# LunaOps-1 Executive Brief (v0.1)

## Decision Summary
**Recommend advancing LunaOps-1** as a low-risk, high-utility lunar operations rover for early Starship surface missions.

Why this is selection-friendly:
- Proven mobility architecture (6-wheel rocker-bogie class)
- Teleop-first with bounded autonomy (lower certification risk)
- Clear operational value from mission day 1
- Conservative mass/power/thermal posture

## Mission Value (Immediate)
1. Landing-zone inspection after touchdown
2. Route scouting and hazard mapping
3. Cargo-zone logistics support
4. Local comms/situational awareness relay

## High-Level Configuration
- Mobility: 6-wheel rocker-bogie
- Control: teleop-first + assisted waypoint autonomy
- Power: solar + battery with strict reserve policy
- Payload: ops/safety sensing (nav/haz/thermal)

## Preliminary Program Envelope
- Dry mass target: ~67 kg class (55-75 kg envelope)
- Sortie role: short/medium traverses near mission assets
- Safety doctrine: hazard-stop, safe posture, return-home policies

## Why Not Lead with Novel Burrowing
For first flight-likelihood, baseline should prioritize reliability and integration certainty.
Crover-like subsurface scouting remains valuable but should be a **later module path** after baseline ops rover validation.

## Risks & Controls (Top 3)
- Dust wear/ingress -> hardened sealing + wear covers + inspections
- Energy shortfall under derates -> reserve floors + conservative sortie planning
- Thermal excursions -> WEB-style insulation/heater control + ops constraints

## 90-Day Decision Gate Plan
- Days 1-30: subsystem verification
- Days 31-60: integrated analog testing
- Days 61-90: mission rehearsal + fault injection + acceptance checks

## Recommendation
Proceed to PDR baseline with LunaOps-1 and maintain a parallel, non-blocking roadmap for optional subsurface scout add-on.
