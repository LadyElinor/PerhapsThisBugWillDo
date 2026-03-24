# CI Governance Checks

This repository includes governance-focused checks that run in CI via `make governance_artifacts`.

## Scope

These checks enforce that key governance artifacts are schema-valid, policy-consistent, and executable in pipeline form.

## Checks

1. **ICD contract catalog validation**
   - Command: `python verification/scripts/validate_icd_contract_catalog.py`
   - Verifies `icd/contract_catalog_v0.2.yaml` against `icd/contract_catalog.schema.json`
   - Enforces policy checks:
     - no duplicate message contracts
     - no duplicate field names inside a contract
     - numeric field ranges must satisfy `min <= max`

2. **Build-gate receipt template validation**
   - Command: `python verification/scripts/validate_build_gate_receipt_template.py`
   - Verifies template against `verification/data_schema/build_gate_receipt.schema.json`
   - Checks referenced traceability paths exist
   - Checks evidence paths are safe repo-relative paths

3. **Perception eval protocol bin coverage validation**
   - Command: `python verification/scripts/validate_perception_eval_protocol_bins.py`
   - Verifies `docs/PERCEPTION_EVAL_PROTOCOL_ILLUMINATION_TERRAIN_BINS_v0.1.md` contains required:
     - illumination bins (`I0..I3`)
     - terrain bins (`T0..T3`)
     - governance/acceptance markers (16-cell matrix, sample counts, stop-now recall, Bohmian untouched scope)

4. **NASA-JPL retry queue artifact validation**
   - Command: `python verification/scripts/check_nasa_jpl_retry_queue.py`
   - Verifies `analysis/nasa_jpl_retry_queue_prioritized.csv` and `.md` summary structure
   - Enforces headers, sort order, status/action consistency, and required markdown sections
   - Optional regeneration mode: `--rebuild`

## CI integration points

- `.github/workflows/ci.yml`
- `.github/workflows/ci-pr-gates.yml`
- `Makefile` target: `governance_artifacts`

## Local run

If `make` is available:

```bash
make governance_artifacts
```

Fallback (no `make`):

```bash
python verification/scripts/validate_icd_contract_catalog.py
python verification/scripts/validate_build_gate_receipt_template.py
python verification/scripts/validate_perception_eval_protocol_bins.py
python verification/scripts/check_nasa_jpl_retry_queue.py
```
