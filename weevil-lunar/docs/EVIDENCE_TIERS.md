# Evidence Tiers

## Why this exists
Prevent claim drift by separating implementation proof from physics inference.

## Tier A — Integration Evidence
Supports claims that the system/build/pipeline works as configured.

Examples:
- CAD receipts and interface completeness checks
- DAQ pipelines and run receipts
- Reproducibility scripts and artifact regeneration

## Tier B — Physics Evidence
Supports claims about measured behavior in tested regimes.

Examples:
- Calibrated traction/sinkage metrics
- Strategy ranking under controlled matrix
- Trend validation vs preload/soil changes

## Tier C — Mission Inference (Speculative)
Extrapolations from measured data toward lunar mission contexts.

Rules:
- Must be explicitly marked as extrapolation
- Must cite Tier A/B limits and assumptions
- Cannot be presented as validated performance

## Report banner template
Include at top of every report:
- `evidence_tier: A|B|C`
- `claim_scope:`
- `unsupported_claims:`

## Review rule
A report is incomplete if evidence tier is absent.
