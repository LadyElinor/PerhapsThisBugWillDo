# Studica Robotics Resources — Integration Note (Earth-Analog Prototyping)

## Purpose
Capture where Studica resources are useful for `weevil-lunar` and where they are **not** valid evidence.

## Source
- https://www.studica.com/studica-robotics-resources

## Evidence tier
- **Tier:** Integration/implementation support
- **Not a tier for:** lunar terramechanics or low-gravity contact-physics validation

## What is usable now
- **COTS actuator/sensor integration patterns**
  - motor controllers, servos, linear slides, wiring practices
- **Mobile robotics build workflows**
  - chassis integration, electrical bring-up, controller + telemetry loops
- **STEP/CAD assets for rapid prototyping**
  - fixture/interface starting points for bench prototypes
- **Training materials**
  - practical assembly/programming references for rapid team onboarding

## Mapping to `weevil-lunar`
- **Anchoring mechanics prototyping**
  - use linear actuation and servo-driven linkages as Earth analogs for leg/foot mechanism bring-up
- **Controller + state machine validation**
  - use VMX/NavX-style integration patterns to harden gait state transitions and telemetry checks
- **Bench validation infrastructure**
  - use COTS stack to test repeatability, fault handling, and instrumentation before custom hardware
- **CAD acceleration**
  - adapt STEP components to `cad/interfaces` and fixture templates where compatible

## Non-goals / caveats
- Do **not** cite Studica materials as support for:
  - lunar regolith constitutive modeling,
  - low-gravity traction/sinkage claims,
  - mission-level mobility performance.
- Any physics credibility claim must remain anchored to terramechanics literature, simulant data, or dedicated experiments.

## Recommended next actions
1. Add a COTS bench profile under verification docs (Earth analog only).
2. Add a CAD crosswalk list of reusable Studica component classes.
3. Track evidence separation in reports: `integration evidence` vs `physics evidence`.
