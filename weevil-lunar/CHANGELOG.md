# Changelog

## Unreleased
- Added gearbox allocation configuration set for comparative rover leg studies, including:
  - `uniform_ae070`
  - `tapered`
  - `hybrid_b`
  - synthetic midpoint `hybrid_a` using `apex_ae060_equiv_blend`
- Added reproducible allocation comparison runner:
  - `weevil-lunar/tools/compare_gearbox_allocations.py`
  - supports sweepable realism knobs (`--derate`, `--ankle-demand-mult`, `--slopes`)
  - supports `real_sim` evaluation mode and CSV outputs
- Added comparison result artifacts:
  - `weevil-lunar/results/comparisons/gearbox_comparison.csv`
  - `weevil-lunar/results/comparisons/gearbox_comparison_realism_tightened.csv`
  - `weevil-lunar/results/comparisons/gearbox_comparison_hybridA_derate055_ankle15_s35.csv`
  - `weevil-lunar/results/comparisons/gearbox_alloc_tapered_vs_uniform.md`
- Added current rover blueprint artifact:
  - `weevil-lunar/results/blueprints/lunar_weevil_blueprint_v0_4.png`
- Added candidate STEP tracking and APEX parameter manifests used by allocation configs:
  - `weevil-lunar/cad/lunar_weevil_step_candidates.md`
  - `cad_assets/manifests/lunar_weevil_candidates/*.json`

## v0.1.0-prealpha
- Added reproducible dependency files (`requirements.txt`, `requirements-lock.txt`).
- Added lint/test configuration (`pyproject.toml`, YAML/Markdown lint configs).
- Added unit tests for regolith/contact/margin checks and YAML contract validation.
- Added schema file for ICD contract shape.
- Portabilized FreeCAD export macro path handling.
- Added model-fidelity statement to system spec.
- Added sensitivity sweep + classical baseline comparison scripts and reports.
- Added multi-leg gait planner scaffold and dynamic-regime flag.
- Added demo notebook and seeded contributor issue list.
- Updated CI workflows to install deps, lint, run pytest+coverage, and run verification scripts.
- Added actuator/drive modeling appendix and drive-train sanity tests (MIT 2.12-aligned reduced-order checks).
- Added COTS interface map, profile IDs in export receipts, and CI verification for interface completeness.
