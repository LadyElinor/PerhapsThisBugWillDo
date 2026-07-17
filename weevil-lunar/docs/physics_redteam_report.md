# Physics Red-Team — Weevil-Lunar Contact & Leg Models

Scope: `weevil-lunar/models/contact/regolith_contact_model.py` and the
reduced-order leg model. This is an adversarial review of the *physics*, not
the code quality (covered separately). The goal is to find where the model
would misrepresent reality, sorted by how badly and how quietly it does so.

Three failure classes were checked: **formulation** (wrong equations),
**parameters** (wrong constants), and **coupling/abstraction** (each piece
fine alone, but the composition drops something that matters).

A note on method: two preliminary claims in this review were checked against
the literature and **retracted** when the numbers contradicted them. Those
retractions are kept visible below, a red-team that hides its own misfires
is not trustworthy.

---

## SUMMARY OF FINDINGS

| # | Class | Severity | One line |
|---|-------|----------|----------|
| 1 | Parameter | **CRITICAL** | Bekker parameters are unprovenanced, and the model does not enforce the cited fit's validity envelope |
| 2 | Coupling | **CRITICAL** | Gravity enters the contact physics nowhere, the model cannot compare Moon vs Earth |
| 3 | Formulation | **HIGH** | `cleat_gain` is an unbounded free multiplier on traction with no physical basis |
| 4 | Formulation | LOW | Mohr-Coulomb form is correct; cohesion term is numerically negligible (not a bug) |
| 5 | Parameter | LOW | `k_c`, `phi`, `cohesion`, `density` are individually within literature ranges |

**Headline:** the contact model is not calibrated. Its Bekker parameters are
uncited and unguarded against invalid regimes, and it has no gravity term, so
it cannot answer the question the project is named for.

---

## FINDING 1 — Bekker parameters are unprovenanced and the validity envelope is unenforced (CRITICAL, parameter)

`bearing_capacity()` implements the standard Bekker-Wong form
`p = (k_c/b + k_phi) * z^n`, intended as p in kPa, b and z in metres. The
equation form is correct and the `b = foot radius` convention is supported by
the literature.

The problem is now understood more precisely than in earlier passes. The model
uses uncited Bekker parameters:

| type | k_c | k_phi | n |
|------|-----|-------|---|
| MARE | 0.9 | 1528.0 | 1.0 |
| HIGHLAND | 0.5 | 820.0 | 1.1 |
| COMPACTED | 2.0 | 3500.0 | 0.8 |

Primary-data recovery from Lim et al. (2021) Tables 3–4 showed that an earlier
claim that these `k_phi` values were "~400–1700× too large" was itself a
cross-unit comparison error and is retracted. The model's `k_phi` values sit
inside the published cross-material range when one consistent convention is
used, and the MARE value 1528 matches the published dry-sand value from Wong
(2001) exactly. That does **not** clear Finding 1. It changes what Finding 1
is.

**The actual bug:** the parameter set is **uncited and unprovenanced**, and a
properly cited lunar fit comes with a bounded validity envelope the model does
not enforce. The extracted KLS-1 fit is:

- `n = 1.2594`
- `k_c = -44.0554 kN/m^(n+1)`
- `k_phi = 3581.8106 kN/m^(n+2)`

under specific fitted conditions: KLS-1 simulant, density 1602 kg/m³, Earth
gravity, plate radii 30 / 35 / 37.5 mm, and loads up to 889.64 N.

That fit creates two concrete hazards:

1. **`n > 1` makes extrapolation hazardous.** Outside the fitted load and plate
   regime, sinkage grows by extrapolating an already unusual concave-up curve.
2. **Negative `k_c` creates a small-foot failure region.** Because the model
   computes `k_eq = k_c/b + k_phi`, the cited fit crosses `k_eq = 0` at about
   `b = 12.3 mm` radius. Below that, predicted pressure goes negative and the
   model is physically meaningless.

The nominal Weevil foot is safely above that threshold, but the morphology
sweep varies foot geometry. Without a validity-envelope guard, the model can
silently report output from an invalid regime. **This is the highest-priority
physics fix.**

---

## FINDING 2 — gravity/load-path coupling remains only partially repaired (CRITICAL, coupling)

Original defect: `RegolithContactModel.__init__` took `gravity = 1.62` and
stored it, but no method read `self.gravity`; all contact forces were driven by
caller-supplied `normal_load` values in Newtons. The lunar-vs-Earth distinction
therefore lived entirely in whatever the caller injected upstream.

That original defect has now been **partially repaired** in the codebase:
- the contact boundary exposes named gravity-coupled load helpers rather than
  leaving gravity entirely implicit
- the reduced-order/contact-facing path makes the load derivation contract more
  explicit
- scenario, receipt, and comparative-artifact schemas now record `load_path`
  semantics (`gravity_coupled` vs `externally_injected`)
- tests now enforce default/declared load-path behavior and backend receipt
  propagation

Those are real improvements. They make the abstraction boundary legible,
machine-visible, and testable.

But **Finding 2 remains open** under this red-team's original standard.
The repo still has not earned a blanket Moon-vs-Earth claim merely because the
contract is now explicit. Closure still requires a stronger proof that gravity
is mechanistically real across the full model path, not just named and carried
through the contract surface.

**Current consequence:** the repo is no longer accurately described as purely
gravity-blind at the contract boundary, but it is still not justified to claim
that the model answers Moon-vs-Earth behavior as validated comparative physics.

