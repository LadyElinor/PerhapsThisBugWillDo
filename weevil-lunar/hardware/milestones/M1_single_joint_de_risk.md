# M1 – Single-Joint Hardware De-Risk

**Milestone Goal**  
Close torque/current/position loop on one joint with real hardware and compare measured performance vs. simulation within ±15%.

**Target Joint**  
Ankle (recommended first)
- Lowest torque demand → cheapest gearbox/motor
- Most sensitive to contact/settle dynamics → highest calibration value for regolith model
- If budget/timeline forces knee first → acceptable fallback

**Timeline Target**  
2–6 weeks from order placement (parts lead time dominant)

**Success Criteria**
1. Stable position loop (step response: settle <50 ms, overshoot <5%)
2. Torque linearity pass (R² > 0.95 across 20–80% range)
3. Thermal pass (5 min @ 50% continuous torque → housing <60°C)
4. Measured torque constant & reflected inertia within ±15% of STEP-derived / sim values
5. Data logged and committed (CSV + plots)

**Execution Card**

### 1. Parts Order (Minimum Viable Set)

| Item | Recommended Model / Spec | Qty | Supplier | Est. Cost | Lead Time | Notes / Alternatives |
|-------------------------------|---------------------------------------------------|-----|---------------------------|-----------|-----------|----------------------|
| Planetary Gearbox | APEX AE070 metric (50:1 ratio preferred) | 1 | APEX Dynamics / Motion Industries | $500–800 | 4–8 wk | AE050 fallback if budget tight |
| Brushless DC Motor | CubeMars AK70-10 (Kv ~100–150, integrated encoder) | 1 | CubeMars / RobotShop | $200–400 | 2–6 wk | Match input shaft dia/keyway |
| Motor Controller | ODrive S1 (single-axis) or Titan Quad channel | 1 | ODrive Robotics / Studica | $150–300 | 1–4 wk | CAN/USB, torque/velocity mode |
| Power Supply | 24–48V DC, 10–20A bench supply | 1 | Mean Well / Amazon | $50–100 | 1–5 days | Bench use only |
| Mounting Bracket / Coupler | Custom alum plate + zero-backlash shaft coupler | 1 set | SendCutSend / McMaster-Carr | $50–150 | 1–3 wk | PCD match gearbox flange |
| Fasteners & Misc | M5 SHCS, nyloc nuts, thread locker, wires | lot | McMaster-Carr | $30–80 | 3–7 days | — |

**Total est. cost:** $1,000–$2,000

**Action:** Place order this week → track lead times in checklist

### 2. Test Stand Build
- Base plate: 300×300 mm alum (1/2" thick)
- Mount gearbox to base, motor to gearbox input
- Add load cell or torque arm at output shaft for torque measurement
- Secure encoder if not integrated
- Wire controller, power, USB/CAN to laptop

### 3. Test Sequence & Acceptance Checks

**Day 1–2 (Mechanical & Electrical Checkout)**
- [ ] Mount & alignment: <0.1 mm runout (dial indicator)
- [ ] Open-loop spin: velocity command → smooth rotation, no binding
- [ ] Encoder feedback: position/velocity @ ≥100 Hz, resolution matches spec

**Day 3–7 (Torque & Position Loops)**
- Torque loop:
  - Apply stepped current (10–100% in 10% increments)
  - Measure output torque (load cell / pron y brake)
  - Plot current vs. torque → R² > 0.95
  - Measured torque constant (Nm/A) vs. sim value: ±15%
- Position loop:
  - Basic PID tuning (10° step response)
  - Settle time <50 ms, overshoot <5%
  - Hold under 1–2 Nm hand load → steady-state error <2°

**Day 8–10 (Thermal & Long-Run)**
- Run 5 min @ 50% continuous torque
- Measure housing temp (IR thermometer): <60°C
- Log current, torque, velocity, temp over time

**Day 11–14 (Sim Comparison & Data Logging)**
- Feed measured torque constant, inertia into sim config
- Re-run single-joint sim scenario (e.g., position step + preload)
- Compare: measured vs. sim torque/position trajectories
- Pass if key metrics (peak torque, settle time, energy) within ±15%

### 4. Data Logging Schema (CSV Format)

Create `m1_joint_test_data_YYYYMMDD.csv`

| timestamp_ms | command_type | command_value | measured_position_deg | measured_velocity_deg_s | measured_torque_Nm | current_A | temp_C | notes |
|--------------|--------------|---------------|------------------------|--------------------------|---------------------|-----------|--------|-------|
| 0 | position | 10.0 | ... | ... | ... | ... | ... | step start |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Plots to generate & commit:**
- Torque vs. current (linearity)
- Position step response
- Measured vs. sim torque/position overlay

### 5. Risk & Contingency
- Lead time delay → order AE070 + motor immediately
- Mismatch (shaft/keyway) → verify specs before shipping
- Controller issues → have Arduino fallback for basic PWM test
- Thermal fail → add heatsink/fan, lower duty cycle

**Milestone Owner:** [Your name/handle]  
**Success =** Measured constants within ±15% of sim + stable loops → proceed to single-leg stand

Commit location: `weevil-lunar/hardware/milestones/M1_single_joint_de_risk.md`
