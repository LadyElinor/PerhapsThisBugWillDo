# Parametric fixtures and verified CAD handoff

This workflow builds **five editable fixture concepts**, screens their geometry,
and exports only selected physical solids. It does not yet build an assembled
leg or a complete rover. Tested with FreeCAD 1.1.4 / OCCT 7.8.1.

## Build in FreeCAD

1. Open `cad/Build_ParametricFixtures.FCMacro` from the checked-out repository and
   execute it in FreeCAD. Keep the macro next to its `scripts` directory.
2. Edit the `Params` spreadsheet and recompute. Dimensions are native expressions
   on PartDesign features. They continue to work after saving/reopening the FCStd
   without a Python proxy or this repository on the Python import path.
3. Inspect the `DesignNotes` object. The bodies are spaced 60 mm apart for viewing;
   this is not a neutral stance or a validated joint assembly.
4. Run `cad/Phase2_Export.FCMacro`. It uses `cad/fixture_selection.json` and writes
   to a new timestamped folder under `cad/exports/generated/`. It refuses invalid
   geometry and never exports every object in the document.

The export folder contains `Fixtures.FCStd`, `fixtures_ap242.step`, and
`audit.json`. The receipt records the observed schema, hashes, shape measurements,
limitations and round-trip result. The default manifest contains no densities:
mass/inertia remain null until an explicit material density is supplied.

Set `WEEVIL_SELECTION` to another explicit JSON manifest and `WEEVIL_EXPORT_DIR`
to a new output directory when needed. Existing output directories are refused.
The macro sets process-wide OCCT STEP writer options; the standalone CLI below
isolates those options in its own process.

## Headless Linux workflow

Download the pinned official release and verify it before extraction:

```bash
curl -fL -o FreeCAD.AppImage https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage
echo "f6dc6ba676e5ac96a565ebc8d657232f94c6158e85b4352141bd1a46f6b43434  FreeCAD.AppImage" | sha256sum -c -
chmod +x FreeCAD.AppImage
./FreeCAD.AppImage --appimage-extract > /dev/null
```

From `weevil-lunar/`, replace `/path/to/squashfs-root` with the extracted runtime:

```bash
bash cad/scripts/run_freecad_python.sh /path/to/squashfs-root \
  cad/scripts/build_parametric_fixtures.py --output cad/exports/generated/run-01

bash cad/scripts/run_freecad_python.sh /path/to/squashfs-root \
  cad/scripts/freecad_audit.py cad/exports/generated/run-01/Fixtures.FCStd \
  cad/exports/generated/run-01/selection.json \
  --report cad/exports/generated/run-01/audit.json \
  --step cad/exports/generated/run-01/fixtures_ap242.step

bash cad/scripts/run_freecad_python.sh /path/to/squashfs-root \
  verification/freecad/check_freecad_pipeline.py
```

The builder refuses an existing output directory. The audit returns 0 on pass,
2 on a completed but failed audit, and nonzero for invalid inputs or setup errors.
An existing STEP output is never overwritten. A failed geometry audit cannot
publish a STEP. New outputs are ignored by git; freeze reviewed snapshots at a
deliberate design milestone.

## What is modeled

| Body | Native features | Remaining design work |
|---|---|---|
| Adapter blank | Cylinder and minor-diameter pilot bore | Real spline profile, fit, bolt ligament and tolerances |
| Pivot flange | Hub, bore, bolt cut and live polar pattern | Bearing/mount interface and load validation |
| Servo mount | Plate, ears, four through-bores | Actual actuator envelope, fit and attachment |
| Right-angle mount | Two plates and a web | Mounting interfaces and load path |
| Actuation lever | Hub, arm and tip bore | Hub connection, joints and tolerances |

The adapter is deliberately named **blank**. The old parameters specify OD 10 mm,
bolt circle 8 mm and holes 2 mm, giving zero outer ligament. No nominal spline
tooth profile is specified. The builder retains the source dimensions and omits
those bolt holes and teeth; it does not invent a manufacturable connector.
Servo bores now pass through the entire ear depth, rather than just the thin
central plate. This remains a concept to check against the selected actuator.

