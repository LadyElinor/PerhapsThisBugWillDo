# Build Packet — Phase-0 Hardware Readiness

**Date:** 2026-02-22  
**Build target:** Single-leg bench module + incline traction test rig (no full rover hardware yet).  
**Design baseline:** `LEG-C1 (AE070/AE070/AE070)` with `CLEAT-C1` primary, `CLEAT-C2` contingency.

## 1) Manufacturing notes (print/machine first)

### Print first (fast loop, low cost)
1. CLEAT-C1 and CLEAT-C2 sets (minimum 3 sets each for repeated runs).
2. Logger/sensor mounts and cable guides.
3. Non-critical spacers/shims and fixture blocks.

**Print controls (must record):** material, nozzle, layer height, infill, orientation, post-processing.  
Reason: validation conclusions must not be confounded by build-process drift.

### Machine/procure in parallel (critical geometry)
1. Joint interface plates and shaft adapters.
2. Bearing seats / precision bores.
3. Incline rig angle-lock hardware and structural rails.

**Tolerance priority:** shaft-bearing fits, gearbox output interface concentricity, and cleat mounting interface flatness.

## 2) Assembly order (gated)

### Gate A — Bench rig infrastructure
1. Assemble incline board frame and lock points for 35° and 45°.
2. Install angle verification reference points.
3. Verify board stability under ballast load + dynamic stepping.

**Acceptance:** rig holds angle within ±0.5° during 120 s run.

### Gate B — Leg drivetrain core
1. Build hip/knee/ankle chain using AE070 baseline stack.
2. Install motor drivers and route power/data harness with strain relief.
3. Static fit + hand-rotation check for binding/interference.

**Acceptance:** no hard points across full commanded range; electrical continuity verified.

### Gate C — Foot and cleat integration
1. Mount CLEAT-C1 and CLEAT-C2 interchangeably on same foot interface.
2. Torque fasteners to documented value; mark witness paint.
3. Confirm swap time and repeatability (target <10 min changeover).

**Acceptance:** 3 consecutive swaps without thread or alignment degradation.

### Gate D — Instrumentation and logging
1. Install current logger and synchronize clock with video capture.
2. Validate file naming and run ID mapping to template schema.
3. Dry-run one 30 s script-driven test and parse output.

**Acceptance:** one dry-run row fully fills required fields in template CSV.

## 3) Required tools / jigs
- Torque driver + hex/bit set
- Threadlocker and witness marker
- Calipers and angle gauge/inclinometer
- Bench PSU with current limit + e-stop
- Inline current logger (>=10 Hz)
- Cleat swap jig (holds foot at repeatable orientation)
- Surface conditioning rake/level tool for granular prep
- Camera mount with fixed side-view reference scale

## 4) Interface assumptions (explicit)
1. **Mechanical interface:** cleat mounting pattern is common between C1 and C2.
2. **Electrical interface:** driver/motor pinout remains unchanged between baseline and fallback gearbox variants.
3. **Control interface:** same firmware/gait profile used across A/B except allowed same-day retune in stop-rule path.
4. **Data interface:** run log schema exactly matches `03_data_logging_template_2026-02-22.csv` column names.
5. **Geometry scope assumption:** current CAD evidence is leg-stack-centric (`digital_baseline_v0_4.md`), so chassis couplings are treated as external/lumped for now.

## 5) Build records for audit
For each build/rework event, record:
- timestamp, operator initials
- part rev / print profile / machine setup
- torque values used
- deviations from nominal process
- photo references and file paths

Without this log discipline, validation outcomes are non-auditable.
