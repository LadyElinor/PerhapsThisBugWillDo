# Weevil-Lunar Candidate Rover Design, WL-D1 (model-derived, v0.3 stack)

Generated 2026-06-09 by running the repository's own analysis surface
(reduced-order leg model, morphology harness, Bekker-Wong/Mohr-Coulomb
regolith contact model v0.3) plus a 360-point configuration sweep
(`../fable5/design_synthesis.py`). Every number below traces to a listed receipt.

**Provenance caveat up front:** this is a reduced-order, quasi-static,
model-derived design point. Regolith parameters are literature-typical,
several verification harnesses carry model-based placeholder values, and
nothing here has hardware-in-the-loop validation. It is a candidate, not
a validated design.

## Configuration

| parameter | value | source |
|---|---|---|
| Morphology | Beetle/Weevil hexapod, screw-coupled tibia | morphology_tradeoff.csv |
| Legs | 6 (tripod gait, quasi-static) | design sweep |
| Body mass (swept-feasible max) | 40 kg | design sweep (sweep ceiling, not a physics limit) |
| Body mass (CAD baseline) | 30 kg | cad/weevil_leg_params.yaml |
| Stance height | 180 mm | cad/weevil_leg_params.yaml |
| Leg kinematics | coxa yaw ±60°, femur −90°/+45° (50 mm link), helical tibia 13.5 mm/rev × 35 mm stroke | cad/weevil_leg_params.yaml; leg model run |
| Foot | 80 mm radius circular pad, 6 mm pad | rescue sweep optimum; CAD freeze |
| Directional cleats | forward gain 1.50 (rake 38°), lateral gain 1.80 (rake 60°) | rescue sweep; CAD freeze |
| Anchoring | preload 20 N/leg, twist-settle gain ≥1.15, cleat engage threshold 20 N (recommended change) | design sweep |
| Actuation per leg | ~50 W BLDC + ~80:1 reduction (coxa/femur), recirculating-ball screw (tibia) | CAD yaml; prototype_bom_v0.csv |

## Why hexapod beetle/weevil

From `results/GPT/Robotics/morphology_tradeoff.csv`: the arachnid offers the
largest workspace volume but the lowest shear per leg, the crab posts the best
raw slope margins but with deliberately reduced ROM, and the ant is fastest but
weaker on durability routing. The beetle/weevil combines strong workspace with
the screw-coupling durability note, and no morphology passes 45° unaided at
baseline anyway. In this scaffold, slope capability comes from the anchoring
envelope rather than morphology choice, which frees morphology selection to
optimize durability and workspace.

## Slope performance at the design point

| stance | downslope margin (≥1.05) | lateral margin (≥1.20) | worst sinkage (≤8 cm) |
|---|---|---|---|
| Full 6-leg stance | 1.17 | 1.28 | 0.43 cm |
| Tripod (3-leg) stance | 1.16 | 1.27 | 0.43 cm |

REQ-FOOT-002/003/004 pass on all terrains in both stances; anchoring engages
above 25° as required. The unassisted baseline still fails 45° on all terrains,
which remains the documented expected-fail design gap the anchoring envelope is
meant to close.

## Finding: the v0.3 CAD freeze fails its own gates

`cad/weevil_leg_params.yaml` freezes `cleat_engage_threshold_N: 50.0`, but the
rescue envelope it also freezes (preload 20 N, gains 1.50/1.80) was validated
with threshold 20 N. Under the current engagement rule (`anchored = preload >=
threshold`), the frozen values prevent cleat engagement.

Two quantified resolutions from `fable5/design_sweep.csv`:

| resolution | down/lat margin (full) | sinkage | cost |
|---|---|---|---|
| Lower threshold to 20 N (recommended) | 1.18 / 1.29 | 0.38 cm | one YAML line |
| Raise preload to 50 N | 1.15 / 1.26 | 0.66 cm | +30 N/leg actuation authority |

Recommended next action: change `cleat_engage_threshold_N` from 50.0 to 20.0,
then rerun the suite so the receipts spine records the change explicitly.

## Open items before physical claims

The mass ceiling still reads as sweep-limited, not actuation- or structure-
closed. Bekker-Wong parameters still need calibration against simulant data.
Several harnesses remain model-based until hardware-in-the-loop data lands.
Use this design note as a candidate recommendation, not evidence of validated
hardware performance.

## Receipts

- `../fable5/design_synthesis.py` and `../fable5/design_sweep.csv`
- `results/GPT/Robotics/morphology_tradeoff.csv`
- `results/GPT/Robotics/gate_results.csv`
- `results/GPT/Robotics/mare_rescue_profile.md`
- `results/GPT/Robotics/weevil_lunar_test_results.md`
- `verification/reports/receipts.json`
