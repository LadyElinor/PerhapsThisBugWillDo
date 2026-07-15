# Simulation Backend Integration Roadmap (MuJoCo First, ODE Second)

Status: proposed roadmap  
Scope: integrate MuJoCo and ODE into `PerhapsThisBugWillDo/weevil-lunar/` as comparative simulation backends  
Intent: strengthen embodiment checks and backend-comparison discipline without overstating validation status

## 1. Purpose

This roadmap turns the current recommendation into a repo-ready execution plan:

- **MuJoCo first** for embodied modern simulation
- **ODE second** for skeptical solver contrast
- **shared scenario / metrics / receipts spine before ambitious modeling**
- **treat both as comparative evidence layers, not validation closure**

This plan is governed by `weevil-lunar/DECISION_MEMO.md`.

Nothing in this roadmap should be interpreted as permission to upgrade the current scaffold into a predictive lunar-contact claim set. The goal is to build stronger comparative simulation infrastructure, not to bypass Findings 1–3.

## 2. Integration principles

### 2.1 What these backends are for

MuJoCo and ODE are being added to support:
- embodied multibody comparison against the reduced-order scaffold
- scenario reproducibility under a shared contract
- backend disagreement detection
- solver-sensitivity analysis
- better identification of which outputs are fragile, assumption-sensitive, or backend-specific

### 2.2 What these backends are **not** for

Until the validation-spend gate in `DECISION_MEMO.md` is green, these backends must **not** be used to claim:
- predictive lunar sinkage realism
- validated Moon-vs-Earth comparative performance
- physically grounded traction margins from free gain knobs
- readiness for hardware-validation spend

### 2.3 Backend roles

#### Reduced-order scaffold
Current role:
- cheap design-space exploration
- assumption surfacing
- parameter sweeps
- governance scaffolding

#### MuJoCo backend
Intended role:
- primary embodied simulation backend
- first serious multibody contact comparison layer
- place to test whether toy conclusions survive richer embodiment

#### ODE backend
Intended role:
- secondary comparison backend
- solver-family contrast layer
- stress test for backend fragility and conclusion stability

## 3. Target repository structure

Create a simulation backend layer under `weevil-lunar/`.

```text
weevil-lunar/
  docs/
    simulation_backend_integration_roadmap.md
    simulation_governance.md
  simulators/
    common/
      __init__.py
      scenario_schema.py
      metrics.py
      receipts.py
      artifact_paths.py
    mujoco/
      __init__.py
      runner.py
      adapters.py
      extract_metrics.py
      models/
        single_leg_basic.xml
        single_leg_incline.xml
    ode/
      __init__.py
      runner.py
      adapters.py
      extract_metrics.py
      configs/
        single_leg_basic.yaml
        single_leg_incline.yaml
  verification/
    backends/
      test_backend_metric_contracts.py
      test_backend_parity_smoke.py
      test_backend_disagreement_flags.py
```

Optional future expansion:

```text
  results/
    simulation/
      mujoco/
      ode/
      parity/
```

## 4. Shared contracts to build before engine ambition

## 4.1 Scenario schema

Create `weevil-lunar/simulators/common/scenario_schema.py`.

The schema should define one canonical scenario object used by all backends.

Minimum fields:
- `scenario_id`
- `backend`
- `body_mass_kg`
- `gravity_m_s2`
- `leg_count`
- `stance_legs`
- `foot_radius_m`
- `foot_geometry_kind`
- `terrain_class`
- `slope_deg`
- `preload_normal_n`
- `twist_settle_gain_assumed`
- `cleat_gain_forward_assumed`
- `cleat_gain_lateral_assumed`
- `control_mode`
- `maneuver`
- `duration_s`
- `timestep_s`
- `notes`

Design rule:
- scenario definitions must be engine-agnostic
- backend adapters may translate them, but may not silently add new physics assumptions without recording them in receipts

## 4.2 Metrics contract

Create `weevil-lunar/simulators/common/metrics.py`.

Minimum common metrics:
- `completed`
- `failure_mode`
- `normal_reaction_n`
- `tangential_reaction_n`
- `slip_distance_m`
- `slip_velocity_m_s`
- `stance_stable_duration_s`
- `peak_body_pitch_deg`
- `peak_body_roll_deg`
- `foot_penetration_proxy_m`
- `control_effort_proxy`
- `anchor_state_confirmed`
- `notes`

Rule:
- if a backend cannot natively produce a metric, mark it as unavailable in a structured way rather than faking comparability

## 4.3 Receipt contract

Create `weevil-lunar/simulators/common/receipts.py`.

