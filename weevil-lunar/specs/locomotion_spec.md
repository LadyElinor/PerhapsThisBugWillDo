# Locomotion Spec (v0.3)

## Purpose
Define gait modes, stability targets, and slope behaviors for Weevil-Lunar mobility.

## Modes
- **Nominal:** quasi-static traverse on mild terrain
- **Steep-slope:** enforced anchoring sequence, reduced speed, higher duty factor
- **Recovery:** stuck escape / retreat behavior

## Requirements
- REQ-LOCO-001: Default gait shall be quasi-static with bounded slip.
- REQ-LOCO-002: System shall switch to steep-slope mode above slope threshold (default 25°).
- REQ-LOCO-003: Push-off shall be blocked unless anchoring criteria are satisfied in steep-slope mode.
- REQ-LOCO-004: Recovery mode shall support at least one-step retreat from failed foothold state.

## Control parameters (initial)
- duty_factor_nominal: 0.65
- duty_factor_steep: 0.80
- max_speed_nominal: configurable
- max_speed_steep: nominal * 0.5

## Verification
- Flat-bed low-slip traverse test
- Slope progression test up to 45° with directional margin checks
- Disturbance recovery test with bounded slip and no tip-over
