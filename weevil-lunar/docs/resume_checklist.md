# Resume Checklist (Lunar-Weevil)

Use this checklist to restart work quickly with minimal context loss.

## 1) Sync and branch
```bash
git fetch origin
git checkout feature/rover-informed-upgrade
git pull --ff-only
```

## 2) Environment
```bash
cd weevil-lunar
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

## 3) Run baseline gates
```bash
make burrow_process
make bench_ingest
python verification/check_traceability_namespace.py
python verification/run_gate_check.py
```

Expected refreshed artifacts:
- `verification/reports/regolith_variant_schema_validation.{csv,md}`
- `verification/reports/regolith_burrow_threshold_sweep.{csv,md}`
- `verification/reports/regolith_variant_retrieval.{csv,md}`
- `verification/reports/minimal_hardware_ingest.{csv,md}`
- `verification/reports/traceability_namespace_check.{csv,md}`
- `verification/reports/gate_check.{csv,md}`

## 4) First docs to read
- `docs/agent_operating_mode.md`
- `docs/system_spec.md`
- `docs/requirements_namespace.md`
- `docs/bench_data_protocol.md`
- `docs/lunaops1_document_bundle_index_v0_1.md`

## 5) First high-value next actions
1. Replace heuristic threshold sweep scoring with physics-grounded model hook.
2. Add one real bench dataset (force/slip/sinkage fields populated) and re-run ingest.
3. Add regression trend checks for retrieval distance and gate drift.

## 6) Commit hygiene
- Keep scoped commits only.
- Separate process wiring, model/spec changes, and docs where practical.