Each simulation run should emit a receipt containing:
- `backend`
- `scenario_id`
- `generated_at`
- `model_artifact`
- `model_hash`
- `parameter_hash`
- `code_commit`
- `engine_version`
- `metrics_path`
- `status`
- `warnings`
- `assumption_notes`

Receipt statuses should align with the existing repo governance style:
- `pass`
- `partial`
- `missing`
- `error`
- `drift`

## 5. Phase plan

## Phase 0 — Governance and seams first

### Objective
Create the rules and file structure that keep the backend work honest.

### Deliverables
- `docs/simulation_governance.md`
- `simulators/common/scenario_schema.py`
- `simulators/common/metrics.py`
- `simulators/common/receipts.py`
- `simulators/common/artifact_paths.py`

### Required decisions
- how scenario IDs are named
- where backend artifacts live
- how unavailable metrics are encoded
- which results are allowed into verification receipts vs exploratory reports only

### Exit criteria
- a shared scenario object exists
- a shared metric dictionary/schema exists
- a simulation receipt format exists
- the governance doc explicitly states that simulator integration does not close Findings 1–3

---

## Phase 1 — MuJoCo single-leg embodiment bootstrap

### Objective
Bring up a narrow, controlled MuJoCo integration for one leg and one terrain surrogate.

### Why this comes first
MuJoCo is the most useful first embodied backend because it offers:
- strong articulated-body simulation
- good model description ergonomics
- practical contact experimentation
- a cleaner path to future locomotion studies

### Deliverables
- `simulators/mujoco/runner.py`
- `simulators/mujoco/adapters.py`
- `simulators/mujoco/extract_metrics.py`
- `simulators/mujoco/models/single_leg_basic.xml`
- `simulators/mujoco/models/single_leg_incline.xml`

### Initial scenarios
1. flat-ground preload hold
2. tangential push / slip onset
3. incline hold at 15°
4. incline hold at 25°
5. incline hold at 35°
6. incline hold at 45°

### Exit criteria
- MuJoCo can run a canonical scenario from the shared schema
- metrics extraction works for at least the basic common metrics
- one receipt is written per run
- a smoke report comparing reduced-order vs MuJoCo exists for incline hold

---

## Phase 2 — MuJoCo comparative profile layer

### Objective
Expand MuJoCo from smoke test to comparative analysis tool.

### Deliverables
- scenario sweep support in `simulators/mujoco/runner.py`
- stable artifact naming under `results/simulation/mujoco/`
- markdown or CSV summaries for:
  - preload sweeps
  - slope sweeps
  - foot-radius sweeps

### Candidate scenarios
- `single_leg_incline_hold`
- `single_leg_slip_onset`
- `single_leg_push_off_gate`
- `single_leg_repeated_contact_cycle`

### Exit criteria
- MuJoCo outputs can be compared across scenario sweeps reproducibly
- receipt artifacts capture parameter provenance
- backend-specific assumptions are recorded in receipts and not hidden in prose

---

## Phase 3 — ODE baseline backend

### Objective
Add a second dynamics engine to expose solver-family sensitivity and disagreement.

### Why ODE is second
ODE should not be treated as the main future platform. Its primary value here is:
- source-level transparency
- classic iterative rigid-body contact baseline
- contrast against MuJoCo and the reduced-order scaffold

### Deliverables
- `simulators/ode/runner.py`
- `simulators/ode/adapters.py`
- `simulators/ode/extract_metrics.py`
- `simulators/ode/configs/single_leg_basic.yaml`
- `simulators/ode/configs/single_leg_incline.yaml`

### Scope constraint
Keep ODE intentionally narrow:
- rigid contact baseline only
- simple terrain / incline scenarios only
- no attempt at elaborate ODE-only model sophistication in the first pass

### Exit criteria
- ODE can execute the same canonical scenario IDs used by MuJoCo
- ODE emits the same receipt structure
- at least one reduced-order / MuJoCo / ODE comparison can be generated from one scenario definition family

### Current verified status
- ODE source tree is present locally under `0sourceforge/ode-0.11.1/ode-0.11.1`
- MSVC Build Tools are usable after `vcvars64.bat` initialization
- legacy project files were generated successfully via Premake (`build/vs2008/ode.sln`, `ode.vcproj`, `tests.vcproj`)
- ODE preflight now exists at `simulators/ode/toolchain_preflight.py`
- current blocker is build-surface compatibility, not missing source or missing compiler
- bundled Premake only exposes legacy Visual Studio generation up to `vs2008`
- current headless MSBuild flow does not yet yield a truthful runtime-backed ODE path from those legacy project files

### Current governance implication
Until the legacy-project-format boundary is cleared, ODE remains a receipted comparative scaffold with explicit blocked-runtime provenance, not a runtime-backed contrast backend.

