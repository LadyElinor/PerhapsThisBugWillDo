# Warranted tests, tranche 02

**Result: retain the nominal analytical model; reject a universal contact-loss recovery claim and whole-assembly clearance. Fabrication and unrestrained walking remain blocked. No physical tests were performed.**

The 2026-10-16 UTC experiment used design revision `4330551e5776e094e03767caa6a727679f5a071f`. [spec.json](spec.json) was written and committed locally before evaluation. It freezes the configuration, BOM, model and CAD-generator hashes, scenario grid, perturbations, controls and stopping rule. No geometry, friction coefficient, torque cap or mass assumption was tuned after inspecting these results. The fixture and component drawing gaps need engineering evidence, not suppressed collision pairs.

## Frozen inputs and candidates

The baseline is the existing 60 kg Earth prototype, with five contacts during a wave-gait phase, 1.3 sizing load factor, 43.2 Nm joint cap, 300 N foot-normal cap, planar idealized contacts and a 40 mm required support margin. Four COM x/y corners and flat plus eight slope headings are applied at 30 selected gait poses per profile. The perturbations are deliberately chosen sensitivity cases, not measured distributions or confidence intervals.

Ten preselected profiles cover the 10° analytical boundary, 5° commissioning profile, friction coefficients 0.3 and 0.2, torque limits reduced by 10% and 20%, COM raised by 50 mm, moving-leg proxy masses increased by 20%, a combined perturbation, and the allocated 56.335 kg mass. A separate interpolation check uses 48 previously unsampled gait positions. The fault family removes each of the five supporting feet in turn while the sixth foot remains in swing.

The leg-mass multiplier changes conservative moving-mass proxies at fixed gross mass. It does not authorize adding that mass to the BOM or exceeding the 60 kg limit.

There is no fitted statistical model, parameter selection or physical holdout dataset here. Identifiability and statistical significance claims are not applicable. The new interpolation points were fixed before scoring; they are mathematical verification cases, not independent measurements of the rover.

## Necessary-condition and output results

| Candidate or claim | Cases | Result | Verdict |
|---|---:|---|---|
| Ten frozen nominal/sensitivity profiles | 10,800 | All satisfy configured wrench, margin and pad-COP constraints | RETAIN under sampled assumptions |
| New intermediate gait positions at 10° | 1,728 | All satisfy the same constraints | RETAIN; no continuous-motion proof |
| Hold the posture after any further supporting-foot loss at 5° | 5,400 | 2,921 infeasible wrenches; 2,479 accepted | CLOSED under tested specification |
| Clearance between all modeled solids | 113,305 pair checks over 31 poses | 70 unique overlapping pairs | CLOSED for current packaging geometry |
| Physical holding-temperature and power performance | No measurements supplied | No numerical physical-record result | SOURCE-GATED |

Full machine-readable outputs: [robustness.json](robustness.json), [geometry.json](geometry.json), [measurement_status.json](measurement_status.json), [release_status.json](release_status.json).

Support-loss rejection counts are **not probabilities of falling or measured failure rates**. They include the configured 1.3 load factor and actuator/contact caps. Some remaining support polygons also place the gravity projection outside the polygon; the worst signed margin is −90.37 mm. The analysis examines the instant after contact removal, not a dynamic recovery trajectory. A feasible static case does not establish successful recovery either.

At 5°, the baseline minimum margin is 94.48 mm and the largest returned joint bound is 39.95 Nm. With the combined perturbations it is 90.39 mm and 36.54 Nm against that profile's reduced cap of 38.88 Nm. These allocations are re-solved separately. The allocator's objective balances normalized contact and joint loading, so a lower torque cap changes the selected force distribution; reported peak torques are not unique minimum required torques. Results for one allocation must not be interpreted as a thermal torque reserve.

### Geometry findings

All 86 modeled solids were checked against each other at the nominal pose and 30 gait poses. The earlier actuator-only screen remains a correct but narrower result.

