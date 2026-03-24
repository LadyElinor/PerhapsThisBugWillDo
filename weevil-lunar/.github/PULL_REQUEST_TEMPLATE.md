## Summary
- What changed?
- Why now?

## Validation
- [ ] `python -m pytest --no-cov tests/test_governance_validators.py`
- [ ] `python scripts/run_governance_checks.py` (or `make governance_artifacts`)
- [ ] Relevant verification scripts/tests run for touched areas

## Governance impact
- [ ] ICD contracts updated (if interface changed)
- [ ] Build-gate receipt schema/template updated (if gate semantics changed)
- [ ] Perception protocol bins/thresholds reviewed (if perception policy changed)
- [ ] NASA-JPL retry queue logic/artifacts updated (if ingest prioritization changed)

## Threshold/policy changes
- [ ] No threshold/policy changes in this PR
- [ ] If yes, explain rationale and migration/waiver plan

## Artifacts
- List generated artifacts changed and regeneration command(s)

## Risk notes
- Key risks introduced + mitigations
