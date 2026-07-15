# ODE Build Preflight

Status: active preflight note  
Scope: local Windows ODE build attempts for `weevil-lunar` comparative backend work

## Purpose

This note defines the environment checks required before attempting the next ODE tranche beyond placeholder receipts.

The repo already supports:
- shared ODE scenario/config scaffolds
- ODE receipt generation with explicit blocked-runtime provenance
- comparative backend tests that keep ODE marked `partial`

The repo does **not** yet support a reliable local ODE runtime-backed path on this machine.

## Required capability for the next tranche

A truthful ODE runtime tranche needs all of the following:

1. ODE source tree present locally
2. `premake4.exe` present in the ODE `build/` directory
3. MSVC Build Tools installed and usable through `vcvars64.bat`
4. A project generation path that modern headless tooling can actually consume

Today, the main blocker is not just compiler availability. It is the gap between:
- legacy ODE Premake output (`vs2008` / `.vcproj`)
- modern headless MSBuild expectations

## Preflight script

Run:

```bash
python simulators/ode/toolchain_preflight.py
```

This reports:
- whether the local ODE source tree exists
- whether `premake4.exe` and `premake4.lua` are present
- whether `vcvars64.bat` exists
- whether `cl.exe` becomes usable after `vcvars64` initialization
- which Premake actions are actually supported
- whether legacy generated files exist
- whether a modern headless-ready runtime path is honestly available

## Interpretation

### If `runtime_path.headless_runtime_ready == true`
A real headless ODE build attempt may proceed.

### If `runtime_path.headless_runtime_ready == false`
Do **not** present ODE as runtime-backed.
Keep ODE in `partial` status and record the blocker in receipts.

### Current expected blocker on this machine
The current likely state is:
- MSVC can be made available via `vcvars64.bat`
- Premake only exposes `vs2008`
- generated `.vcproj` files are legacy and not directly consumable by current headless MSBuild flow

## Governance reminder

Even if the build path clears later, ODE remains a skeptical contrast backend, not a validation engine. Runtime execution would increase comparative power and disagreement visibility, not close the findings in `DECISION_MEMO.md`.
