# MuJoCo Trace Harness Preflight

Status: active preflight note  
Scope: custom MuJoCo trace-harness work beyond `testspeed.exe` summary parsing

## Purpose

This note defines the environment checks required before attempting the next MuJoCo tranche:
- custom per-step state capture
- contact persistence by step
- slip trajectory extraction
- direct reaction/contact-force proxies where available

The repo already supports:
- MuJoCo model compilation via `compile.exe`
- rollout summary extraction via `testspeed.exe`

The repo does **not** yet support custom trace harness compilation or Python-driven per-step instrumentation without additional local tooling.

## Required capability for the next tranche

At least one of the following must be true:

1. Python MuJoCo binding is installed:
   - `pip install mujoco`

or

2. A usable C/C++ compiler toolchain is available locally:
   - MSVC Build Tools / `cl`
   - or another supported compiler such as `g++`

Without one of those capabilities, the repo cannot honestly proceed to custom per-step MuJoCo trace capture.

## Preflight script

Run:

```bash
python simulators/mujoco/toolchain_preflight.py
```

This reports:
- whether the local MuJoCo bundle exists
- whether `compile.exe`, `testspeed.exe`, and `mujoco.dll` are present
- whether Python `mujoco` is importable
- whether a compiler is visible on PATH
- whether any Visual Studio `cl.exe` candidates are visible in standard install roots
- the exact blocker state for custom trace-harness work

## Interpretation

### If `runtime.runtime_ready == true`
The repo can continue using compile-backed and `testspeed`-backed runtime paths.

### If `custom_trace_harness.custom_trace_ready == true`
The repo may proceed to a custom per-step MuJoCo trace harness tranche.

### If `custom_trace_harness.custom_trace_ready == false`
Do not begin custom trace-harness implementation work. First install either:
- Python `mujoco`, or
- a usable compiler toolchain

## Governance reminder

Even once the toolchain is ready, custom trace capture still increases comparative power, not validation status. It should improve visibility into contact/slip behavior, but it does not by itself close the findings in `DECISION_MEMO.md`.