---

## Phase 4 — Backend parity harness

### Objective
Create explicit cross-backend comparisons under the same scenario contract.

### Deliverables
- `verification/backends/test_backend_metric_contracts.py`
- `verification/backends/test_backend_parity_smoke.py`
- `verification/backends/test_backend_disagreement_flags.py`

### Required parity scenarios
1. nominal flat stance
2. 15° incline hold
3. 25° incline hold
4. 35° incline hold
5. 45° incline hold
6. preload sweep
7. foot-radius sweep

### Parity outputs should answer
- where all backends agree qualitatively
- where only the reduced-order model passes
- where MuJoCo and ODE disagree materially
- where results are highly sensitive to assumptions or solver behavior

### Exit criteria
- one parity report exists for incline-hold scenarios
- disagreement is reported explicitly, not normalized away
- backend drift produces `drift` or equivalent flagging behavior

---

## Phase 5 — Verification spine integration

### Objective
Connect backend runs into the repo’s existing receipts-first verification style.

### Deliverables
- add backend harness declarations to `verification/harness_manifest.yaml`
- add backend report contracts to receipt processing
- add traceability mapping only for claims that are actually earned

### Important constraint
Do **not** immediately map MuJoCo or ODE outputs to strong requirement claims such as:
- “45° slope capability validated”
- “traction margins proven”
- “sinkage limit predictive”

Use them first for weaker, honest categories such as:
- comparative support
- backend reproducibility
- disagreement detection
- scenario completion under stated assumptions

### Exit criteria
- simulation backend harnesses show up in receipts
- backend reports can fail honestly
- no inflated requirement traceability is introduced prematurely

---

## Phase 6 — Reality-coupling work aimed at Findings 1–3

### Objective
Use the backend infrastructure to help close the known model weaknesses rather than just decorate them.

### Workstream A — Finding 1 (`k_phi` / sinkage units)
Deliverables:
- documented parameter derivation note
- explicit unit tests for pressure-sinkage handling
- backend comparison report showing how sinkage proxies behave across foot sizes

### Workstream B — Finding 2 (gravity path)
Deliverables:
- one canonical load-derivation path from `mass * g / stance_distribution`
- tests proving gravity changes arise from mechanism, not scenario labeling
- shared scenario support for gravity/body-mass dependence across all backends

### Workstream C — Finding 3 (`cleat_gain` free multiplier)
Deliverables:
- bounded or replaced traction-amplification assumptions
- explicit assumption notes when gains remain nonphysical placeholders
- tests that distinguish geometry-derived behavior from free-gain behavior

### Exit criteria
- backend work helps clarify the findings
- backend work does not obscure the findings
- validation-spend gate remains controlled by the memo, not by simulator prestige

## 6. Concrete task tickets

The following tickets are sized for direct repo execution.

### Ticket SIM-001 — Add simulation governance doc
**Goal:** create backend-integration claim boundaries.  
**Files:**
- `weevil-lunar/docs/simulation_governance.md`

**Tasks:**
- summarize allowed and disallowed uses of MuJoCo/ODE outputs
- state that backend agreement is not hardware validation
- define terminology for exploratory vs comparative vs stronger evidence

**Done when:** governance doc exists and cites `DECISION_MEMO.md` explicitly.

---

### Ticket SIM-002 — Create shared scenario schema
**Goal:** prevent backend divergence at the input layer.  
**Files:**
- `weevil-lunar/simulators/common/scenario_schema.py`

**Tasks:**
- define canonical scenario dataclass or typed schema
- add validation for required fields
- support serialization to JSON/YAML for receipts

**Done when:** one scenario object can be loaded and passed to future backends unchanged.

---

### Ticket SIM-003 — Create shared metrics contract
**Goal:** make cross-backend outputs comparable.  
**Files:**
- `weevil-lunar/simulators/common/metrics.py`

**Tasks:**
- define common metrics schema
- define unavailable/unsupported metric encoding
- add normalization helpers for comparison reports

**Done when:** backends can emit a common result payload without inventing incompatible field names.

---

### Ticket SIM-004 — Create simulation receipt writer
**Goal:** align backend runs with the repo’s receipts-first verification style.  
**Files:**
- `weevil-lunar/simulators/common/receipts.py`
- `weevil-lunar/simulators/common/artifact_paths.py`

**Tasks:**
- define receipt schema
- implement hash capture for model/config artifacts
- write receipt JSON to stable output location

**Done when:** one fake or stub run can emit a receipt with hashes and metadata.

---

### Ticket SIM-005 — MuJoCo single-leg bootstrap
**Goal:** first embodied backend run.  
**Files:**
- `weevil-lunar/simulators/mujoco/runner.py`
- `weevil-lunar/simulators/mujoco/adapters.py`
- `weevil-lunar/simulators/mujoco/models/single_leg_basic.xml`

