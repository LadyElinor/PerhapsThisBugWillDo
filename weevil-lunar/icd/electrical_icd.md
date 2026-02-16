# Electrical ICD (v0.3)

## Scope
Electrical interfaces for actuation, sensing, power distribution, and compute.

## Interface definitions
- Power rails and current limits by subsystem
- Sensor bus mapping (foot state, thermal, actuator health)
- Motor driver control/feedback channels
- Fault lines and emergency inhibit signaling

## Requirements
- Critical mobility loops shall have deterministic update path
- Health telemetry shall be timestamped and buffered during comm loss
- Connector strategy shall account for dust and vibration exposure
