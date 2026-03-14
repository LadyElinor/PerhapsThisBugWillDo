# LunaOps-1 PDR Package (v0.1)

## 0) Mission intent
**LunaOps-1** is an operations-enabler lunar rover designed for early Starship surface missions.

Primary mission value:
- landing-zone inspection
- route scouting / hazard mapping
- cargo-zone logistics support
- local comms/situational awareness relay

Design philosophy:
- maximize flight-likelihood (heritage architecture, bounded autonomy, conservative margins)
- avoid high-risk novelty in first mission build

---

## 1) Preliminary mass budget (target class: 55-75 kg dry)

| Subsystem | Target Mass (kg) | Notes |
|---|---:|---|
| Chassis + rocker-bogie structure | 14.0 | Al/composite frame, mounting rails |
| Wheels + drive assemblies (x6) | 12.0 | Motors, gearboxes, wheel hubs/grousers |
| Avionics + compute + harness | 5.0 | Primary compute + watchdog + buses |
| Power (battery + PMAD) | 10.0 | Includes BMS, converters, margins |
| Solar deployables | 4.0 | Stowed + deployment hardware |
| Thermal hardware | 5.0 | WEB insulation, heaters, radiator interfaces |
| Sensors payload | 4.0 | Nav/haz cams, IMU, thermal cam |
| Comms hardware | 2.5 | Local relay + high/low rate links |
| Dust mitigation + covers | 2.0 | Seals/shields/sacrificial surfaces |
| Contingency (15%) | 8.8 | Early-phase reserve |
| **Total (dry)** | **67.3 kg** | Within target range |

### Stowed envelope target
- Approx. **1.2 m x 0.9 m x 0.7 m** (config dependent)

### CG target
- Keep CG centered and low relative to axle plane for slope robustness.

---

## 2) Preliminary power budget (day operations)

| Mode | Avg Power (W) | Peak Power (W) | Duration Assumption |
|---|---:|---:|---|
| Idle-safe + comm listen | 45 | 70 | standby windows |
| Teleop crawl | 180 | 320 | nominal traverse |
| Assisted autonomy traverse | 210 | 360 | hazard-aware route |
| Intensive sensing burst | 260 | 420 | mapping/inspection pass |
| Recovery maneuver | 300 | 500 | short transient |

### Energy policy
- Minimum battery reserve floor: **25%**
- Recovery reserve carve-out: **>=10%** of pack
- Hard no-go if predicted return energy margin < threshold

### Generation assumptions (early)
- Solar generation is mission/profile dependent; use conservative derates for dust/angle/thermal.

---

## 3) Subsystem block diagram (functional)

```text
            +---------------------------+
            |   Mission Ops / Ground    |
            +-------------+-------------+
                          |
                          v
+---------------------------------------------------+
|                    COMMS STACK                    |
|  relay mode / teleop link / store-forward logs    |
+---------------------+-----------------------------+
                      |
                      v
+---------------------------------------------------+
|               AVIONICS + AUTONOMY                |
|  mode manager | planner | hazard detect | health  |
+---------+----------------------+-------------------+
          |                      |
          v                      v
+------------------+    +---------------------------+
| SENSOR SUITE     |    | POWER + THERMAL CONTROL   |
| nav/haz cams     |    | battery/BMS/PMAD/heaters  |
| IMU/odometry     |    | WEB + radiator interfaces |
| thermal camera   |    +---------------------------+
+---------+--------+
          |
          v
+---------------------------------------------------+
|             MOBILITY CONTROL LAYER                |
| wheel drive commands | slip control | safe stop   |
+---------------------+-----------------------------+
                      |
                      v
+---------------------------------------------------+
|        ROCKER-BOGIE + WHEELS + DUST SEALING       |
+---------------------------------------------------+
```

---

## 4) 90-day test campaign (selection demo oriented)

## Phase 1 (Days 1-30): subsystem verification
- Mobility bench: actuator smoothness, backlash, wheel torque checks
- Power/thermal bench: charge/discharge behavior, heater control, thermal control loops
- Sensor calibration: camera/IMU alignment, odometry sanity
- Dust ingress bench: seal effectiveness under abrasive cycle proxy

Deliverables:
- subsystem test reports
- updated mass/power rollup
- risk burn-down update

## Phase 2 (Days 31-60): integrated terrestrial analog tests
- Traversability course: slopes, obstacles, low-cohesion bins
- Teleop with latency profile and comm dropout cases
- Safety behaviors: hazard-stop, safe posture, return-home
- Endurance run: repeated traverses with thermal/power logging

Deliverables:
- integrated performance report
- autonomy policy evidence package
- failure mode log + mitigations

## Phase 3 (Days 61-90): mission rehearsal + acceptance readiness
- Full mission script rehearsal (landing-zone inspection scenario)
- Cargo-zone route scout + mapping repeatability
- Fault injection series (sensor loss, wheel degradation, comm interruptions)
- Final verification against acceptance gates

Deliverables:
- PDR closeout packet
- acceptance gate results
- recommended flight config freeze list

---

## 5) Flight acceptance gate checklist (draft)

## A) Mechanical / mobility
- [ ] Structural margins validated for launch and surface loads
- [ ] Slope and obstacle performance meets mission minima
- [ ] Wheel/drive assemblies pass endurance thresholds

## B) Power / thermal
- [ ] Battery safety and reserve policy validated
- [ ] Thermal operating band maintained in test envelope
- [ ] Survival mode and recovery mode validated

## C) Avionics / software
- [ ] Mode manager behavior verified (teleop, assisted, recovery, safe)
- [ ] Hazard-stop and return-home reliability demonstrated
- [ ] Watchdog/reset and log persistence verified

## D) Comms / operations
- [ ] Teleop command loop validated under expected latency/dropout
- [ ] Relay/store-forward functions verified
- [ ] Ops procedures validated with rehearsal scripts

## E) Dust / reliability
- [ ] Dust ingress thresholds pass acceptance criteria
- [ ] Post-test teardown shows acceptable wear/binding

## F) Interface compliance
- [ ] Mass/CG/envelope within mission allocation
- [ ] Mechanical tie-down and deployment constraints satisfied
- [ ] Electrical/data interfaces pass compatibility checks

## G) Mission utility
- [ ] Landing-zone inspection products generated to required quality
- [ ] Route scouting and hazard map outputs meet ops needs
- [ ] Cargo-zone support scenario completed within time/energy budget

---

## 6) Top risks and mitigations (early)
- **Dust-induced degradation** -> sealing hardening, sacrificial covers, frequent inspection points
- **Thermal excursions** -> stronger WEB insulation/heater control + operational thermal constraints
- **Energy shortfall in degraded solar conditions** -> conservative reserve policy + shorter sortie planning
- **Autonomy overreach risk** -> keep autonomy bounded and explainable; teleop-first doctrine

---

## 7) Recommendation
Proceed with **LunaOps-1 baseline** as a low-risk operations rover. Keep Crover-like subsurface scout as a later add-on payload/module after baseline ops rover is flight-proven.
