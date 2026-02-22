# 72h Validation Matrix + Continue/Pivot/Stop Thresholds (2026-02-22)

## Test matrix

| Axis | Levels | Notes |
|---|---|---|
| Cleat candidate | CLEAT-C1, CLEAT-C2 | A/B comparison |
| Slope | 35°, 45° | Mission-relevant stress points |
| Repeats | 3 per candidate per slope (min) | 12 total runs minimum |
| Runtime per run | 120 s | Fixed |
| Load condition | Ballast-equivalent fixed | Same placement each run |
| Surface | Same prep protocol | Recondition between blocks |

## Derived metrics (candidate-level)
Compute per candidate at each slope, then pooled (35°+45°):
1. Mean slip ratio (%)
2. Mean current (A)
3. Progress efficiency (`mm progress / Wh`)
4. Structural integrity pass rate (no crack/delam failures)

## Decision thresholds
Reference baseline rule from sprint summary:
- Pivot if sustained climb slip >25% at 35–45° equivalent loading.
- Stop if inability to maintain positive climb progress at 35° in two independent repeats.

### Continue (GO with C1 baseline)
All must be true:
1. C1 pooled mean slip ratio <= 25%
2. C1 slip improvement vs C2 >= 15% relative (i.e., `(C2 - C1)/C2 >= 0.15`)
3. C1 mean current delta vs C2 <= +10% (no major electrical penalty)
4. C1 progress efficiency delta vs C2 >= 0% (non-inferior)
5. No structural failure in C1 across all valid runs

### Pivot (switch cleat baseline to C2 or tune/retest)
Any one trigger:
1. C1 pooled mean slip ratio > 25% but positive progress still maintained
2. C1 slip improvement vs C2 < 15%
3. C1 current penalty > +10% with no compensating efficiency gain
4. Any single critical C1 structural failure that invalidates confidence

### Stop (pause current architecture path)
Any one trigger:
1. Two independent repeats at 35° show non-positive progress (<=0 mm) despite cleat swap and same-day control retune attempt
2. Repeat hard stalls or overcurrent events prevent completion of minimum matrix safely
3. Structural integrity failure appears in both C1 and C2 at test load

## Statistical confidence gate (lightweight)
- Require at least 3 valid repeats/cell before final decision.
- If borderline (within ±3% of threshold), add 2 extra repeats/cell same day and recompute.
