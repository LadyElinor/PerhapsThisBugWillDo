# Weevil-Lunar v0.3 Test Summary (Directional Slope Rescue)

## mare
- [PASS] twist_settle_gain: value=1.150, threshold=1.150 (shear ratio=1.150)
- [PASS] sinkage_limit: value=0.231, threshold=8.000 (sinkage=0.23 cm)
- [FAIL] directional_slope_margin_45deg: value=0.801, threshold=1.050 (cone_fwd=36.06°, cone_lat=36.06°, down_margin=0.801, lat_margin=0.801, anchored=True, preload=20.0N, gf=1.00, gl=1.00)
- [RESCUE] feasible with radius=0.08 m, preload=20.0 N, gains(fwd/lat)=(1.50/1.80), sinkage=0.09 cm
  note: cone_fwd=49.18°, cone_lat=54.25°, down_margin=1.093, lat_margin=1.206, anchored=True, preload=20.0N, gf=1.50, gl=1.80

## highland
- [PASS] twist_settle_gain: value=1.150, threshold=1.150 (shear ratio=1.150)
- [PASS] sinkage_limit: value=0.707, threshold=8.000 (sinkage=0.71 cm)
- [FAIL] directional_slope_margin_45deg: value=0.855, threshold=1.050 (cone_fwd=38.49°, cone_lat=38.49°, down_margin=0.855, lat_margin=0.855, anchored=True, preload=20.0N, gf=1.00, gl=1.00)
- [RESCUE] feasible with radius=0.05 m, preload=20.0 N, gains(fwd/lat)=(1.40/1.80), sinkage=0.71 cm
  note: cone_fwd=48.07°, cone_lat=55.06°, down_margin=1.068, lat_margin=1.224, anchored=True, preload=20.0N, gf=1.40, gl=1.80

## mixed
- [PASS] twist_settle_gain: value=1.150, threshold=1.150 (shear ratio=1.150)
- [PASS] sinkage_limit: value=0.177, threshold=8.000 (sinkage=0.18 cm)
- [FAIL] directional_slope_margin_45deg: value=0.856, threshold=1.050 (cone_fwd=38.50°, cone_lat=38.50°, down_margin=0.856, lat_margin=0.856, anchored=True, preload=20.0N, gf=1.00, gl=1.00)
- [RESCUE] feasible with radius=0.08 m, preload=20.0 N, gains(fwd/lat)=(1.30/1.60), sinkage=0.07 cm
  note: cone_fwd=48.22°, cone_lat=54.02°, down_margin=1.072, lat_margin=1.200, anchored=True, preload=20.0N, gf=1.30, gl=1.60

## compacted
- [PASS] twist_settle_gain: value=1.150, threshold=1.150 (shear ratio=1.150)
- [PASS] sinkage_limit: value=0.018, threshold=8.000 (sinkage=0.02 cm)
- [FAIL] directional_slope_margin_45deg: value=0.968, threshold=1.050 (cone_fwd=43.56°, cone_lat=43.56°, down_margin=0.968, lat_margin=0.968, anchored=True, preload=20.0N, gf=1.00, gl=1.00)
- [RESCUE] feasible with radius=0.08 m, preload=20.0 N, gains(fwd/lat)=(1.10/1.30), sinkage=0.01 cm
  note: cone_fwd=51.07°, cone_lat=55.64°, down_margin=1.135, lat_margin=1.237, anchored=True, preload=20.0N, gf=1.10, gl=1.30

