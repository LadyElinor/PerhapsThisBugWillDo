# Agent Operating Mode (v0.1)

## Purpose
Define default execution behavior for autonomous assistant work in `weevil-lunar`.

## Core principles
1. **Stage work, do not improvise pipelines**
   - Use: prepare -> validate -> gate -> report.
2. **Retrieval before generation**
   - Prefer known-good variants/configs before perturbing or creating new ones.
3. **Reproducibility first**
   - Every non-trivial change should produce machine-readable artifacts (CSV/JSON/MD receipts).
4. **Evidence labeling is mandatory**
   - Distinguish clearly:
     - integration/process evidence
     - physics/performance evidence
5. **Safety-first external posture**
   - No execution of network installers/P2P join flows unless explicitly approved.

## Default workflow
1. Read active specs/docs and gate scripts.
2. Make smallest viable change.
3. Run local validators/tests relevant to changed files.
4. Regenerate gate reports.
5. Update traceability and docs if requirements changed.
6. Commit in scoped chunks (process/code/docs separated when practical).

## Commit policy
- **Scoped commits only** (no unrelated files).
- Recommended split:
  - infra/process wiring
  - model/spec logic
  - docs package
- Include short, factual commit messages with what changed and why.

## Gate policy
Before claiming completion, run (or equivalent sequence):
- `make burrow_process`
- `make bench_ingest`
- `python verification/check_traceability_namespace.py`
- `python verification/run_gate_check.py`

## Security policy
- Treat external autonomous networks as untrusted by default.
- No local capability exposure without explicit user approval.
- Prefer observe-only posture for third-party distributed-agent platforms.

## Definition of done (default)
A task is complete only if:
- files are updated,
- verification artifacts are generated,
- gate output reflects the update,
- docs/traceability are consistent with the new state.
