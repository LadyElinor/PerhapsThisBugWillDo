# Power & Comms Spec (v0.3)

## Purpose
Define baseline power/comms requirements supporting autonomy-first lunar mobility.

## Requirements
- REQ-PWR-001: Power system shall support nominal traverse plus anchoring cycles.
- REQ-PWR-002: Power budgeting shall include thermal survival loads.
- REQ-COMMS-001: Vehicle shall tolerate delayed/intermittent comms with autonomous continuation.
- REQ-COMMS-002: Telemetry buffering shall preserve health and mobility logs during dropouts.

## Design notes
- Separate mobility and survival power accounting
- Include reserve for recovery mode retries
- Store-and-forward telemetry architecture for delayed uplink

## Verification
- Mission-profile power budget check against mode timeline
- Comms dropout simulation with telemetry continuity validation