This remains the same class as the earlier Bug 2: the critical issue is the
abstraction boundary between where weight is computed and where contact is
computed. The recent repair made that boundary explicit; full closure still
requires proving that the explicit boundary is the authoritative mechanism
across the relevant model paths.

---

## FINDING 3 — `cleat_gain` is an unbounded free multiplier (HIGH, formulation)

`compute_contact_forces_with_preload` multiplies the Mohr-Coulomb shear by
`cleat_gain_forward/lateral` (default 1.0, used up to ~2.0) and again by a
`twist_settle_gain`. The resulting friction-cone angle:

```
 cleat_gain 1.0, settle 1.0 : cone = 35.7 deg
 cleat_gain 1.5, settle 1.3 : cone = 54.5 deg
 cleat_gain 2.0, settle 1.5 : cone = 65.1 deg
```

A friction-cone angle above ~45° asserts the foot resists a lateral force
*larger than the normal load*. Cleats biting into regolith genuinely can add
mechanical interlock beyond pure friction, so this is not impossible — but the
model gives `cleat_gain` **no upper bound and no physical derivation**. It is a
free knob that multiplies traction directly, and the verification suite's
"slope rescue" and "anchoring" gates pass or fail based substantially on it.
Whatever margin those gates report is only as real as a number with no
physical basis. Same family as Finding 2 and the earlier Bug 2: an unphysical
multiplier silently sized to make downstream checks pass.

A defensible model would derive cleat benefit from cleat geometry and
regolith shear strength (a passive-earth-pressure or interlock term) and cap
it, rather than exposing a raw gain.

---

## FINDING 4 — Mohr-Coulomb form correct, cohesion negligible (LOW, not a bug)

`mohr_coulomb_shear` computes `c·A + N·tan(phi)`, the correct total-shear-force
form of `tau = c + sigma·tan(phi)`. No error.

Observation, not a defect: for the small feet modelled (r = 5 cm), the
cohesion term contributes <1 N against ~30 N of friction, because `c·A`
shrinks with area while `N·tan(phi)` does not. The model is effectively
friction-only; cohesion is decorative at this scale. Worth knowing because
real lunar regolith cohesion, while small, is not *this* irrelevant — on a
larger pad it would matter. Flagging so nobody trusts the cohesion knob to do
something it currently can't.

---

## FINDING 5 — individually-plausible parameters (LOW, parameter)

`k_c` (0.5–2.0), `phi` (35–40°), `cohesion` (0.05–0.40 kPa) and `density`
(1300–1800 kg/m³) all sit within published lunar-regolith and simulant ranges.
Recent Chang'e-6 far-side DEM work reports phi ≈ 48° and cohesion ≈ 1 kPa as an
upper bound; the model's values are conservative-to-central against that. No
action needed beyond labelling them as POC buckets, which the code already
does. The contrast with Finding 1 is the point: every parameter *except*
`k_phi` is reasonable, which is exactly why the `k_phi` error is easy to miss.

---

## VERDICT

The contact model has the right *equations* (Bekker-Wong, Mohr-Coulomb,
friction cone — all standard and correctly coded as formulas). It fails on
**calibration and coupling**, not on form:

- Bekker parameters are uncited and the model does not enforce the valid
  regime of any cited fit, so morphology-dependent outputs can silently leave
  the physically meaningful regime (Finding 1).
- Gravity is structurally absent, so Moon-vs-Earth claims have no mechanism
  (Finding 2).
- Traction rests partly on an unbounded, underived `cleat_gain` (Finding 3).

None of these is exotic. All three are the same recurring failure this project
has shown throughout: a number or factor inserted to make things work
downstream, without the physical reasoning that would constrain it. The model
is a reasonable *scaffold* of the right equations; it is **not calibrated** and
should not be read as predictive of real lunar leg performance.

## RECOMMENDED SEQUENCE

1. **Repair Bekker parameter provenance and enforce the validity envelope** —
   adopt a single cited source with explicit source conditions; add a
   curve-reproduction test (known load + plate size → known sinkage from a
   published bevameter curve); and refuse or loudly flag evaluations outside
   the fitted regime, including any case where `k_eq <= 0`. Highest priority;
   everything downstream depends on it.
2. **Thread gravity through** — define `normal_load = mass × g / n_stance` at
   one named site; make `g` actually reach the contact model or be applied
   immediately before it. Until then, label all "lunar" outputs as un-gravity-
   coupled.
3. **Constrain or remove `cleat_gain`** — derive cleat benefit from geometry +
   shear strength with a physical cap, or drop the multiplier and state that
   traction is friction-only pending a real cleat model.
4. **Add physical-sanity tests**, not just numeric-regression tests: sinkage
   monotonic *and within a realistic band* across the morphology sweep; friction
   cone bounded; traction zero at zero load. The current suite locks in
   whatever the model does, including the coincidental-but-wrong behavior.

## METHOD NOTE

Two claims in early passes ("1000× too little sinkage"; a later claim that the
model's `k_phi` was orders of magnitude too large) were retracted after
checking against the data — the first because the model's output is actually in
range, the second because primary-data recovery showed the magnitude comparison
crossed unit conventions. The retractions are the method working: the same
adversarial check applied to one's own conclusions. Any fix to the Bekker
parameter set must be validated against a real pressure-sinkage curve and a
stated validity envelope, not asserted.
