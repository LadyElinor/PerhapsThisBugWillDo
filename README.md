# PerhapsThisBugWillDo 🪲🌙

**Weevil-Lunar** is a biomimetic robotics sandbox that treats locomotion as **constrained dynamical systems cartography**:

joint manifolds → reachable sets → contact constraints → mission feasibility.

This repo is the working lab notebook + executable scaffold for comparing arthropod-inspired morphologies under lunar regolith contact mechanics.

## What’s here

### Runnable analysis / package surface
- `weevil-lunar/models/lunar_integrated_weevil_leg.py`
  - reduced-order leg model for reachability + traction checks
- `weevil-lunar/models/contact/regolith_contact_model.py`
  - Bekker-Wong pressure–sinkage
  - Mohr-Coulomb shear envelope
  - preload + twist-settle + directional cleat gains (v0.3)
- `weevil-lunar/models/contact/morphology_harness.py`
  - shared morphology-variant evaluator (ant / beetle / arachnid / crab)
- `weevil-lunar/models/contact/weevil_lunar_tests.py`
  - slope/sinkage/anchoring gates
  - mare rescue profile generation

Generated artifacts (figures, CSVs, reports) for the contact analysis are
written to `results/GPT/Robotics/`.

### Blueprint package
- `weevil-lunar/`
  - system + subsystem specs
  - ICDs
  - verification matrix + traceability
  - test harnesses + gate reports

## Quickstart

### 1) Install dependencies
```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run reduced-order leg model
```bash
python weevil-lunar/models/lunar_integrated_weevil_leg.py
```
This prints sampled leg states and traction estimates from the current canonical model location under `weevil-lunar/models/`.

### 3) Run contact / morphology analysis
```bash
cd weevil-lunar
python -m models.contact.weevil_lunar_tests
python -m models.contact.morphology_harness
```
Outputs are written under `results/GPT/Robotics/` as generated working artifacts, for example:
- `weevil_lunar_test_results.md`
- `mare_rescue_profile.md`
- `morphology_tradeoff.csv`
- `lunar_morphology_tradeoff.md`

### 4) Run Weevil-Lunar verification package
```bash
cd weevil-lunar
python -m pytest verification/tests -q
python weevil-lunar/verification/benchmark_runner.py
python weevil-lunar/verification/check_benchmark_regression.py
```

## Core idea

This project compares morphologies via:

(ROM constraints) × (actuation limits) × (contact dynamics) × (control policy)
→ accessible phase volume
→ reachable trajectories
→ mission role fit.

On the Moon, traction must come from **geometry + control**, not weight.

## v0.3 contact knobs (slope rescue)

In `weevil-lunar/models/contact/regolith_contact_model.py`:
- `preload_normal`
- `twist_settle_gain`
- `cleat_gain_forward`
- `cleat_gain_lateral`
- `cleat_engage_threshold_preload`

These parameters drive directional traction envelopes and mare rescue feasibility.

## Current roadmap

1. Consolidate all model code under `weevil-lunar/models/` (done) and add
   lint/type checks to CI.
2. Replace placeholder verification runs with hardware-in-the-loop data.
3. Tie all requirements to reproducible reports via traceability CSV.

## Repo hygiene
- `requirements.txt` is authoritative for Python deps.
- All model code lives under `weevil-lunar/models/`; `results/GPT/Robotics/`
  holds generated artifacts (figures, CSVs, reports) and may be absent in a fresh clone until local runs create them.
- CI and most package-local commands assume execution from `weevil-lunar/` unless a path is explicitly repo-root-relative.
- Never commit secrets/tokens.
