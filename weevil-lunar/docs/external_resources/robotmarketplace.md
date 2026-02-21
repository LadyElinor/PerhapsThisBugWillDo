# RobotMarketplace Mechanical Resources — Integration Note (Earth-Analog Prototyping)

## Purpose
Capture where RobotMarketplace mechanical categories are useful for `weevil-lunar` implementation and where they are not valid scientific evidence.

## Source
- https://www.robotmarketplace.com/products/mechanical_main.html

## Evidence tier
- **Tier:** Integration/implementation support
- **Not a tier for:** lunar terramechanics or low-gravity contact-physics validation

## What is usable now
- **Drivetrain primitives**
  - bearings, shafts/axles, sprockets, roller chain (#35), gearboxes
- **Mechanical integration hardware**
  - mounts, hubs, fasteners, nut strips, key stock
- **High-load mechanical patterns**
  - reduction-ratio selection practices
  - material durability emphasis (e.g., Chromoly for high-load modules)
  - chain-link caveats (connecting link derate)

## Mapping to `weevil-lunar`
- **Earth-analog bench drivetrain rig**
  - use COTS chain/sprocket/shaft/hub combinations to derisk actuation transmission reliability
- **Fixture and interface prototyping**
  - use mounts/hubs/fastener families to standardize mechanical integration patterns
- **Verification support**
  - add chain/sprocket design checklist with explicit derating and safety-factor assumptions

## Non-goals / caveats
- Do **not** use category/product pages as evidence for:
  - regolith constitutive behavior,
  - lunar sinkage/traction performance,
  - mission-level mobility predictions.
- These resources support hardware implementation and reliability heuristics only.

## Recommended next actions
1. Add a COTS drivetrain BOM variant under verification docs (Earth analog only).
2. Add a mechanical crosswalk table mapping external part classes to `cad/interfaces` and fixtures.
3. Add chain/sprocket reliability checklist item (including connecting-link derating note).
