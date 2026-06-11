# Decision Memo — Weevil-Lunar Model Use, Claim Boundaries, and Validation Gate

Status: internal governance memo
Basis: `C:\Users\arren\.openclaw\workspace\robotics\bug2\physics_redteam_report.md`
Scope: contact and reduced-order leg model use inside `weevil-lunar/`

## Purpose

This memo is not a summary of the physics red-team. It is the governance artifact to use when someone is about to make a claim from this repo that the current model does not earn.

Its job is to do three things:

1. define what the scaffold is still genuinely useful for
2. prohibit specific recognizable claims that exceed the model's current support
3. define the single gate that must go green before real validation spend is justified

## Current project posture

The repo is currently:
- an exploratory research/prototype scaffold
- useful for design-space exploration and assumption organization
- not calibrated for predictive lunar leg/contact claims
- not ready to support hardware-validation spend on the current contact model as-is

The recent governance cleanup made the repo more honestly unvalidated. It did **not** make the underlying model validated.

## Still usable for

The current scaffold is approved for the following uses:

1. **Design-space exploration**
   - parameter sweeps
   - morphology what-if comparisons
   - qualitative reachability/traction thought experiments

2. **Assumption and dependency documentation**
   - making model assumptions explicit
   - exposing where gravity, preload, contact parameters, and geometry enter the stack
   - identifying which outputs depend on underived knobs versus physically constrained quantities

3. **Verification/governance scaffolding**
   - maintaining requirements-to-report mappings
   - preserving explicit separation between generated reports, baselines, and durable evidence snapshots
   - running sanity checks on reproducibility and artifact integrity

4. **Qualitative comparative reasoning only**
   - asking whether one toy configuration is better or worse than another under the current scaffold
   - surfacing where model outputs are highly sensitive to parameters or couplings
   - identifying which claims would require calibration or real-world data before they can be made

5. **Negative-use documentation**
   - explicitly documenting where the model is not reality-coupled
   - recording known limitations so later readers do not upgrade exploratory output into evidence

## Disallowed claims, by red-team finding

These are prohibitions, not suggestions. Each one is tied to a specific finding in the physics red-team report.

### Finding 1 — `k_phi` is unit-inconsistent; sane sinkage is coincidental

Until Finding 1 is closed:

- **No sinkage number may be quoted as physically predictive across morphology sweeps.**
- **No sinkage result may be generalized outside the narrow foot/load regime where outputs happened to look plausible.**
- **No slide, note, report, or caption may present sinkage values for changed foot radii or morphology variants as if they were calibrated physical estimates.**
- **No argument may use current sinkage outputs as evidence that a morphology is realistic, validated, or field-ready.**
- **No one may cite a sinkage result outside approximately the current nominal foot scale (`r ≈ 5 cm`) without an explicit note that Finding 1 remains open.**

Recognizable violation examples:
- “This beetle-foot variant only sinks 0.9 mm, so it is mechanically superior.”
- “The morphology sweep shows realistic sinkage across variants.”
- “These sinkage values are lunar-plausible” without explicit qualification that calibration is still broken.

### Finding 2 — gravity enters the contact physics nowhere

Until Finding 2 is closed:

- **No figure may be captioned or discussed as ‘lunar vs Earth’ performance if the distinction is coming from scenario labeling rather than a gravity-coupled load path.**
- **No output may be presented as evidence of Moon-vs-Earth behavior until gravity is actually threaded into the normal-load path.**
- **No claim may say the model answers how this leg behaves on the Moon relative to Earth.**
- **No preload-based comparison may be narrated as a gravity-based comparison unless preload is explicitly derived from `mass × g / n_stance` at a named site in the model path.**

Recognizable violation examples:
- “The lunar workspace is larger than Earth workspace” when `g` never enters the contact computation.
- “This model compares lunar and terrestrial traction.”
- “These plots show Moon-vs-Earth performance” when they only reflect externally chosen load values.

### Finding 3 — `cleat_gain` is an unbounded free multiplier on traction

Until Finding 3 is closed:

