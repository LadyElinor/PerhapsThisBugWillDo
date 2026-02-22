# M1 Post-Mortem – Single-Joint De-Risk Review

**Date Completed:** [YYYY-MM-DD]  
**Joint Tested:** [Ankle / Knee]  
**Gearbox:** [e.g., APEX AE070 metric]  
**Motor:** [e.g., CubeMars AK70-10]  
**Controller:** [ODrive S1 / Titan Quad]

## Success Criteria Recap
- [ ] Torque linearity R² > 0.95
- [ ] Measured Kt within ±15% of sim
- [ ] Position step settle <50 ms, overshoot <5%
- [ ] Hold 2 Nm external load with <2° error
- [ ] Thermal <60°C @ 5 min 50% torque
- [ ] Sim vs. measured within ±15% on key metrics

## Results Summary
- Measured torque constant (Nm/A): [value] (sim: [value], diff: ±__%)
- Position loop settle time: [ms], overshoot: [%]
- Max hold load without slip: [Nm / deg error]
- Peak housing temp: [°C] @ [duty cycle]
- Key metrics drift (sim vs. measured):
  - Peak torque: ±__%
  - Settle time: ±__%
  - Energy per step: ±__%

## Lessons Learned / Surprises
- [e.g., Encoder noise higher than spec → added shielding]
- [e.g., Thermal rise faster than expected → need heatsink]
- [e.g., Kt measured 12% lower → possible calibration offset]

## Action Items for M2 (Single-Leg)
- [ ] Update sim config with measured Kt / inertia
- [ ] Adjust ankle demand mult based on real settle time
- [ ] Order remaining joints (AE070 knee, AE090 hip?)
- [ ] Design load cell mount for full-leg stand

## Data Artifacts
- Raw logs: [link to CSVs]
- Plots: [link to torque linearity, step response, sim overlay]

**Overall Outcome:** [PASS / PARTIAL / FAIL] → Proceed to [next milestone / rework]
