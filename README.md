# PerhapsThisBugWillDo 🪲🌙

**Weevil-Lunar** is a biomimetic robotics sandbox that treats locomotion as **constrained dynamical systems cartography**:

joint manifolds → reachable sets → contact constraints → mission feasibility.

This repo is the working lab notebook + executable scaffold for comparing arthropod-inspired morphologies under lunar regolith contact mechanics.

## What’s here

### Runnable analysis
- `results/GPT/Robotics/lunar_integrated_weevil_leg.py`
  - generates workspace/force/mission-feasibility outputs
- `results/GPT/Robotics/regolith_contact_model.py`
  - Bekker-Wong pressure–sinkage
  - Mohr-Coulomb shear envelope
  - preload + twist-settle + directional cleat gains (v0.3)
- `results/GPT/Robotics/weevil_lunar_tests.py`
  - slope/sinkage/anchoring gates
  - mare rescue profile generation

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

### 2) Run lunar integrated analysis
```bash
python results/GPT/Robotics/lunar_integrated_weevil_leg.py
```
Expected outputs:
- `results/GPT/Robotics/workspace_lunar_vs_earth.png`
- `results/GPT/Robotics/force_capacity_terrain.png`
- `results/GPT/Robotics/mission_feasibility_map.png`

### 3) Run Weevil-Lunar tests
```bash
python results/GPT/Robotics/weevil_lunar_tests.py
```
Expected outputs:
- `results/GPT/Robotics/weevil_lunar_test_results.md`
- `results/GPT/Robotics/mare_rescue_profile.md`

## Core idea

This project compares morphologies via:

(ROM constraints) × (actuation limits) × (contact dynamics) × (control policy)
→ accessible phase volume
→ reachable trajectories
→ mission role fit.

On the Moon, traction must come from **geometry + control**, not weight.

## v0.3 contact knobs (slope rescue)

In `regolith_contact_model.py`:
- `preload_normal`
- `twist_settle_gain`
- `cleat_gain_forward`
- `cleat_gain_lateral`
- `cleat_engage_threshold_preload`

These parameters drive directional traction envelopes and mare rescue feasibility.

## Current roadmap

1. Extend morphology harness (crab / ant / arachnid / beetle) into one unified evaluator.
2. Replace placeholder verification runs with hardware-in-the-loop data.
3. Tie all requirements to reproducible reports via traceability CSV.

## Repo hygiene
- `requirements.txt` is authoritative for Python deps.
- Keep generated outputs under their existing results folders.
- Never commit secrets/tokens.
