# Weevil-Lunar Blueprint Package (v0.3)

This package defines a markdown-first, test-traceable blueprint for a lunar weevil-class mobility platform.

## State of the project
- **Status:** early-stage research/prototype package
- **Current model class:** quasi-static envelope + reduced-order contact assumptions
- **Validation status:** simulation-first; no hardware validation in-repo yet
- **Intended use:** design-space exploration, requirement shaping, and verification scaffolding

Governance-critical reading before making validation or performance claims:
- `DECISION_MEMO.md` — internal claim boundaries and validation-spend gate
- `docs/physics_redteam_report.md` — adversarial physics review underpinning the memo

## Quick reproducible benchmark
From repo root:

```bash
cd weevil-lunar
python verification/test_steep_slope_state_machine.py
python verification/test_rover_informed_profile.py
python verification/test_phase2_export_bundle.py
python verification/run_gate_check.py
```

Expected outputs are generated under `verification/reports/` as local working artifacts and CI artifacts, not canonical committed evidence.

## Included now
- `docs/system_spec.md`
- `docs/ops_playbook.md`
- `docs/rover_informed_build_plan.md`
- `docs/lunar_weevil_build_checklist.md`
- `docs/phase2_handoff_summary.md`
- `docs/physics_redteam_report.md`
- `specs/foot_anchoring_spec.md`
- `icd/software_icd.md`
- `icd/data_contracts.yaml`
- `verification/test_matrix.csv`
- `verification/requirements_traceability.csv`
- `verification/test_rover_informed_profile.py`
- `verification/test_phase2_cad_artifacts.py`
- `verification/test_phase2_export_bundle.py`
- `cad/Phase2_Templates.FCMacro`
- `cad/Phase2_SeedGeometry.FCMacro`
- `cad/Phase2_BuildAttempt1Geometry.FCMacro`
- `cad/Phase2_ViewCleanup.FCMacro`
- `cad/Phase2_Export.FCMacro`

## Source evidence used
- `results/GPT/Robotics/weevil_lunar_test_results.md` (generated local artifact, may be absent in a fresh clone)
- `results/GPT/Robotics/mare_rescue_profile.md` (generated local artifact, may be absent in a fresh clone)
- `results/GPT/Robotics/weevil_lunar_tests.py` (generated/local evidence snapshot, not canonical source, may be absent in a fresh clone)

## Project metadata
- CI workflow: `../.github/workflows/validate-and-benchmark.yml`
- License: not yet committed in this clone
- Citation: not yet committed in this clone

## Export receipt workflow (v0.4)
Use deterministic receipt generation for CAD handoff traceability:

```bash
python cad/scripts/generate_export_receipt.py --interface-version v0.4 --notes "v0.4 handoff refresh"
python verification/check_export_receipt.py --receipt cad/exports/latest/export_receipt_v0.4.json --max-age-days 7
```

Verification reports under `verification/reports/` are intentionally treated as generated working outputs. If durable evidence snapshots are needed, freeze them explicitly at a release or handoff rather than relying on mutable dev-run report files.

Canonical receipt artifacts:
- `cad/exports/latest/export_receipt_v0.4.json`
- `cad/exports/latest/export_receipt_latest.json`
- `cad/exports/receipt.schema.json`

## Next authoring targets
- mechanical/electrical ICD
- thermal, dust sealing, and actuation subsystem specs
- preliminary BOM and materials sheet
- dynamics-layer and HIL calibration milestones (roadmap doc not yet committed in this clone)
