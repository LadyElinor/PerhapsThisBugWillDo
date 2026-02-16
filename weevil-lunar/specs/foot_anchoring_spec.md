# Foot & Anchoring Subsystem Spec (v0.3)

## 1. Scope
Defines geometry, anchoring behavior, and directional traction requirements for Weevil-Lunar feet.

## 2. Geometry envelope
- Nominal foot radius classes: 0.05, 0.06, 0.07, 0.08 m
- Preferred mare-target class: 0.07–0.08 m
- Foot shall be replaceable (wear surface)
- Directional cleat architecture required

## 3. Anchoring behavior
Steep-slope state machine (required for slopes >25°):
1) Settle
2) Preload
3) Twist-settle
4) Anchor confirmation
5) Push-off

Anchor engage threshold:
- preload >= configured threshold (default 20 N in current model)

## 4. Directional traction model (current)
- Forward directional gain: cleat_gain_forward
- Lateral directional gain: cleat_gain_lateral
- Effective margins evaluated on 45° reference slope:
  - downslope margin >= 1.05
  - lateral margin >= 1.20

## 5. Performance gates
- GATE-FOOT-001 (twist): shear gain ratio >= 1.15
- GATE-FOOT-002 (sinkage): sinkage <= configured cap (default 8 cm system check; tighten for mission mode)
- GATE-FOOT-003 (slope): directional 45° pass with required margins

## 6. Current mare rescue profile (model-derived)
Feasible v0.3 point:
- radius: 0.08 m
- preload: 20 N
- gain_forward: 1.50
- gain_lateral: 1.80
- sinkage: ~0.09 cm (model)

## 7. Interfaces
Inputs:
- preload command
- slope estimate
- slip estimate

Outputs:
- anchored state (bool)
- directional margins (downslope/lateral)
- penetration depth estimate
