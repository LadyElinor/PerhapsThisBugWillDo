# Software ICD (v0.3)

## Purpose
Defines message/interface contract between mobility controller, foothold scorer, and health monitor.

## Core messages

### foot_state
- foot_id: string
- anchored: bool
- preload_N: float
- slip_ratio: float
- penetration_depth_cm: float
- margin_downslope: float
- margin_lateral: float

### terrain_patch
- regolith_class: enum(mare, highland, mixed, compacted)
- slope_deg: float
- confidence: float

### health_state
- joint_torque_margin: float
- thermal_margin: float
- actuator_friction_index: float
- degraded_mode: bool

### locomotion_command
- gait_mode: enum(nominal, steep_slope, recovery)
- target_velocity_mps: float
- duty_factor: float
- preload_schedule: object

## Safety interlocks
- push_off_enabled requires anchored=true when slope_deg>25
- if margin_downslope<1.05 or margin_lateral<1.20 then block push-off and trigger re-anchor/replan
