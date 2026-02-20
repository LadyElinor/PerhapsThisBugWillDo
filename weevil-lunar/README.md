# Weevil-Lunar Blueprint Package

![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Status: Pre-Alpha Research Prototype](https://img.shields.io/badge/status-pre--alpha%20research%20prototype-orange)

Markdown-first, test-traceable blueprint for a lunar weevil-class mobility platform.

## State of the project
- **Status:** pre-alpha research prototype
- **Current model class:** quasi-static envelope + reduced-order contact assumptions
- **Validation status:** simulation-first; no hardware validation in-repo yet
- **Intended use:** design-space exploration, requirement shaping, and verification scaffolding

See also: `docs/modeling_assumptions.md` and `docs/system_spec.md`.

## Quick Start (30 seconds)
```bash
git clone https://github.com/LadyElinor/PerhapsThisBugWillDo.git
cd PerhapsThisBugWillDo/weevil-lunar
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
pytest
python verification/run_gate_check.py
```

## Verification and reproducibility
Core checks:
```bash
python verification/test_steep_slope_state_machine.py
python verification/test_rover_informed_profile.py
python verification/test_phase2_export_bundle.py
python verification/run_gate_check.py
```

Quality and contract checks:
```bash
black .
ruff check . --fix
yamllint .
```

## Included now
- `docs/system_spec.md`
- `specs/foot_anchoring_spec.md`
- `docs/ops_playbook.md`
- `docs/rover_informed_build_plan.md`
- `docs/lunar_weevil_build_checklist.md`
- `docs/phase2_handoff_summary.md`
- `docs/modeling_assumptions.md`
- `docs/public_roadmap_issues.md`
- `docs/lunar_data_anchoring.md`
- `icd/software_icd.md`
- `icd/data_contracts.yaml`
- `icd/data_contracts.schema.json`
- `verification/test_matrix.csv`
- `verification/requirements_traceability.csv`
- `verification/test_rover_informed_profile.py`
- `verification/test_phase2_cad_artifacts.py`
- `verification/test_phase2_export_bundle.py`
- `verification/sensitivity_sweep.py`
- `verification/benchmark_classical_models.py`
- `cad/Phase2_Templates.FCMacro`
- `cad/Phase2_SeedGeometry.FCMacro`
- `cad/Phase2_BuildAttempt1Geometry.FCMacro`
- `cad/Phase2_ViewCleanup.FCMacro`
- `cad/Phase2_Export.FCMacro`

## Export receipt workflow (v0.4)
Deterministic receipt generation for CAD handoff traceability:

```bash
python cad/scripts/generate_export_receipt.py --interface-version v0.4 --notes "v0.4 handoff refresh"
python verification/check_export_receipt.py --receipt cad/exports/latest/export_receipt_v0.4.json --max-age-days 7
```

Canonical receipt artifacts:
- `cad/exports/latest/export_receipt_v0.4.json`
- `cad/exports/latest/export_receipt_latest.json`
- `cad/exports/receipt.schema.json`

## Suggested first issues
See `docs/open_issues_seed.md`.

## License
MIT (`LICENSE`)
