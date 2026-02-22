# Model Assumptions Update — 2026-02-22 Design Sprint

## New realism sweep assumptions (applied today)
1. **Steep terrain included:** evaluate at **35° and 45° slope**.
2. **Higher ankle loading:** ankle demand multiplier sweep at **1.5 / 1.7 / 1.9**.
3. **Size-dependent gearbox derate** (replaces one-size global derate for stress runs):
   - AE090: **0.60**
   - AE070: **0.56**
   - AE060: **0.53**
   - AE050: **0.50**
4. **Energy/reachability pipeline unchanged** from `compare_gearbox_allocations.py` real-sim path to preserve comparability.

## Rationale
- Larger reducers generally keep more torque headroom under thermal and duty stress; smaller units are derated harder.
- 45° and high ankle multipliers represent explicit mission-edge realism checks requested at unpause.
- Maintaining the same energy/reachability model isolates impact of derate and loading assumptions.

## Interpretation rule for this sprint
- **Robustness metric:** minimum overall torque margin across all stress cases.
- **Efficiency metric:** mean energy per gait cycle.
- **Decision score:** `min_margin - 10 * mean_energy` (used only for ranking alternatives in this sprint).
