# PerhapsThisBugWillDo 🪲🌙

This workspace contains multiple projects.  
For lunar mobility work, **`weevil-lunar/` is the canonical package and entrypoint**.

## Start here (Lunar-Weevil)
- Package root: `weevil-lunar/`
- Primary docs:
  - `weevil-lunar/README.md`
  - `weevil-lunar/docs/system_spec.md`
  - `weevil-lunar/docs/modeling_assumptions.md`

## Quickstart
```bash
cd weevil-lunar
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
pytest
python verification/run_gate_check.py
```

## What this repo is (epistemic status)
- Pre-alpha research prototype
- Simulation-first design-space exploration and verification scaffolding
- Not a hardware-validated mobility performance claim

## Legacy paths
Some historical analysis scripts remain under `results/GPT/Robotics/` for provenance.
They are **legacy artifacts**, not the primary onboarding flow.
