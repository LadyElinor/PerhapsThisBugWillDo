# Support-region investigation 02

**The offline analysis and evidence checks are stronger; the rover has not acquired a feasible support-loss design.** A necessary normal-force bound closes the registered fixed-height/orientation foot-placement family. No new candidate is admitted, and the original load, torque, friction and stability constraints remain unchanged.

This additive investigation follows the [walking-robot source review](../../../research/walking_robot_review_2026-10-17.md). It adapts the idea of feasible support regions while retaining this project's six-leg model, L1 friction pyramid, conservative leg self-weight torque, normal cap, finite-foot COP check and stability reserve. It does not import another robot's constraints or claim that a learned policy transfers. The original model, guard, CAD, interfaces and tranche results remain frozen.

## Decision rule and provenance

[spec.json](spec.json) was committed before these experiments in [d42f008](https://github.com/LadyElinor/PerhapsThisBugWillDo/commit/d42f0082feb6536a9af98501a04831c69c86d636), on research parent `1bbf4e419d48afe5c5d2392c7e531d00c19476af`. Input hashes bind the COTS-1.1 configuration and the earlier support-loss investigation. This is an analytical follow-up using the same scenarios, not a new independent physical holdout.

Any proposed gait must pass all **1,080 nominal and 5,400 additional-support-loss cases**, with no rejection, plus the full progressing periodic gait, joint, clearance, speed and shaft checks. The unchanged limits include 300 N per-foot normal load, 43.2 Nm actuator torque, the original coefficient-0.5 L1 friction pyramid, 40 mm stability margin and 70 mm usable COP radius. The 60 kg Earth-prototype screening model uses a 1.3 load factor. These results are not lunar-soil measurements or failure probabilities.

The preregistered stop rule closes only the stated fixed-height/orientation family if its necessary normal-force bound exceeds 300 N. Search inside a closed family is recorded as unexecuted; there is no expansion to another geometry after observing the result.

## What was rectified in the software

- `models/cots_support_audit.py` checks raw force witnesses, support identities, force/moment equilibrium, unilateral support, the original L1 friction constraint, normal loads, torque including leg self-weight, COP and support margin. It also checks the reported summary against the recomputed quantities. A solver success flag cannot replace this evidence.
- Its separate contact-evidence check requires fresh touching, load-confirmation and non-slip inputs for each planned support. Tests demonstrate rejection of stale, unconfirmed and malformed synthetic evidence. This adds an offline check; it is not connected to the frozen monitor, and no physical load detector has been validated.
- `support_regions.py` constructs the intersection for **one common pre-loss body translation covering all possible additional losses**. A separate feasible translation for each possible failure is insufficient. Forces may vary between scenarios.
- Saved halfspaces and numerical certificates, raw force allocations, scenario identities and frozen hashes can be checked with `check_support_region_artifacts.py`. A separate GitHub Actions workflow reproduces the run.

The witness auditor is independent of the LP constraint assembly but shares the original kinematics, mass assumptions and software ecosystem. It is not an independent physical model. All release flags remain false, including hardware motion, fabrication and automatic recovery.

## Necessary mechanical bound

The registered family fixes the original hip locations, yaw ranges, body height/orientation, body-relative COM and uncertainty, and planar ankle height. It permits independent foot placement subject to the accepted IK convention and the inherited shaft envelope. This is broader than the common-sway family studied previously.

Let the hip-side distance be $H=0.26$ m. The unchanged 400 mm shaft arm, including the inherited 40 mm allowance, bounds the horizontal hip-to-ankle reach by

$$R=\sqrt{(0.400-0.040)^2-(0.300-0.055)^2}=0.263770734\ \mathrm{m}.$$

For a swing and additional loss on the same side, only one support remains on that side. The accepted yaw ranges keep all three opposite-side feet at $y\leq-H$; the sole same-side foot has $y\leq H+R$. Choose the original outward COM corner and outward 5 degree gravity case. The required projected centroid and total normal load are

$$Y=0.030+(0.310-0.055)\tan 5^\circ=0.052309609\ \mathrm{m},$$

$$W=60(1.3)(9.80665)\cos 5^\circ=762.007953\ \mathrm{N}.$$

Force and moment balance with nonnegative normal forces require

$$WY=\sum_i y_iN_i\leq(H+R)N_{\mathrm{sole}}-H(W-N_{\mathrm{sole}}),$$

so

$$N_{\mathrm{sole}}\geq W\frac{Y+H}{2H+R}=\mathbf{303.637781\ N}>300\ \mathrm{N}.$$

A separate relaxed four-normal-force LP reproduces this bound, with equilibrium residual below $10^{-13}$. Its favorable contact coordinates need not be attainable by the actual mechanism: granting them only makes this necessary bound more permissive. The mirrored argument covers the other side; the report retains a witness for each physical swing leg. Changing phase order or selecting independent foot positions within these premises cannot eliminate every such scenario.

**CLOSED_UNDER_EXPLICIT_PREMISES.** The inherited 40 mm allowance is part of the premise; it is not a newly measured mechanical clearance. This bound does not cover changed body height/orientation, a relocated COM, changed hips/yaw ranges, added support contacts, nonplanar contact models, or arbitrary redesigns. It neither authorizes a higher normal limit nor proves a feasible alternative. The flat, zero-uncertainty control stays below the cap, as required.

## Common support regions and reference replay

Each region intersects all four COM corners, all nine gravity vectors and all five possible extra losses at one sampled stance. The halfspaces encode capped normal-load centroids and the ordinary support polygon with its 40 mm inset. Torque, reach, collision and COP are omitted here, making these **necessary outer regions only**. A nonempty region would still require the complete original admission checks at the new body pose.

| Phase | Swing leg (one-based) | Original rejected / 900 | Common regions empty / 5 | Per-loss outer regions nonempty / 25 | Common signed slack (mm) |
|---|---:|---:|---:|---:|---:|
| 0 | 1 | 542 | 5 | 25 | -74.502 |
| 1 | 4 | 540 | 5 | 25 | -66.565 |
| 2 | 2 | 368 | 5 | 25 | -54.307 |
| 3 | 5 | 383 | 5 | 25 | -48.134 |
| 4 | 3 | 544 | 5 | 25 | -69.007 |
| 5 | 6 | 548 | 5 | 25 | -61.361 |

All **30 common regions are empty**, although all **150 individual-loss outer regions are nonempty**. Thus individual-loss body-position solutions cannot establish a common pre-loss solution. This diagnostic also explains why a planner with the wrong order of quantifiers could give a misleading positive result.

The signed slack is the maximum minimum normalized-halfspace slack, constant across the five samples of each phase up to floating-point tolerance. A negative value is a constraint inconsistency measure, **not a physical recovery distance**. Each empty result includes a checked floating-point dual combination with nonnegative weights, cancelled translation coefficients and a strictly negative right-hand side. These are numerical certificates, not exact-arithmetic proofs.

The full **6,480-case replay** matches every frozen reference decision: 1,080 nominal passes and 2,925 contingency rejections. All **3,555 feasible raw force witnesses** pass the new audit. There are zero encoding disagreements. Per-phase differences and earlier failure classifications remain in the [first investigation](../support_loss_01/README.md); no frozen failure was erased.

## Successful, unsuccessful and unexecuted work

**Successful software and analytical checks:** exact reference replay, raw-force audit, full scenario coverage, all 30 common-region certificates, all 150 per-loss necessary-region witnesses, mechanical bound/LP agreement, and positive/negative regression controls. Negative controls cover forged success, incorrect support identities, componentwise-friction false passes, omitted self-weight, negative/excessive normal force, stale/unconfirmed contacts and altered certificates.

**Unsuccessful feasibility hypotheses:** the registered fixed-height/orientation placement family cannot meet the unchanged normal cap for every original scenario; no original sampled stance has a common necessary body-translation region. These are bounded mathematical conclusions, not measured physical failures.

**UNEXECUTED_BY_NECESSARY_GATE:** independent-foot and body-path candidate search inside that family. **Zero new candidate configurations were scored.** The report explicitly records the stop rule and does not present this skipped search as an executed unsuccessful experiment.

**UNEXECUTED_OUT_OF_SCOPE:** changed body height/orientation, relocated COM, added supports, new CAD/interface geometry, continuous-envelope certification, physical sensing/calibration, dynamic recovery, hardware motion and fabrication. These require a separately justified and registered design investigation. No physical recovery capability is claimed.

## Reproduce and verify

From `weevil-lunar/`, with the repository analysis/development requirements installed:

```sh
python verification/cots/run_support_region_02.py --output /tmp/support-region-02
python verification/cots/check_support_region_artifacts.py --results-dir /tmp/support-region-02 --compare-committed
python -m pytest verification/tests/test_support_regions.py -q
```

Choose a new output directory: overwriting a previous run is refused. Interrupted runs retain an incomplete checkpoint. The runner succeeding means the declared experiment completed; it never means that the rover is admitted.

[results.json](results.json) records the configuration provenance, source/artifact hashes, runtime, controls, outcomes and release flags. [regions.json.gz](regions.json.gz) retains exact reference poses, every tagged halfspace, per-loss witnesses and common-region certificates. [replay.csv.gz](replay.csv.gz) retains the scenario keys, decisions and raw allocation JSON. Scenario swing/lost IDs are zero-based; lost `-1` means nominal. Human-readable witness leg IDs are one-based. Gzip timestamps are fixed. Cross-runtime reproduction compares decisions and bounded numeric differences rather than requiring identical compressed bytes.

Local validation: **162 existing unit tests and 28 new regression tests passed**; **two backend tests passed and two optional backend tests skipped**; Ruff and mypy passed. All 15 existing verification harnesses and the strict gate passed. The committed artifact checker verified all 6,480 cases, 3,555 force witnesses and 30 complete region records. Remote CI status is separate and is not asserted here.
