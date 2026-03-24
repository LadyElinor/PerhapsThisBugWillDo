# Artifact Policy

Defines what generated artifacts are committed vs kept local-only.

## Commit (tracked, durable)

Commit generated artifacts when they are governance evidence or stable research outputs used by review/traceability:

- `analysis/nasa_jpl_retry_queue_prioritized.csv`
- `analysis/nasa_jpl_retry_queue_prioritized.md`
- `verification/reports/*.csv`
- `verification/reports/*.md`
- Schema files under `icd/` and `verification/data_schema/`
- Governance templates under `verification/templates/`

## Do not commit (ephemeral/local)

- cache files (`.pytest_cache/`, `.ruff_cache/`, `__pycache__/`)
- coverage outputs (`.coverage`, `htmlcov/`)
- local virtualenvs (`.venv/`, `venv/`)
- ad-hoc temp files/logs (`*.tmp`, `*.log`, scratch files)

## Regeneration rule

If a committed generated artifact drifts after running canonical generators/checks, commit both:
1. source/config change, and
2. regenerated artifact outputs.

## Review rule

Any PR that changes governance-critical generated outputs should include:
- command(s) used
- rationale for changes
- whether thresholds/policies changed
