# Procurement Sequencing Plan (Lead-Time Aware)

**Date:** 2026-02-22  
**Objective:** Acquire only what is needed to reach first decision-quality bench data, while protecting schedule from long-lead failures.

## Ordering waves

## Wave 0 (Day 0–1): schedule protection orders
Place immediately:
1. AE070 drivetrain set (Phase-0 quantity + spare)
2. Reservation/quote hold for AE090 hip fallback quantity
3. Motor drivers (primary + pin-compatible backup)
4. Bearings/shafts/critical precision hardware

**Risk mitigations:**
- dual-vendor quote comparison within 24h
- split order across suppliers when possible
- confirm cancellation/change terms before PO

## Wave 1 (Day 1–3): validation rig essentials
Place after Wave 0 acknowledgements:
1. Incline rig structural materials and angle-lock hardware
2. Logger, power safety hardware, cabling, connectors
3. Cleat print materials and standard fasteners

**Risk mitigations:**
- prioritize local stock for consumables
- buy 20% overage on low-cost failure-prone items

## Wave 2 (Day 4+): contingent expansion
Release only if pre-hardware readiness gate passes and no architecture pivot:
1. Additional instrumentation
2. Chassis-level structure and noncritical assemblies
3. Optional test enhancements

**Risk mitigations:**
- tie release to explicit gate criteria, not calendar date
- avoid locking capital into components not needed for first decision

---

## Lead-time risk register

| Risk | Impact | Early indicator | Mitigation |
|---|---|---|---|
| AE070 supply slip | Blocks baseline build | quoted lead >6 weeks | convert hip position to AE090 fallback reservation; keep interface adapters configurable |
| Driver SKU EOL/backorder | Electrical integration delay | distributor low stock alerts | qualify pin-compatible alternate now; abstract firmware IO layer |
| Precision machining queue delay | Assembly lag, tolerance risk | shop ETA > planned start by >1 week | shift to COTS stock dimensions where feasible; prioritize only fit-critical parts |
| Print material inconsistency | Invalid A/B comparison | lot-to-lot property changes | single lot purchase for C1/C2 campaign; record lot ID in run log |
| Missing small hardware | Hidden blockers | repeated partial kits | kitted fastener bins + receiving checklist |

---

## Decision-coupled release logic
- **Continue outcome (C1 passes):** release Wave 2 for integration expansion.
- **Pivot outcome:** pause nonessential orders; release only parts needed for fallback candidate.
- **Stop outcome:** freeze all architecture-specific long-lead spend and open redesign package.

## Audit controls
- Keep procurement ledger with: item, supplier, quote date, promised lead, order date, actual receipt.
- Weekly variance review: promised vs actual lead time and burn-down of critical-path risk.
