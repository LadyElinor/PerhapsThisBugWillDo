# Tranche 03: correction verification

**The declared chassis repair passes its checks. Whole-assembly clearance and universal support-loss recovery do not pass.** Ten original overlaps are removed, 60 remain, and all six phases fail the static contingency admission check. Hardware motion and fabrication remain blocked.

## Frozen specification

[spec.json](spec.json) was committed before evaluation, against parent `99e607062a8c7a221458bb13a6cffa0dbec900e3`. It defines four deck passages, equipment and rail translations, a conservative COM increment, exact target pairs, preservation of all component envelopes, no new overlaps, and unchanged load/cap assumptions. Original COTS-1 configuration, model, BOM and CAD hashes are checked before execution. The original tranche 02 reports are not overwritten.

This is a deterministic corrective design based on observed geometric causes. It is not independent experimental confirmation of the original design, a statistical optimization, or a hardware holdout. The sampled pose grid is reused to demonstrate the specified repair. No continuous-motion proof is claimed.

## Results

| Test | Result |
|---|---|
| Full modeled-solid inventory | 86 solids retained; all commercial envelope volumes preserved |
| All-pair geometry screen | 113,305 pair checks over 31 poses |
| Original overlapping pairs | 70 accounted for individually |
| Declared chassis/landing overlap corrections | 10 removed; no new pairs |
| Remaining overlaps | 60 unfinished leg interfaces; none waived |
| Guide/deck, guide/equipment, equipment/roof gaps | 2 mm radial, 8 mm, 27 mm nominal minima |
| STEP export/reimport | 86 valid solids; relative volume error below 10⁻⁸ |
| Revised nominal statics, COM raised 10 mm, ≤5° | 1,080 / 1,080 pass sampled constraints |
| Additional supporting-foot loss | 2,925 / 5,400 fail the static constraints |
| Whole-phase static contingency admission | 0 / 6 phases admitted |
| Physical tests | None; no physical gate closed |

Full results, hashes, first rejected cases, overlap volumes and the 70-pair issue ledger are in [results.json](results.json). Each leg contributes three motor/carrier overlaps, five carrier/link overlaps, one knee stock overlap and one tibia/sensor overlap. They require completed assemblies and supported load paths, not deletion of their envelopes.

Raising the modeled COM changes the support-loss rejection count from 2,921 in tranche 02 to 2,925 here. The repair does not improve that fault response. These counts are conditional mathematical cases, not measured failure rates or fall probabilities. A static feasible wrench after loss would not establish transient recovery either. The revised nominal cases preserve the 1.3 sizing factor, 43.2 Nm torque cap, 300 N contact cap, 40 mm support margin and assumed friction coefficient 0.5.

## Controls and software behavior

The unchanged all-pairs checker recovers the planted 100 mm³ box overlap and distinguishes touching/separated boxes. The revision checker verifies names, component counts, solid validity and volumes, so shrinking or deleting an equipment envelope cannot silently remove a collision. Only the four declared deck passages may remove material. Both exact targeted-pair elimination and absence of new pairs are enforced; a worsening correction exits with an error.

The offline preflight independently checks margin, COP, limits and residuals after solver success and refuses incomplete generated phases. Fault-injection tests exercise contact loss, contact relabeling, premature swing changes, missing channels, malformed flags, nonfinite timing, backward/duplicate clocks, 40 ms feedback staleness and 100 ms heartbeat timeout. Faults stay latched until explicit rearm with six fresh contacts and restraint confirmation. Synthetic successful sequences remain non-evidence; `hardware_motion_allowed` is always false.

Local validation passes: **142 unit tests** (35 new correction tests), **two backend tests** with two optional skips, Ruff, mypy, and all 15 existing verification scripts plus their strict/traceability gates. The latter are software checks, not physical test results. The project tests include failure injections and checks binding the report to source hashes. CAD runs in the optional CAD CI job; ordinary unit tests do not silently require CadQuery. A green correction job means these narrowly specified fixes and regressions passed, not that the remaining mechanical or recovery claims passed.

## Remaining blockers

The deck holes are passages, not finished guide mounts. Deck stiffness, guide retention and reinforcement, rail attachments, landing peak forces, park stops, tolerance stacks, all 60 leg interfaces, cables and fasteners remain unverified. The new STEP continues to expose incomplete geometry. The corrected design and detailed closure criteria are in [COTS-1.1](../../../design/cots_v1_1/README.md).

Physical evidence for holding temperature, actual mass/COM, electrical transients and restrained fault response remains absent. No simulated control sequence or absence of modeled collision closes those gates. The blank tranche 02 bench manifest remains SOURCE-GATED.

## Reproduce

From `weevil-lunar/` with the existing analysis and optional CAD requirements installed:

```sh
python verification/cots/run_tranche_03.py --output /tmp/cots-corrections.json
python cad/scripts/build_cots_revision.py --output /tmp/cots-cad-revision
python -m pytest verification/tests/test_cots_corrections.py -q
```

The runner exits 0 only when the declared correction checks pass; its output still explicitly denies fabrication and hardware motion. An existing export directory is refused to avoid accidentally replacing a prior CAD deliverable. The old tests remain independently reproducible with their original commands.