- **No traction margin may be cited as a physically grounded result while `cleat_gain` remains an underived free multiplier.**
- **No slope-rescue, anchoring, or traction-gate pass may be narrated as real performance evidence if the pass materially depends on `cleat_gain` or `twist_settle_gain`.**
- **No claim may present friction-cone or traction outputs as if they are constrained by physical cleat geometry when they are still driven by a raw gain knob.**
- **No stability margin may be used as decision-grade evidence for morphology choice, hardware direction, or expected field behavior while Finding 3 remains open.**

Recognizable violation examples:
- “The model shows adequate slope-rescue margin.”
- “Anchoring is validated in the current configuration.”
- “The cleat design yields this traction advantage” when the benefit is actually a free scalar.

### Findings 1–3 together

Until Findings 1–3 are closed together:

- **Do not describe the current contact/leg model as calibrated.**
- **Do not describe the repo as predictive of real lunar leg performance.**
- **Do not use current outputs as justification for hardware-validation spend.**
- **Do not cite this scaffold as evidence that the design is ready for real-world lunar-contact testing.**

## Approved claims, while findings remain open

The following statements are allowed and encouraged because they are honest to the current state:

- “This repo is an exploratory scaffold for design-space reasoning.”
- “These outputs are qualitative and assumption-sensitive, not calibrated field predictions.”
- “The model contains standard equation forms but remains uncalibrated in key parameters and couplings.”
- “Moon-vs-Earth claims are not yet supported because gravity is not yet coupled into the load path.”
- “Traction-sensitive outputs remain contingent on an underived cleat-gain term.”
- “This package is useful for organizing assumptions and identifying what would need real validation.”

## Validation-spend gate

Real validation spend is locked until the following single gate is green:

**Re-run the same physics red-team and have Findings 1–3 come back closed.**

That gate requires all three conditions below.

### Gate condition A — Finding 1 closed

`k_phi` must be re-derived from a cited source with explicit unit handling, and all of the following must be true:
- the derivation is documented with units
- a unit-consistency test against a cited pressure-sinkage or bevameter curve passes
- the radius/morphology sweep remains within a physically sane band rather than only looking plausible at one nominal foot size

### Gate condition B — Finding 2 closed

Gravity must become mechanistically real in the model path, and all of the following must be true:
- `normal_load` is derived at one named place from body/load assumptions rather than treated as a floating preload constant
- the gravity/body-mass dependence is explicit and testable
- Moon-vs-Earth outputs differ because the model path includes gravity coupling, not because scripts inject arbitrary load differences upstream

### Gate condition C — Finding 3 closed

`cleat_gain` must either be physically derived and bounded or removed, and all of the following must be true:
- traction amplification is tied to a stated physical mechanism or is absent
- any cap or constraint is documented and tested
- traction/slope margins no longer depend on a free unconstrained multiplier

If any one of A, B, or C is still open, the validation-spend gate remains closed.

## Decision rule after the gate

Passing the gate does **not** mean the model is validated.
It means the model has earned the right to be considered for the next, more expensive conversation.

Only after the gate is green should the project ask whether hardware-in-the-loop, simulant testing, or other reality-contact validation deserves budget.

## Method note

The physics red-team that underwrites this memo visibly retracted two of its own preliminary claims after checking them against the literature and the model outputs.

That is not a weakness to hide. It is one reason this memo should be trusted.
A critique willing to correct itself is more trustworthy than one that arrives with false neatness.

Those retractions mean:
- fixes must be demonstrated, not asserted
- parameter/unit repairs must be checked against cited curves
- apparent plausibility in a narrow regime is not enough to upgrade confidence

## Operational takeaway

Use this repo as:
- a cheap thinking tool
- a governance scaffold
- an assumption map

Do not use it as:
- a predictive lunar-contact model
- evidence of Moon-vs-Earth comparative behavior
- justification for validation spend

Until Findings 1–3 are closed, the correct narrative is:

**useful scaffold, honest prototype, not yet calibration-worthy evidence.**
