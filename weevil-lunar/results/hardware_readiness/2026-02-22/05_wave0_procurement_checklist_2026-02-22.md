# Wave 0 Procurement Checklist (Buy-Now)

## Objective
Place critical-path orders for the selected default configuration:
- **Geometry:** `scaled_full_cleat`
- **Drivetrain/Cleat baseline:** `uniform_ae070 + CLEAT-C1`
- **Fallback reserve:** `hybrid_b + CLEAT-C2`

## A) Place immediately (today)
- [ ] AE070-class gearbox set for Phase-0 leg module (**3 + 1 spare**)
- [ ] Compatible motor + driver set (**3 + 1 spare driver**)
- [ ] Bench PSU + protection kit (fuse/e-stop/current limiting)
- [ ] Inline current logger (>=10 Hz) + 1 spare sensing path
- [ ] Incline rig core materials (frame/deck/angle-lock hardware for 35° + 45°)
- [ ] Fastener/retention kit (threadlocker, locking hardware, witness paint)
- [ ] Cleat prototype print materials (enough for C1/C2 repeated A/B cycles)

## B) Reserve now (long-lead risk mitigation)
- [ ] AE090-class fallback reservation for hip position (no full release yet)
- [ ] Pin-compatible fallback driver SKU reservation
- [ ] Precision shaft/bearing alternates (second source)

## C) Vendor/order hygiene (must capture)
For each line item:
- [ ] Vendor
- [ ] SKU/part number
- [ ] Unit cost
- [ ] Qty ordered
- [ ] ETA / lead time
- [ ] Cancellation terms
- [ ] Substitute SKU

## D) Gate before releasing Wave 1
- [ ] Confirm CAD/package interfaces pass pre-hardware checks
- [ ] Confirm logging schema + analysis scripts parse synthetic and first real records
- [ ] Confirm no geometry overlap in chosen variant (`scaled_full_cleat`)

## Decision rules
- Continue: all A-items ordered + fallback reserves in place + no interface blockers.
- Pivot: any critical A-item >6 week lead with no substitute.
- Stop: unresolved interface mismatch preventing bench-leg assembly.
