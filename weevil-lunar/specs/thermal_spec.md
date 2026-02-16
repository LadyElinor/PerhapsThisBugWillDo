# Thermal Spec (v0.3)

## Purpose
Define thermal-control architecture and operating limits for lunar day/night environments.

## Requirements
- REQ-THERM-001: Critical electronics and actuators shall remain within operating temperature range.
- REQ-THERM-002: System shall provide survival thermal mode for night/shadow operation.
- REQ-THERM-003: Thermal monitoring shall be exposed to health-aware planner.

## Architecture assumptions
- Conduction path through structural backbone
- Radiative surfaces/panels for heat rejection
- Insulated actuator enclosures
- Survival heaters for non-operational thermal maintenance

## Verification
- Thermal-vac cycle with representative motion load
- Heater budget validation in survival mode
- Thermal margin trend logging under repeated locomotion cycles
