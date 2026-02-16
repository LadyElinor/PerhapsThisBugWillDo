# Cleat Sketch Spec (v0.3)

## Objective
Implement directional traction anisotropy matching rescue assumptions:
- forward gain ~1.5
- lateral gain ~1.8

## Reference geometry
- Foot radius: 80 mm nominal (sweep 70–90)
- Quadrant-based cleat layout around pad

## Quadrant specs

### Forward quadrant (±45° about +X)
- Count: 5–7 cleats
- Rake angle: ~38°
- Profile: wedge/triangular
- Base width: 8–10 mm
- Height: 6–8 mm

### Lateral quadrants (left/right)
- Count: 9–12 cleats per side
- Rake angle: ~60°
- Profile: sharper wedge
- Base width: 6–8 mm
- Height: 7–9 mm

### Rear quadrant
- Count: 3–5 cleats
- Rake angle: 15–20°
- Low-profile geometry to reduce drag

## Parametric implementation notes
- Build one cleat seed feature and polar-array it
- Apply quadrant-specific count/rake multipliers
- Keep cleats as separable features for fast sweep variants
- Optional: add perimeter microspine ring for fail-safe on steep slopes
