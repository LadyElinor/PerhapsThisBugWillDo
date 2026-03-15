# Verification Copilot (v0.1)

Automated consistency scanner for:
- requirements declared in `specs/*.md` and `docs/*.md`
- `verification/requirements_traceability.csv`
- report artifact paths referenced by traceability rows

## Run
```bash
python verification/copilot/run_copilot.py --stale-days 14
```

With explicit suppression policy:
```bash
python verification/copilot/run_copilot.py --stale-days 14 --suppressions verification/copilot/suppressions.yaml
```

## Outputs
- `verification/reports/copilot_findings.csv`
- `verification/reports/copilot_findings.md`
- `verification/reports/copilot_status.csv`
- `verification/reports/copilot_summary.json`
- `verification/reports/copilot_trend_history.csv`
- `verification/reports/copilot_trend_check.{csv,md}`

## What it flags
- missing requirement mappings
- traceability orphans (IDs not found in active specs/docs)
- missing report artifacts
- weak status rows (`fail`, `partial`, etc.)
- stale reports older than threshold

## Weighted scoring
Severity weights:
- high = 5
- medium = 2
- low = 1

Copilot status is pass/fail against `--max-weighted-score`.
Trend check compares current run against previous sample and fails on spike thresholds.
