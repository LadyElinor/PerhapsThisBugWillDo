# Simulation Governance for Backend Integration

Status: active governance note  
Scope: MuJoCo and ODE integration under `weevil-lunar/`  
Authority: subordinate to `DECISION_MEMO.md`

## Purpose

This document defines how simulation backend work may be used inside `PerhapsThisBugWillDo` without upgrading exploratory results into unsupported validation claims.

It exists to keep three layers distinct:
- reduced-order exploratory models
- comparative embodied simulation backends
- real validation evidence

## Core rule

**Backend integration increases comparative power, not validation status.**

Adding MuJoCo or ODE does not by itself close the findings in `DECISION_MEMO.md`, does not justify hardware-validation spend, and does not convert simulator outputs into predictive lunar-contact evidence.

## Allowed uses

MuJoCo and ODE outputs are approved for:
- embodied comparison against the reduced-order scaffold
- sensitivity analysis across scenario definitions
- backend disagreement detection
- solver-family contrast
- identifying which conclusions disappear under richer embodiment
- generating structured receipts and reproducible scenario artifacts

## Disallowed uses

Until the validation-spend gate in `DECISION_MEMO.md` is green, backend outputs must not be used as support for claims such as:
- predictive lunar sinkage realism
- validated Moon-vs-Earth performance (even where simplified gravity-coupled load paths now exist)
- physically grounded traction margins from free gain knobs
- design readiness for hardware-validation spend
- field-ready slope capability

## Evidence labels

All simulation artifacts should use one of the following labels:

- `exploratory`: toy or reduced-order, assumption-heavy output
- `comparative`: cross-backend or scenario-comparison output, still non-validating
- `backend-consistent`: multiple backends agree qualitatively under the same scenario contract
- `validated`: reserved for evidence that passes the repo’s validation-spend gate and subsequent reality-contact criteria

`validated` should not be used by simulator-only outputs.

## Scenario discipline

All new simulation backends must consume a shared scenario contract.

Scenario definitions must:
- be engine-agnostic
- name gravity, mass, stance, preload, and load-path assumptions explicitly
- record free or nonphysical assumptions in receipts
- avoid hidden backend-specific parameter injection

## Metric discipline

Common metrics are for comparison, not false equivalence.

If a backend cannot produce a metric directly:
- mark it unavailable in structured form
- do not fabricate a proxy silently
- do not present unavailable metrics as if they were comparable

## Receipt discipline

Each backend run must emit a receipt capturing:
- backend name
- engine version
- scenario id
- model artifact path and hash
- parameter hash
- metrics artifact path
- warnings and assumption notes
- status

Receipts are required because simulator prestige should not outrun traceability.

Current Finding 2 note:
- load-path semantics are now explicit in scenario and receipt contracts
- this improves comparative honesty and testability
- it does not by itself close the gravity-coupling finding or authorize validated Moon-vs-Earth claims

## Backend roles

### Reduced-order scaffold
Use for:
- cheap sweeps
- assumption mapping
- negative-use documentation

### MuJoCo
Use for:
- primary embodied simulation layer
- multibody contact comparison
- testing whether toy conclusions survive richer embodiment

### ODE
Use for:
- solver-family contrast
- rigid-body baseline comparison
- disagreement detection against MuJoCo and the reduced-order scaffold

Current implementation note:
- local ODE source and build tooling are present
- MSVC can be activated locally via `vcvars64.bat`
- however, the currently verified Windows build surface is still legacy-Premake-driven (`vs2008` / `.vcproj`)
- until that build-surface incompatibility is cleared, ODE outputs must remain explicitly marked as blocked-runtime `partial` artifacts rather than runtime-backed backend evidence

## Verification posture

Backend integration should enter the verification spine carefully.

Safe early uses:
- scenario reproducibility
- receipt integrity
- backend parity smoke tests
- disagreement flags
- build-preflight reporting that records toolchain and project-format blockers without overstating runtime readiness

Unsafe early uses:
- mapping simulator passes directly to strong mission-capability requirements
- treating backend agreement as validation closure

## Bottom line

Use simulation backends to make the repo more honest, more comparative, and more falsifier-aware.

Do not use them to smuggle in stronger claims than the current model and evidence base can support.
