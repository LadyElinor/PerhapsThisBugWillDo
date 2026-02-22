# M1 – ODrive S1 Torque-First Bringup & Loop Closure

**Goal**  
Safely bring up ODrive S1 in torque mode, calibrate torque constant, close basic loops, and compare measured vs. sim within ±15%.

**Assumptions**
- ODrive S1 (firmware ≥ v0.6) + CubeMars AK70-style BLDC + APEX AE070 gearbox
- Encoder: integrated or external (≥4096 counts/rev)
- Power: 24–48 V bench supply (current-limited 10–20 A initial)
- Measurement: load cell / pron y brake at output shaft
- Laptop: USB connection + odrive-py / odrivetool installed

**Safety First – Startup Limits**
- Initial current limit: 10 A (motor & controller)
- Voltage limit: 48 V max
- Velocity limit: 200 deg/s (early tests)
- Always have emergency stop (power switch + physical brake)
- Monitor motor temp (IR thermometer or ODrive sensor) – abort >60 °C

## Bringup Progression

### Phase 1: Hardware & Electrical Checkout (Day 0–1)
- [ ] Mount motor to gearbox input (zero-backlash coupler, <0.1 mm runout)
- [ ] Connect phases U/V/W, encoder, power, USB
- [ ] Power on supply → ODrive LED green (no faults)
- [ ] Run `odrivetool` → connect → `odrv0.axis0` responds

### Phase 2: Open-Loop Torque Calibration (Day 1–2)

1. Set torque mode & safe limits

```python
# odrivetool commands
odrv0.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
# Wait for calibration complete (motor beeps, ~10–30 s)
odrv0.axis0.controller.config.control_mode = CONTROL_MODE_TORQUE
odrv0.axis0.controller.config.input_mode = INPUT_MODE_PASSTHROUGH
odrv0.axis0.motor.config.current_lim = 10.0  # A
odrv0.axis0.controller.config.vel_lim = 200.0  # deg/s
odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
```

2. Step current (manual or script)
- Command: `odrv0.axis0.controller.input_torque = 0.0` → measure baseline
- Ramp: 0 → 2 → 4 → 6 → 8 → 10 Nm (or max safe) in 1–2 Nm steps
- Hold each 5–10 s, record torque (load cell)

3. Pass gates
- Torque vs. current plot linear: R² > 0.95
- Measured Kt (Nm/A) within ±15% of expected (from motor spec or sim)
- No cogging/jitter at low torque

### Phase 3: Closed-Loop Torque Hold (Day 3–5)
- Add outer torque PID if needed (or rely on ODrive internal current loop)
- Command steps: 0 → 5 Nm → 0 → -5 Nm
- Pass gates
  - Settle time <100 ms
  - Overshoot <10%
  - Steady-state error <0.2 Nm under load

### Phase 4: Velocity & Position Ramp-Up (Day 6–10)
- Velocity mode

```python
odrv0.axis0.controller.config.control_mode = CONTROL_MODE_VELOCITY_CONTROL
odrv0.axis0.controller.input_vel = 50.0  # deg/s
```

- Ramp 0 → 100 → 0 deg/s, check smoothness
- Position mode

```python
odrv0.axis0.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL
odrv0.axis0.controller.config.input_mode = INPUT_MODE_TRAP_TRAJ
odrv0.axis0.trap_traj.config.vel_limit = 200.0
odrv0.axis0.trap_traj.config.accel_limit = 500.0
odrv0.axis0.controller.input_pos = 10.0  # deg
```

- 10° step: settle <50 ms, overshoot <5%
- Hold under 1–2 Nm hand load → error <2°

### Phase 5: Sim Comparison & Data Logging (Day 11+)
- Feed measured Kt, Kv, reflected inertia into sim config
- Run identical single-joint scenario (position step + preload)
- Compare trajectories (torque, position, velocity)
- Pass if peak torque, settle time, energy within ±15%

**Data Logging Template**  
See companion file: `M1_data_logging_template.csv`

## Acceptance Checklist
- [ ] Torque linearity R² > 0.95
- [ ] Measured Kt within ±15% of sim
- [ ] Position step settle <50 ms, overshoot <5%
- [ ] Hold 2 Nm external load with <2° error
- [ ] Thermal <60°C @ 5 min 50% torque
- [ ] Sim vs. measured within ±15% on key metrics

## Risk Mitigations
- Shaft mismatch → measure diameters before ordering
- Encoder noise → add shielding, lower gains
- Thermal runaway → start at 5 A limit, increase slowly
- ODrive faults → check `odrv0.axis0.error` frequently

**Data Logging Template File:** `M1_data_logging_template.csv` (companion artifact)
