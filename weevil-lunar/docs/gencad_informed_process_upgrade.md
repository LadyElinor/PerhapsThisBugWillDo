# GenCAD-Informed Process Upgrade for Lunar-Weevil (2026-03-14)

## Why this exists
GenCAD demonstrates a practical pattern we can reuse: **structured representation -> staged training/validation -> conditional generation -> deterministic decode/export**.

For Lunar-Weevil, this translates into a tighter design loop for regolith navigation variants (including a Crover-like subsurface concept).

## Process upgrades (adopt now)

1. **Three-stage pipeline (separate concerns):**
   - **Stage A: Geometry/kinematics latent prep** (variant parameters + feasibility descriptors)
   - **Stage B: Cross-modal alignment** (images/sketches/terrain maps <-> variant descriptors)
   - **Stage C: Conditional proposal + deterministic checks** (generate candidate, then gate with physics/safety)

2. **Artifact discipline:**
   - Every generated variant must emit:
     - parameter receipt (YAML/JSON),
     - gate report,
     - export receipt (CAD + traceability refs).

3. **Retrieval before generation:**
   - First retrieve nearest known-good variants from local library.
   - Only generate/perturb when retrieval confidence is low or constraints are unmet.

4. **Conditioned generation target:**
   - Condition candidate generation on mission context (terrain class, slope, disturbance budget, sensing objective),
   - not just geometry priors.

5. **Safety-first decode:**
   - Any candidate decode must pass hard gates:
     - slope margin,
     - disturbance index,
     - resurfacing viability,
     - thermal/power reserve.

## Crover-like lunar variant direction (new)

### Name
`regolith_swimmer_v1` (concept variant)

### Intended role
Low-disturbance entry + short-range in-medium scouting in loose regolith pockets where surface-first traversal underperforms.

### Key attributes
- Wedge/shovel entry profile
- Phase-aware controller: `entry -> translate -> resurface`
- Disturbance-budget governor (collapse-risk aware)
- In-medium sensing payload profile (thermal + volatile proxy + load trend)

### Non-goals (for now)
- No claim of full mission replacement for hexapod surface mode
- No assumption of vacuum-validated Crover-equivalent hardware yet

## Immediate implementation hooks
- Config variant file: `configs/regolith_burrow_variants_2026-03-14.yaml`
- Validation test: `verification/test_regolith_burrow_profile.py`

## Acceptance criteria for process upgrade
- Variant config passes schema sanity checks.
- Gate check can ingest variant and produce pass/fail with explicit reasons.
- Variant outputs receipts compatible with current traceability flow.