**Tasks:**
- load a canonical scenario
- translate it into a minimal MuJoCo model/config
- run flat-ground preload hold
- emit metrics + receipt

**Done when:** one MuJoCo run completes from the shared scenario contract.

---

### Ticket SIM-006 — MuJoCo incline-hold profile
**Goal:** first meaningful parity scenario.  
**Files:**
- `weevil-lunar/simulators/mujoco/models/single_leg_incline.xml`
- `weevil-lunar/simulators/mujoco/extract_metrics.py`

**Tasks:**
- implement incline scenarios at 15°, 25°, 35°, 45°
- extract stance stability, slip, and reaction metrics
- write scenario-specific artifacts

**Done when:** incline-hold scenarios produce comparable outputs and receipts.

---

### Ticket SIM-007 — ODE minimal baseline backend
**Goal:** bring up the skeptical comparison engine.  
**Files:**
- `weevil-lunar/simulators/ode/runner.py`
- `weevil-lunar/simulators/ode/adapters.py`
- `weevil-lunar/simulators/ode/configs/single_leg_basic.yaml`

**Tasks:**
- run a simple flat-ground or incline case in ODE
- emit the common metric shape
- emit the common receipt shape

**Done when:** one scenario family runs in ODE with the shared contracts.

**Current note:** shared contracts and blocked-runtime preflight are in place, but the headless runtime path is still blocked by legacy project-format incompatibility.

---

### Ticket SIM-008 — Backend parity smoke test
**Goal:** compare reduced-order, MuJoCo, and ODE under one scenario family.  
**Files:**
- `weevil-lunar/verification/backends/test_backend_parity_smoke.py`

**Tasks:**
- run the same incline-hold scenarios across all backends
- check metric contract compatibility
- flag qualitative disagreement

**Done when:** one parity test can fail honestly when a backend diverges materially.

---

### Ticket SIM-009 — Backend disagreement report
**Goal:** make disagreement visible instead of smoothed over.  
**Files:**
- `weevil-lunar/verification/backends/test_backend_disagreement_flags.py`
- optional report generator under `simulators/common/`

**Tasks:**
- define what counts as disagreement vs acceptable spread
- mark disagreement as warning or drift
- generate a comparison summary artifact

**Done when:** backend disagreement is reported explicitly in a reusable format.

---

### Ticket SIM-010 — Receipt-spine integration
**Goal:** integrate backend runs into the existing verification spine.  
**Files:**
- `weevil-lunar/verification/harness_manifest.yaml`
- `weevil-lunar/verification/receipts.py`
- `weevil-lunar/verification/run_gate_check.py`

**Tasks:**
- register backend harnesses
- define report/receipt contracts
- ensure missing backend artifacts fail honestly

**Done when:** backend harnesses appear in the same integrity framework as other verification assets.

## 7. Recommended execution order

Implement in this order:

1. `SIM-001` simulation governance doc
2. `SIM-002` shared scenario schema
3. `SIM-003` shared metrics contract
4. `SIM-004` receipt writer
5. `SIM-005` MuJoCo single-leg bootstrap
6. `SIM-006` MuJoCo incline-hold profile
7. `SIM-007` ODE minimal baseline backend
8. `SIM-008` backend parity smoke test
9. `SIM-009` backend disagreement report
10. `SIM-010` receipt-spine integration

## 8. First milestone to target

If only one milestone is funded immediately, make it:

## Milestone M-SIM-1 — Single-Leg Incline Hold Parity v0

### Scope
- shared scenario schema
- shared metrics contract
- shared receipt writer
- MuJoCo incline-hold runner
- ODE incline-hold runner
- reduced-order reference run
- one parity report across 15°, 25°, 35°, 45°

### Expected value
This milestone gives the repo its first real cross-backend embodiment comparison without overcommitting to full hexapod simulation or false validation language.

## 9. Success criteria for the whole roadmap

The roadmap is successful if it produces:
- cleaner separation between toy model and embodied backends
- reproducible scenario definitions
- explicit backend disagreement visibility
- receipts-first simulation governance
- better evidence about fragility and assumption sensitivity

The roadmap is **not** successful if it merely produces more polished plots while leaving the repo more prone to overclaiming.

## 10. Bottom line

This integration plan is designed to make `PerhapsThisBugWillDo` more honest, more comparative, and more technically useful.

Its center of gravity is:
- MuJoCo for primary embodied simulation
- ODE for skeptical solver contrast
- shared contracts before model expansion
- governance strong enough to stop simulator prestige from being mistaken for validation
