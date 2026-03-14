# LunaOps-1 Technical Annex (v0.1)

## 1. Scope
This annex expands the LunaOps-1 PDR package with engineering detail for subsystem owners, verification leads, and integration planning.

Primary reference:
- `docs/lunaops1_pdr_package_v0_1.md`

---

## 2. Derived Technical Requirements (Draft)

### Mobility
- LOPS-MOB-001: Traverse mixed regolith analog terrain with bounded slip.
- LOPS-MOB-002: Sustain controlled operation on 25° slopes nominal, with short 30° sections under assisted mode.
- LOPS-MOB-003: Maintain static stability margin in obstacle crossing up to design step height.

### Autonomy & Safety
- LOPS-AUTO-001: Enforce hazard-stop when perception confidence falls below threshold.
- LOPS-AUTO-002: Provide deterministic safe posture and return-home behavior.
- LOPS-AUTO-003: Preserve command/log continuity across comm interruptions.

### Power/Thermal
- LOPS-PWR-001: Enforce minimum reserve floor >= 25% battery SOC.
- LOPS-PWR-002: Reserve >=10% equivalent energy for recovery actions.
- LOPS-THERM-001: Keep critical avionics/actuators within validated operating envelope.

### Dust/Reliability
- LOPS-DUST-001: Mobility-critical interfaces shall maintain function after abrasive cycle test.
- LOPS-DUST-002: Dust-protection interfaces must be inspectable/serviceable.

### Interfaces
- LOPS-INT-001: Meet mission envelope constraints (mass/CG/stow/deploy).
- LOPS-INT-002: Pass electrical/data compatibility checks for host mission integration.

---

## 3. Subsystem Notes

## 3.1 Mobility
- Architecture: 6-wheel rocker-bogie class for passive load distribution and terrain conformity.
- Wheel choice: grouser pattern tuned for loose regolith traction and manageable sinkage.
- Control coupling: traction-limited command shaping to avoid wheel-churn energy losses.

## 3.2 Compute & Software
- Teleop-first design with bounded autonomy states:
  - `teleop_crawl`
  - `assisted_waypoint`
  - `recovery`
  - `safe_hold`
- Watchdog + restart strategy to ensure recoverability in delayed-link conditions.

## 3.3 Power & PMAD
- Conservative duty-cycle assumptions in mobility-intensive segments.
- Reserve enforcement in planner to prevent no-return sorties.
- Early PMAD sizing should absorb transient peaks from recovery maneuvers.

## 3.4 Thermal
- WEB-style protected core with controlled rejection paths.
- Operational constraints (pause windows / mode throttling) as part of thermal policy.

## 3.5 Dust hardening
- Labyrinth interfaces + sacrificial shields on highest exposure paths.
- Post-run inspect/score criteria tied to acceptance gates.

---

## 4. Verification Mapping (Draft)

| Area | Verification Type | Evidence Artifact |
|---|---|---|
| Mobility envelope | Analog terrain traverse + slope series | mobility report + telemetry logs |
| Autonomy safety | Fault injection + latency/dropout simulation | autonomy safety report |
| Power reserve policy | Mission-script energy replay | energy margin report |
| Thermal envelope | Thermal-vac analog cycles | thermal compliance report |
| Dust durability | Abrasion/ingress endurance + teardown | dust durability report |
| Integration | Interface checklist + deployment rehearsal | interface compliance report |

---

## 5. Proposed V&V Sequence
1. Unit-level component characterization (motors, PMAD, thermal nodes, sensors)
2. Subsystem integration checks (mobility stack, comms stack, autonomy stack)
3. Closed-loop analog mission scenarios (inspection + route scout + return)
4. Fault campaign (degraded wheel, sensor dropout, comm interruption)
5. Acceptance gate closeout with issue disposition log

---

## 6. Configuration & Change Control
- Freeze baseline at PDR closeout tag (`lunaops1-pdr-v0.1`).
- Track changes with requirement impact tags:
  - `MOB`, `AUTO`, `PWR`, `THERM`, `DUST`, `INT`.
- Any change affecting mass/power/thermal must trigger budget re-baseline and gate recheck.

---

## 7. Optional Future Module Path
Crover-like subsurface scout is retained as a **non-blocking extension**:
- only after baseline rover acceptance
- own gates for disturbance/collapse/resurface safety
- no dependency on baseline flight qualification path
