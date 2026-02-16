# Weevil-Lunar Ops Playbook (v0.3)

## Nominal traverse loop
1. Sense terrain patch and slope
2. Score footholds
3. Place feet and run settle/preload
4. If slope >25°, enforce twist-settle anchoring sequence
5. Confirm anchored state + traction margins
6. Execute push-off and advance COM
7. Monitor slip/thermal/torque health

## Steep-slope mode (>25°)
- Reduced speed and increased duty factor
- Push-off blocked unless anchored=true
- If directional margins below threshold:
  - increase preload (bounded)
  - retry twist-settle
  - replan foothold

## Stuck recovery
- Enter low-amplitude reverse-step pattern
- Shift to alternate foothold set
- If repeated failure: lower COM and retreat one body-length

## Safe posture
- Wide stance
- Low COM
- Minimize actuator thermal spikes

## Comms degraded mode
- Continue local waypoint plan with conservative gait
- Store telemetry and health snapshots for deferred uplink