Canonical leg values come from `weevil_leg_params.yaml`. Fixture dimensions come
from the existing `phase2_defaults()` catalog in `generate_csvs_from_yaml.py`;
inherited concept ratios are visible in `Params`. `DesignNotes.ParameterSHA256`
records the initial YAML, not a promise that later spreadsheet edits match it.
Review and reconcile those edits before treating a variant as a canonical design.

## Audit contract and units

The manifest selects **internal object Names**, not display Labels. One selected
body/feature represents one physical solid. Aggregate groups and unresolved links
are rejected; single-solid PartDesign wrappers are supported. Example:

```json
{
  "design_status": "concept",
  "minimum_clearance_mm": 0.1,
  "objects": [
    {"name": "Body_PivotFlange", "density_kg_m3": 2700},
    {"name": "Body_ActuationLever25"}
  ]
}
```

The density and clearance above are examples, not rover material/tolerance
decisions. Use the actual material's warranted density and interface allowance.
`allow_touching_pairs` can waive the clearance threshold for named mating pairs;
it never permits volume overlap or coincident duplicates.

- CAD geometry: mm; volume: mm³; physical mass: kg.
- Mass = volume × density × 10⁻⁹.
- Inertia = geometric inertia in mm⁵ × density × 10⁻¹⁵, yielding kg·m².
- Reported inertia is about each solid COM in axes parallel to world axes.
  Rotate it into the intended link frame and specify the inertial origin before
  using it in URDF. Use the parallel-axis theorem for a different reference point.
- Homogeneous density is assumed. Mixed materials require separately modeled
  solids and an explicit mass-property aggregation step.
- AP242DIS is explicitly requested and `FILE_SCHEMA` checked after export.
  This does not certify AP242 Ed2 or semantic PMI.
- Reimport checks topology, solid count, total volume and per-solid spatial overlap.
  This does not preserve constraints, feature history or materials in STEP.
- Static clearance screening is not a continuous-motion collision proof or
  structural/thermal/lunar qualification.

## Screw travel and simulation

```bash
python cad/scripts/kinematic_report.py --output verification/reports/screw_travel.json
```

The current 13.5 mm/revolution lead and ±60° range produce **4.5 mm** total operating
travel, using 12.86% of the 35 mm mechanical cap. Full-stroke rotation would be
933.33°. The report makes this distinction explicit without silently changing
design parameters. The reduced-order model marks states beyond either the
rotation range or mechanical stroke as unreachable; state sampling uses their
intersection. Reported coordinates for unreachable states remain clipped
diagnostics and must not be accepted as reachable poses.

Before generating a dynamics-ready URDF, settle link origins, axes, materials,
actuator limits and supported screw coupling. The four empty links in the old
URDF do not supply these. A fictitious complete URDF would conceal the gap.

## Historical bundle and CI

The old `cad/export/` bundle is preserved for provenance. Its STEP is actually
AP214, its FCStd is nonparametric seed geometry, and its URDF is incomplete.
`verification/test_phase2_export_bundle.py` inspects their contents and reports
three explicit failures. The harness manifest declares these baseline failures
so that a change in either direction requires review. Its contract can pass
while `evidence_pass` stays false and CAD findings remain listed in receipts.
Presence of files alone is no longer described as successful CAD validation.

CI runs the ordinary unit, lint, type, receipt and benchmark gates, plus a separate
pinned FreeCAD job. Native checks cover analytic mass/inertia, nested transforms,
contact versus overlap, invalid inputs, export round trips, saved/reopened
parameter sweeps, dynamic bolt counts and stale-geometry rejection.

## Next mechanical milestone

Define and assemble the actual coxa/femur/tibia/foot interfaces, decide the screw
operating range, assign justified materials, and sample real assembled poses.
Then derive link-frame inertials and simulation geometry. Keep regolith contact,
strength, dust, thermal and hardware validation as separate evidence streams.
