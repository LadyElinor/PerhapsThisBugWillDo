# Verification Receipts Spine

This repo treats verification status as a derived artifact, not a hand-edited
narrative.

## Core rule

- harness execution writes receipts with hashes
- gate checks read receipts, not ad hoc report assumptions
- traceability status is derived from executed receipts
- divergence, stale paths, and undeclared gaps should fail verification

## Why this exists

The previous flow could look green while important harnesses had not actually
been executed under CI, and some report schemas were being interpreted too
naively. The receipts spine makes execution provenance explicit and gives the
repo one place to combine status honestly.

## Main pieces

- `verification/harness_manifest.yaml`
  - declares each harness, its command, expected report files, and pass schema
- `verification/receipts.py`
  - shared receipt/status logic
- `verification/run_verification_suite.py`
  - executes all declared harnesses and writes `verification/reports/receipts.json`
- `verification/run_gate_check.py --strict`
  - reads receipts and fails on unmet strict expectations
- `verification/sync_traceability.py`
  - derives `requirements_traceability.csv` status from receipts

## Status semantics

Typical statuses include:
- `pass`
- `expected-fail`
- `partial`
- `missing`
- `error`
- `drift`

`drift` is important: it means the observed result changed from the declared
expectation and needs conscious review rather than silent normalization.

## Governance intent

This spine does not validate the physics model. It validates execution honesty,
artifact integrity, and traceability coherence.

That distinction matters.