- **Eight packaging conflicts:** each of the four landing guides intersects the deck and an electronics allowance. Maximum overlap is approximately 3,054 mm³ for each guide/deck pair and 1,373 mm³ for each guide/electronics pair. These appear at all 31 sampled poses.
- **62 unresolved interface overlaps:** examples include motor/carrier envelopes, link/carrier interfaces, femur/tibia stock near the knee, and tibia stock intersecting the ATI sensor envelope. These are reported individually, not waived because they share a leg.

An envelope overlap is evidence of unresolved geometry. It does not by itself establish collision between finished manufactured parts, because finished carriers, clevises, sensor adapters and deck openings have not been modeled. Conversely, those missing details cannot justify declaring clearance. Sensor interfaces must also prevent a parallel structural load path from bypassing force measurement.

The next mechanical revision needs actual bearing/coupler/clevis details, guide mounting openings and support structure, equipment and cable routing, and a complete sensor load path. Any such revision must get a **new** verification specification; this experiment remains a record of the current baseline. Do not remove a solid, add a waiver or change a tolerance simply to make this report green.

## Controls and evidence handling

The outside-support COM and frictionless-slope negative controls were rejected. Geometry controls recovered a 100 mm³ planted overlap and distinguished it from touching or separated boxes. These validate the checker behavior for the controls; they do not validate all mechanical assumptions.

The bench-record checker exercises a synthetic 3,601-record, one-hour hold, then rejects injected overloads, torque loss/reversal, stale validity flags, faults, duplicated times, gaps, short duration, nonfinite values, excess temperature and continuing temperature rise. It also rejects CSV tampering and mismatched configuration, and blocks missing provenance or supplier limits. Synthetic controls remain explicitly non-evidence. A declaration that data are measured still never closes a hardware gate automatically.

## Physical evidence still needed

The next physical experiment remains a restrained joint/leg test **after** detailed fixture and interface review. This tranche supplies [a blank manifest](bench_manifest_template.json) and [CSV header](bench_record_template.csv), not permission to energize an unfinished assembly.

`COTS-T02-HOLD-01` is a declared constant-hold record: target magnitude 43.2 Nm, independently measured output torque between 95% of target and the design cap, at least 3,600 seconds, sample gaps no greater than 1.5 seconds, valid feedback and no driver faults. It compares the means of the first and last 60 seconds of the final 600-second window; temperature rise must be less than 1°C and every sample must remain below supplier limits for the **actual sensor locations**. Limits for motor case and driver temperatures are intentionally blank until sourced. Case temperature cannot substitute for winding temperature without supporting evidence.

Record the predeclared hold interval, actuator/driver identity, firmware, fixture, operator, calibration reference, actual acquisition time, configuration hash and raw CSV hash. Preserve the original acquisition, including load-up and shutdown, separately from the declared steady-hold interval. Do not select a favorable interval after examining outcomes. Lower-load commissioning uses a separately declared protocol and cannot satisfy this worst-case hold protocol.

The sampled power checks require 34–52 V, nonnegative motoring bus current ≤16 A and auxiliary output ≤100.8 W. They establish only whether the supplied samples meet those limits. A one-joint record does not demonstrate whole-rover current consumption; one-second samples cannot establish regenerative transients, E-stop timing or brownout behavior. Those require the actual hardware, appropriate acquisition bandwidth and separate E1/C2 protocols.

## Reproduce

From `weevil-lunar/`:

```sh
python verification/cots/run_tranche_02.py --output /tmp/cots-robustness.json
python verification/cots/check_all_geometry.py --output /tmp/cots-geometry.json
python -m pytest verification/tests/test_cots_tranche_02.py -q
python verification/cots/check_bench_evidence.py --manifest verification/cots/tranche_02/bench_manifest_template.json
```

Install the optional `requirements-cad.txt` for the all-solid check. The last command correctly exits 2 with `SOURCE-GATED`, because no measurements exist in a blank template. The experiment runners exit 0 if execution and controls succeed; **that is not a design-release pass**. Their JSON explicitly retains rejected hypotheses, overlaps and the blocked hardware status.

The earlier soil-model restrictions in `DECISION_MEMO.md` remain unchanged. Nothing in this tranche establishes lunar soil, anchoring, fatigue, thermal endurance, safe power-loss response or flight readiness.
