# Physics Toy Fork-Point Result (Negative, Mechanistic)
**Date:** 2026-02-15  
**Scope:** `results/reachability/physics/pilot_2026-02-14.csv` + `results/reachability/physics/exits_2026-02-14.csv`

## Claim (what the data supports)
In the current DSG-Ω physics toy regime, policy differences are primarily **barrier-crossing / time-to-first-crossing** effects, not **exit-connectivity** effects.  
Therefore, `-log(C_saddle)` (as currently measured) has weak leverage in `Lambda = ΔE_eff/T - log(C_saddle)`.

## Evidence
1. **Not early saturation (metastable tail exists).**
   - Late escapes among successes: `29 / 95 = 0.3053` (`escape_time > 1000`).
   - Flips from hit@1000=0 to hit@10000=1: `29`.

2. **Policies differ in crossing efficiency.**
   - Reachability improves with budget, strongest for tempered:
     - greedy: `0.283 -> 0.400`
     - anneal: `0.383 -> 0.500`
     - tempered: `0.433 -> 0.683`

3. **Exit-use distribution is policy-invariant under current mode partition.**
   - Accepted-only concentration:
     - greedy: top1 `0.164`, top3 `0.465`
     - anneal: top1 `0.148`, top3 `0.442`
     - tempered: top1 `0.171`, top3 `0.451`
   - Accessible-only concentration:
     - greedy: top1 `0.164`, top3 `0.465`
     - anneal: top1 `0.147`, top3 `0.437`
     - tempered: top1 `0.171`, top3 `0.452`
   - Weighted-by-acceptance gives the same pattern.
   - `unique_modes = 8` for all policies.

## Interpretation
- The toy exhibits activated behavior (late tail, budget dependence), so dynamics matter.
- But once trajectories reach the exit shell, policies sample nearly the same coarse exit manifold.
- Result: entropy/connectivity term is effectively policy-flat in this regime; collapse cannot improve via reweighting alone.

## Non-claims (explicit boundaries)
- This does **not** prove connectivity is never relevant.
- This does **not** falsify H3 globally; it is a regime-local negative result for the current toy + current exit coarse-graining.

## Smallest next experiment
Refine exit signature from `mode_id` to a higher-resolution channel key (e.g., `mode_id × energy_bin` or `mode_id × phase_bin`) and repeat concentration checks before altering Lambda form.

---

## Figure/Table spec for report
### Figure 1 — Budget reachability by policy (physics)
- Plot: reachability probability vs budget (log-x), one curve per policy.
- Purpose: show policy-separated crossing efficiency and late-tail lift.

### Figure 2 — Exit concentration bars (accepted vs accessible)
- Two panels: accepted-only and accessible-only.
- For each policy, show top1 and top3 mass.
- Purpose: show pathway-use invariance across policies under current mode partition.

### Table 1 — Fork-point diagnostics
Columns:
- `late_ratio`
- `flips_1000_to_10000`
- reachability at 1000 / 10000 by policy
- accepted top1/top3 by policy
- accessible top1/top3 by policy
- weighted top1/top3 by policy

Decision line in caption:
> Barrier-limited regime confirmed; connectivity term non-informative at current coarse-graining.
