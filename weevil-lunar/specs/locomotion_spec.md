# Locomotion Spec (v0.3)

## Purpose
Define gait modes, stability targets, and slope behaviors for Weevil-Lunar mobility.

## Modes
- **Nominal:** quasi-static traverse on mild terrain
- **Steep-slope:** enforced anchoring sequence, reduced speed, higher duty factor
- **Subsurface-burrow (new):** low-disturbance penetration/translation in loose granular media using shape-coupled propulsion and bounded substrate disturbance
- **Recovery:** stuck escape / retreat behavior

## Requirements
- REQ-LOCO-001: Default gait shall be quasi-static with bounded slip.
- REQ-LOCO-002: System shall switch to steep-slope mode above slope threshold (default 25°).
- REQ-LOCO-003: Push-off shall be blocked unless anchoring criteria are satisfied in steep-slope mode.
- REQ-LOCO-004: Recovery mode shall support at least one-step retreat from failed foothold state.
- REQ-LOCO-005: Controller shall support a virtual rocker-bogie coordination profile to reduce body pitch/roll during uneven contact.
- REQ-LOCO-006: Mobility controller shall enforce a hard tilt safety cap of 30° (warn at 25°) during autonomous traverse.
- REQ-LOCO-007: Subsurface mode shall support explicit phase separation: entry/submerging, in-medium translation, and resurfacing.
- REQ-LOCO-008: Subsurface mode shall maintain a bounded disturbance index (to avoid large radial-collapse-style media failure) against a configurable mission threshold.
- REQ-LOCO-009: Burrowing tip geometry shall be wedge/shovel-class or equivalent low-drag profile for granular penetration.

## Control parameters (initial)
- duty_factor_nominal: 0.65
- duty_factor_steep: 0.80
- max_speed_nominal: configurable
- max_speed_steep: nominal * 0.5

## Verification
- Flat-bed low-slip traverse test
- Slope progression test up to 45° with directional margin checks
- Disturbance recovery test with bounded slip and no tip-over
- Subsurface phase test: entry -> in-medium translation -> resurfacing with completion criteria per phase
- Disturbance-budget test: compare local void/collapse signature to configured threshold in representative simulant bins
