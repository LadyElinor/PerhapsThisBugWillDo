# Lunar Data Anchoring (Apollo/Simulant)

## Goal
Anchor reduced-order model parameters within empirically reported lunar ranges to improve scientific credibility.

## Initial anchoring policy
- Cohesion/friction/sinkage parameters must be selected within published lunar regolith or JSC-1A simulant ranges.
- Every parameter used in verification reports must cite a source family (Apollo mechanical properties, simulant campaign, or equivalent peer-reviewed terramechanics source).
- If parameter is heuristic, mark it explicitly as **assumed** and include expected uncertainty.

## Current status
- Partial: reduced-order parameters are plausible but not fully source-traced.
- Next: attach citation table in `results/sensitivity/parameter_sweep.md`.

## Required evidence table fields
- parameter_name
- nominal_value
- low_high_range
- source_type (Apollo | simulant | heuristic)
- citation
- confidence_level

## Acceptance threshold for v0.2 credibility
- 100% of parameters in core margin calculations have source or explicit heuristic tags.
- At least one benchmark comparison includes source-linked ranges.
