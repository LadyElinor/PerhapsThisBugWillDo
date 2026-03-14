# Crover -> Lunar-Weevil Design Delta (2026-03-14)

## Purpose
Capture engineering constraints from newly added Crover source material and map them into Lunar-Weevil specs/docs.

## Inputs reviewed
- `Crover/Crover.txt` (local summary notes)
- `Crover/Crover - Robotic Grain Storage Management.html` (captured product page)
- `Crover/Le -2025 - Change challenges for burrowing soft robots.pdf` (review paper extract)

## Distilled constraints (actionable)

1. **Burrowing must be phase-aware, not monolithic**
   - Separate: entry/submerging, in-medium translation, resurfacing.
   - Why: biological and robotic burrowers show distinct mechanics/failure modes per phase.

2. **Disturbance minimization is a first-class objective**
   - Avoid bulk collapse and high-energy excavation behavior.
   - Use disturbance budget/thresholding, not only speed or distance metrics.

3. **Tip/leading geometry strongly controls drag and insertion force**
   - Wedge/shovel-like leading forms are favored vs blunt profiles.

4. **Media-aware control is required**
   - Burrow feasibility depends on grain/cohesion/moisture regime and depth-dependent pressure.
   - Planner should adapt aggressiveness and pathing to collapse risk.

5. **In-medium sensing is mission-critical**
   - Crover product framing emphasizes high-resolution in-bulk data collection (temperature/moisture/CO2) and remote operation.
   - Lunar analog: in-regolith sensing for hotspot/volatile proxy detection + traversability/collapse cues.

6. **Safety and remote operation remain key value drivers**
   - Crover value proposition includes avoiding hazardous human entry into unstable bulk media.
   - Lunar analog: reduce high-risk direct maneuvers by using autonomous/remote subsurface reconnaissance.

## Mapping into Lunar-Weevil artifacts

### Updated specs/docs in this pass
- `specs/locomotion_spec.md`
  - Added subsurface-burrow mode.
  - Added REQ-LOCO-007/008/009 for phase-aware operation, disturbance-bounded behavior, and tip geometry.
  - Added subsurface verification entries.

- `specs/autonomy_spec.md`
  - Added REQ-AUTO-006/007/008 for phase-aware burrow autonomy, in-medium sensing fusion, and low-disturbance rerouting.
  - Added burrow-response policy and verification item.

- `docs/system_spec.md`
  - Added architecture note for optional Crover-inspired subsurface profile.
  - Added top-level REQ-BURROW-001/002.
  - Added open items for disturbance-index calibration, tip-candidate validation, and in-medium sensing stack.

## Net design delta vs previous baseline

- **Before:** surface-centric hexapod with slope anchoring emphasis.
- **Now:** still surface-first, but with an explicit, optional subsurface mission profile and concrete requirement hooks.

### New capability direction
- Add a low-disturbance subsurface scouting mode for loose regolith pockets where surface-only traversal underperforms.

### New risk introduced
- Added complexity in mobility state machine and validation burden (simulant-bin tests, disturbance metrics, phase-abort behavior).

### New required evidence
- Disturbance-index definition + thresholds.
- Tip-shape A/B validation in representative simulants.
- Subsurface autonomy abort/resurface reliability under injected collapse risk.

## Notes on evidence confidence
- Product-page claims are informative but vendor-provided.
- The Frontiers review provides mechanism-level framing and challenge structure for burrowing soft robots.
- No direct claim here that Crover-like methods are already validated in lunar regolith vacuum conditions.
