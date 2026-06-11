# Traceability Sync Report

Status column is derived from executed receipts rather than hand-edited.

## Summary

- Requirements found in docs/specs: 38
- Rows in traceability CSV: 40
- Harnesses pending requirement linkage: 5
- Requirements with no traceability row: 0

## Pending linkage debt

The following harnesses emit useful receipts but still need explicit requirement
IDs in the traceability map:

- axis_orthogonality_sensitivity
- duty_cycle_cadence_envelope
- offplane_coupling_index
- offplane_impulse_recovery
- stance_phase_detection

## Interpretation

This report is a governance artifact. It should be regenerated from current
receipts and reviewed when harness mappings or expectations change.

The important rule is not the exact prose in this file, but that traceability
status stays derived from executed evidence rather than becoming a stale manual
spreadsheet.
