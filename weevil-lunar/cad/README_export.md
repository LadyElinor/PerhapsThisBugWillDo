# README_export.md

## Export Bundle (per leg module)
1. `weevil_leg_module_ap242.step` — full assembly STEP AP242 (sparse PMI)
2. `weevil_leg_module.urdf` — kinematic chain for sim
3. `weevil_leg_params.yaml` — source-of-truth parameters and sweep ranges
4. `README_export.md` — this file

## Conventions
- **Units**: linear in mm; angles in deg; masses in kg
- **Coordinate frame**:
  - Body/chassis: +X forward, +Y left, +Z up
  - Right-handed (ROS REP-103 aligned)
  - Foot contact plane: Z=0 at pad bottom in nominal stance
- **STEP schema**: AP242 (Ed2+ preferred)

## Export assembly state
- Nominal stance height: 180 mm
- Neutral joints:
  - coxa yaw = 0°
  - femur pitch = 0°
  - tibia extension = mid-stroke
- Mating refs visible:
  - coxa mount interface
  - foot pad bottom datum (Z=0)
  - key bearing/motor faces

## Notes
- URDF approximates helical tibia using revolute+prismatic in v0.3
- Keep YAML as single source of truth for variants
- Include export metadata in commit messages:
  - tool/version/date
  - schema
  - PMI presence
  - git commit hash
