# Digital Baseline Verification - v0.4

**Date:** February 21, 2026  
**FreeCAD Version:** [fill your version]  
**Active File:** [path to your .FCStd]  
**Workbench Used:** [Assembly4 / A2plus / built-in Assembly]  
**Model State:** Post-REFINE shape, datum planes & clipping planes hidden, Display Mode = Shaded

## 1. Mass Properties (Proxy – see caution below)

- **Total Volume (proxy mass, density=1 g/cm³):** 185,852.936 mm³
- **Scaled Mass Estimate (proxy):**
  - Assumed average density for upper-mid bound: 7.85 g/cm³ (steel/alum mix)
  - Calculated: ≈ **1.46 kg**
- **Proxy Caution:** This is a rough upper-mid estimate assuming near-steel density throughout. Actual assembly contains mixed/placeholder geometry (e.g., lightweight brackets, partial representations). Treat as conservative ceiling for leg stack, not literal physical mass.
- **Center of Mass (COM) – Current global coordinates:**
  - X = 6.3996 mm
  - Y = 7.9975 mm
  - Z = 0.8675 mm

→ Very close to origin → likely datum placed at base/plane of assembly.

- **Inertia Tensor at COM (kg·mm²):**

```text
[[4414261.8023, -7.18e-08, 0.00611],
 [-7.18e-08, 8731814.5721, 1.09e-07],
 [0.00611, 1.09e-07, 4414261.7990]]
```

Principal moments ≈ [8.73×10⁶, 4.41×10⁶, 4.41×10⁶] kg·mm² → Dominant Iyy (vertical axis ~2× larger), off-diagonals near zero (principal axes well aligned).

## 2. Collision / Interference Report

- **Method Used:** Assembly validity/interference pass in FreeCAD
- **Invalid shapes found:** 0
- **Colliding pairs found:** 0 (no collisions reported in this pass)
- **Interfering components (if any):** None detected
- **Minimum clearance issues:** None flagged in current check
- **Visual verification notes:** Solid count = 63 (healthy, real geometry present). Bounding box = 92.0 × 28.0 × 92.0 mm (compact, consistent with AE-series gearbox flange scale).

## 3. Model Integrity & Import Summary

- STEP inputs discovered: 6
- Imported successfully: 6
- Failed imports: 0
- Exported object count: 73
- **Interpretation:** Strong import/compile integrity. Model is a partial/merged assembly (likely single-leg stack or gearbox-focused subset), not full rover chassis.

## 4. Single-Leg vs. Full-Rover Interpretation

- **Current scope:** Appears to represent leg stack / gearbox integration only (compact bbox 92×28×92 mm, proxy mass ~1.46 kg at steel density).
- **Full-rover expectation:** Sim assumptions typically target 5–15 kg total mass → current CAD is ~10× lighter → consistent with partial leg focus.
- **Next updates planned:**
  1. Redefine coordinate frame at hip pivot or foot contact plane → re-express COM/inertia relative to that frame.
  2. Keep CAD-derived leg stack as-is → add explicit lumped body/chassis mass + inertia terms in sim config (avoids distorting local dynamics).

## Post-Foot-Plane Reframe Update (v0.4.1)

- Reframe complete: Z=0 at lowest foot contact plane (`Zmin ≈ -3.8e-7 mm`, numerical noise)
- New bounding box: 92.0 × 12.5 × 92.0 mm
- New COM (foot-plane frame): X ≈ 0.0000 mm, Y = 4.7076 mm, Z = 41.4373 mm
- Inertia tensor unchanged under rigid translation (at COM):

```text
[[4414261.8023, -7.18e-08, 0.006111],
 [-7.18e-08, 8731814.5721, 1.09e-07],
 [0.006111, 1.09e-07, 4414261.7990]]
```

- Scaled proxy mass: 0.7317 kg (`ρ = 7.85e-6 kg/mm³`, upper-mid mixed-material estimate)
- Interpretation: COM Z is now physically meaningful height above ground and usable for sinkage/preload/stability calculations.

## 5. Discrepancies vs. Simulation Assumptions (Preliminary)

- Sim mass proxy (from manifest JSON): [fill from current manifest] kg
- FreeCAD scaled proxy: ≈1.46 kg
- Difference: [± % – fill after comparison]
- Sim COM: [x,y,z from JSON] vs. FreeCAD: [diff vector – fill after frame normalization]
- Action items: Frame shift + lumped body addition (see planned updates above)

**Attachments / Screenshots (to be added):**
- Mass properties dialog
- Model tree (showing 63 solids)
- Isometric shaded view
- [Pending: Collision check dialog]

**Status:** Baseline captured (mass/COM/inertia complete); collision pending  
**Next actions:**
- Run Assembly collision check → complete section 2
- Normalize coordinate frame → update COM/inertia
- Commit & push v0.4
- Feed updated values into manifests & sim config augmentation
