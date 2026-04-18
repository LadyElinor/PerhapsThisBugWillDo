# Fresh Crater Risk Register (v0.1)

## Scope
Initial risks for the fresh-crater explorer mission thread and its admitted CAD asset set.

| Risk ID | Description | Impact | Initial mitigation |
|---|---|---|---|
| FCR-001 | Reduced-order contact model underestimates loose ejecta sinkage and edge disturbance | false confidence in rim approach envelopes | keep disturbance and slip limits conservative in v0.1 profiles |
| FCR-002 | Line-of-sight occlusion during edge work reduces operator awareness | delayed fault response | require telemetry buffering and egress reserve in all fresh-crater variants |
| FCR-003 | Geometry-only STEP assets are mistaken for build-qualified components | governance drift / premature hardware commitment | mark admitted assets with evidence tier and synthetic flag |
| FCR-004 | Synthetic actuator blends are treated as physical candidates | invalid design trades | exclude synthetic-only assets from buildable candidate set |
| FCR-005 | Partial descent profile consumes too much reserve for safe retreat | mission loss / entrapment risk | require minimum egress reserve and slip abort threshold |
| FCR-006 | Fractured rim edges create snag or belly-strike conditions outside nominal slope model | mobility failure | maintain edge standoff requirement and guarded descent limit |

## Asset-specific governance
- `params_apex_AE060_equiv_blend.json` is analysis-only until backed by a normalized STEP and explicit admission review.
- Imported STEP candidates are treated as geometry evidence, not manufacturing readiness proof.
- Build decisions should preserve source path, normalized path, intended role, and evidence tier.
