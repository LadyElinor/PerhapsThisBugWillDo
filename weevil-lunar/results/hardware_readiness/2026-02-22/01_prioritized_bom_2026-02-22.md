# Weevil-Lunar Hardware Readiness BOM (Prioritized)

**Date:** 2026-02-22  
**Scope basis:** No physical hardware exists yet. This BOM is for a **Phase-0 bench validation build** aligned to current recommendation (`uniform_ae070 + CLEAT-C1`) and the 72h validation protocol.  
**Primary sources:**
- `results/design/design_sprint_executive_summary_2026-02-22.md`
- `results/design/hip_design_candidates_2026-02-22.csv`
- `results/design/leg_design_candidates_2026-02-22.csv`
- `results/design/cleat_design_candidates_2026-02-22.csv`
- `results/validation/2026-02-22/01_incline_traction_ab_protocol_2026-02-22.md`
- `results/validation/2026-02-22/02_test_matrix_and_decision_thresholds_2026-02-22.md`

---

## Quantity basis and scaling
- **Immediate build quantity:** 1 bench rig leg module + incline test rig + spares for repeat A/B testing.
- **If scaling to full rover:** multiply joint-side drivetrain/actuation quantities by planned leg count (assume 6 unless architecture changed), then add 15–20% spares for first article.

---

## Tier 1 — Must-buy-now (critical path)

| Item | Est. Qty (Phase-0) | Why now | Substitute / long-lead mitigation |
|---|---:|---|---|
| AE070-class gearboxes (joint set for LEG-C1 baseline) | 3 + 1 spare | Core to selected baseline (`LEG-C1`, `uniform_ae070`) and determines integration geometry | Order 2 vendors in parallel if available; if lead >6 weeks, place fallback reservation for AE090 on hip position only |
| Motor+driver set compatible with AE070 joints | 3 + 1 spare driver | Needed to exercise torque/speed envelope and gather current/energy metrics in protocol | Keep pin-compatible backup driver SKU; maintain firmware abstraction layer |
| Bench power supply + protection (fuse/e-stop/current limits) | 1 set | Required for safe repetitive incline runs and overcurrent abort logic | Use lab PSU + inline breaker as interim |
| Incline board assembly (35°/45° lockable), angle gauge | 1 rig | Direct requirement from validation matrix/protocol | If machining delayed, use modular extrusion frame + plywood test deck |
| Data logging stack (inline current logger >=10 Hz, synchronized timestamps) | 1 + 1 spare sensor | Required by data template/quick analysis scripts | Use DAQ or calibrated shunt+MCU logger if primary unavailable |
| Cleat print materials + fasteners (C1/C2 sets) | 6 sets total (3 C1, 3 C2) | Immediate A/B validation objective; wear/destruction expected | PETG/nylon fallback if primary filament unavailable |
| Core structural stock for single leg frame (plates, standoffs, shafts, bearings) | 1 set + 20% extras on wear parts | Enables first mechanical integration and kinematic checks | Prioritize COTS dimensions to avoid custom machining lead times |
| Fastener kit + threadlocker + torque tools | 1 full kit | Required to enforce repeatable assembly and avoid false failures | Maintain mixed lengths and locking features to avoid stall from missing small parts |

---

## Tier 2 — Can-delay (order after first digital/manufacturing gates pass)

| Item | Est. Qty | Delay rationale | Trigger to release |
|---|---:|---|---|
| AE090 hip fallback gearbox | 1–2 | Only needed if torque headroom issues force `HIP-C2`/`LEG-C2` pivot | Release if margin proxy <20 Nm or slip trigger causes drivetrain pivot |
| Extended sensor suite (IMU, thermal probes, force/load sensing) | 1 kit | Helpful but not needed for first decision gates | Release after first valid 12-run matrix completion |
| Chassis-level structure and non-test payload mounts | 1 proto set | Current evidence is leg-stack-focused; full body still provisional | Release after leg module clears continue gate and interface freeze v0.5 |
| Higher-throughput charger/battery pack test set | 1 set | Bench PSU is sufficient for initial runs | Release when moving from fixed bench power to mobile operation |
| Environmental chamber/dust enclosure | 1 | Useful for robustness, not required for first traction A/B | Release after C1/C2 decision lock |

---

## Tier 3 — Optional / optimization

| Item | Est. Qty | Optional value |
|---|---:|---|
| Additional cleat variants (C3 and geometry tweaks) | 2–4 sets | Exploration only if C1/C2 underperform |
| Camera upgrades/high-speed capture | 1 | Better motion analytics; not mandatory for go/pivot/stop logic |
| Rapid jig duplicates | 1 set | Throughput gain if moving to multiple simultaneous rig builds |
| Cosmetic covers/nonfunctional enclosure parts | as needed | No impact on near-term validation decisions |

---

## Long-lead watchlist (audit focus)
1. **AE070/AE090 gearbox procurement** — likely longest lead; dual-source early.
2. **Custom shafts/precision bearings** — second-longest if tolerance stack is tight.
3. **Motor drivers** — chip shortages can force substitutions; pre-qualify pin-compatible alternatives.

## Audit notes
- This BOM intentionally prioritizes **test-decision capability** over full mission hardware completeness.
- Any item not directly supporting the 35°/45° A/B matrix is deprioritized unless it is a known lead-time risk.
