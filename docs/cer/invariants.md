# CER Telemetry invariants (v0.x)

These invariants are the “contract” for the CER-telemetry pipeline.
They are meant to prevent **silent drift**, confounds, and brittle metrics.

## Core invariants

### 1) Determinism (analysis)
**Claim:** Given the same input rows + config, computed tags and metrics are identical.

**Enforce by:**
- Avoid RNG for sampling; prefer stable sorts.
- If backoff/jitter is used for network calls, do **not** let it affect the *analysis* stage outputs.
- Persist `config` and `run_id` alongside outputs.

### 2) Monotonicity of gates
**Claim:** Tightening eligibility gates (e.g., `min_impressions` ↑) can only remove rows and shrink (or keep) totals.

**Enforce by:**
- Assert `eligible.length <= rowsAll.length`.
- If you compute `eligible(min=200)` and `eligible(min=400)` in the same run, assert the second set is a subset of the first.

### 3) Partition sanity
**Claim:** If you declare a partition (e.g., visibility bands), it must be disjoint and cover what you think it covers.

**Enforce by:**
- Assert each row maps to exactly one band.
- If overlaps are allowed for tags (e.g., `safetyEng` and `tokenPromo`), compute and report overlaps explicitly.

### 4) Denominator hygiene
**Claim:** No rates are computed on tiny/invalid denominators; no NaN/Inf.

**Enforce by:**
- Only compute rate metrics when `n >= min_gate` (or report null).
- Use safe division (`n===0 => null`) and `log1p` variants.
- Assert all produced rates are finite when non-null.

### 5) Provenance completeness
**Claim:** Every output row carries enough metadata to be auditable.

**Minimum required fields per row:**
- `run_id`
- `fetched_at`
- `source_endpoint` (where the row came from)
- `config_hash` (optional but recommended)

## Output requirements
- `meta.json` must include: `run_id`, `generated_at`, `config`, and block definitions.
- `summary.json`/`meta.json` should include: `n_raw`, `n_eligible`, and any overlap counts used.

## Notes
These invariants do **not** guarantee causal interpretation. They guarantee the measurement pipeline is stable and comparable enough that causal hypotheses can be debated honestly.
