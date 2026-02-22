# Incline Traction A/B Bench Protocol — CLEAT-C1 vs CLEAT-C2 (72h Validation)

## Objective
Run controlled A/B incline traction tests to determine whether CLEAT-C1 should remain baseline over CLEAT-C2 for the next build cycle.

## Test definition
- **A candidate:** CLEAT-C1 (asymmetric chevron paddle)
- **B candidate:** CLEAT-C2 (split-V + center keel)
- **Terrain analog:** prepared incline board with consistent granular layer
- **Primary outcomes:** slip ratio, motor current, progress efficiency

## Required equipment
1. Incline board with adjustable angle lock (target: 35° and 45°)
2. Angle gauge/inclinometer (±0.5°)
3. Ballast to match test normal load target
4. Inline current logger (>=10 Hz sample rate)
5. DC bus voltage reading (fixed source or logged)
6. Phone video (>=60 fps) side view + scale markers on board
7. Measuring tape/board markings (at least 600 mm track)
8. Two matched printed cleat sets (C1, C2), same material/print settings
9. Fastener torque tool + thread locker
10. Inspection tools (caliper, marker, notebook)

## Controlled constants (must not change within A/B block)
- Same leg module and controller build
- Same control gains and gait profile
- Same ballast mass and placement
- Same board surface prep and simulant thickness
- Same supply voltage setting
- Same warm-up duration before each test block

## Pre-test setup (once)
1. Inspect drivetrain and leg for looseness; verify no pre-existing damage.
2. Confirm firmware/config checksum and record in log.
3. Mount board, set angle to **35°**, verify with inclinometer.
4. Apply and level simulant layer (uniform depth target).
5. Place visual track markers every 50 mm along test path.
6. Mount current logger and verify timestamp sync with phone video.
7. Install CLEAT-C1 set; torque fasteners to spec; record torque value.
8. Run 2 min unloaded warm-up, then 2 min loaded warm-up.

## Test sequence (randomized crossover)
Use randomized order to reduce drift bias.

### Block design
- Slopes: 35°, 45°
- For each slope: 3 runs per candidate (minimum)
- Run duration: 120 s each
- Rest between runs: 60–90 s
- Candidate swap cool-down: 5 min

### Recommended order template
At each slope, draw one of these before running:
- Sequence 1: C1, C2, C2, C1, C1, C2
- Sequence 2: C2, C1, C1, C2, C2, C1

## Per-run procedure
1. Verify slope angle and ballast position.
2. Start video and logger (announce run ID verbally).
3. Place leg at start line with identical start posture.
4. Execute 120 s climb command (no manual intervention unless safety stop).
5. Stop run; save raw logs with run ID.
6. Record quick observations (stall, yaw drift, chatter, shedding).
7. Inspect cleat damage; if critical crack/delam, mark FAIL and stop that candidate.

## Measurements to capture per run
- Commanded travel distance (mm)
- Actual uphill progress distance (mm)
- Slip distance (mm) = commanded - progress
- Slip ratio (%) = slip / commanded * 100
- Mean current (A), peak current (A)
- Input voltage (V)
- Runtime (s)
- Estimated energy input (Wh)
- Any stall event count
- Any structural damage flag

## Safety / abort criteria
Abort run immediately if any of the following occur:
- Persistent stall >3 s
- Current exceeds safe limit for >2 s
- Mechanical interference, crack propagation, or loose cleat
- Loss of board stability or ballast shift

## Post-slope checks
After completing each slope block:
1. Photograph both cleat sets (wear surfaces and cracks).
2. Measure representative lug wear depth at 3 fixed points.
3. Re-level simulant surface before next slope block.

## Data handling
- Save logs under: `weevil-lunar/results/validation/2026-02-22/raw/`
- Use file naming:
  - `run_<slope>deg_<candidate>_<rep>.csv`
  - `video_<slope>deg_<candidate>_<rep>.mp4`
- Consolidate rows into template CSV before analysis.

## Minimum completion definition for readiness
Test is considered complete when:
- Both candidates have >=3 valid runs at 35° and >=3 valid runs at 45°
- No missing current/progress fields
- At least one post-test wear photo per candidate/slope
