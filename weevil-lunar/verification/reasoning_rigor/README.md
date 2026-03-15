# Reasoning Rigor Checks (Competing Hypotheses + Uncertainty Ledger)

## Inputs
- `verification/templates/competing_hypotheses_matrix.csv`
- `verification/templates/uncertainty_ledger.csv`

## Run
```bash
python verification/scripts/check_competing_hypotheses.py
python verification/scripts/check_uncertainty_ledger.py
```

## Outputs
- `verification/reports/competing_hypotheses_check.{csv,md}`
- `verification/reports/uncertainty_ledger_check.csv`
- `verification/reports/uncertainty_ledger.md`

## Gate behavior
- Competing hypotheses check fails if an enforced risk has <2 distinct hypotheses or missing predicted-signature/disconfirming-test fields.
- Uncertainty ledger check fails if high-impact unknown items are unowned/unplanned or any ledger item is stale.
