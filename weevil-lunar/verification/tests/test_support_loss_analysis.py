"""Regression and negative controls for the offline support-loss investigation."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "verification/cots"))
import support_loss_analysis as study
import run_support_loss_01 as runner


@pytest.fixture
def baseline():
    return study.frozen_inputs()[1]


def test_frozen_input_tampering_fails_closed(tmp_path):
    spec, _ = study.frozen_inputs()
    spec["frozen_inputs_sha256"]["models/cots_rover.py"] = "0"*64
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="Frozen input changed"):
        study.frozen_inputs(path)


@pytest.mark.parametrize("variant", [
    {"id": "bad", "normal_force_limit_n": 400}, {"id": "bad", "reach_m": .281},
    {"id": "bad", "sway_m": float("nan")}, {"id": "bad", "stride_m": True},
    {"id": "bad", "order": [0, 0, 1, 2, 3, 4]}, {"id": "bad", "order": [True, 0, 2, 3, 4, 5]},
])
def test_limit_relaxations_and_invalid_candidates_rejected(baseline, variant):
    with pytest.raises(ValueError):
        study.configuration(baseline, variant)


def test_default_gait_matches_frozen_generator_at_dense_positions(baseline):
    for old, new in zip(study.rover.gait_samples(baseline, 100), study.poses(baseline, {"id": "baseline"}, 100)):
        assert old[2] == new[4]
        np.testing.assert_allclose(old[1], new[3], atol=1e-14, rtol=0)


def test_all_registered_variants_preserve_limits_and_mass(baseline):
    spec, _ = study.frozen_inputs()
    for variant in spec["candidates"]:
        c, _ = study.configuration(baseline, variant)
        c["nominal_radial_reach_m"] = baseline["nominal_radial_reach_m"]
        c["screening"]["step_length_m"] = baseline["screening"]["step_length_m"]
        assert c == baseline


def test_reordered_sway_is_continuous_and_stance_translation_is_common(baseline):
    v = {"id": "test", "order": [5, 2, 4, 1, 3, 0], "sway_m": .04}
    samples = list(study.poses(baseline, v))
    for phase in range(6):
        np.testing.assert_allclose(samples[phase*5+4][3], samples[((phase+1)*5) % 30][3], atol=1e-14)
        for a, b in zip(samples[phase*5:phase*5+4], samples[phase*5+1:phase*5+5]):
            displacements = (b[3] - a[3])[list(a[4])]
            np.testing.assert_allclose(displacements, np.tile(displacements[0], (5, 1)), atol=1e-14)


def test_independent_positive_and_planted_negative_controls(baseline):
    assert all(study.controls(baseline).values())


def test_conflict_is_deletion_minimal_for_known_load_shortfall(baseline):
    c = copy.deepcopy(baseline)
    c["screening"]["normal_force_limit_n"] = 100.
    lp = study.WrenchLP(c, study.rover.nominal_feet(c), tuple(range(6)), np.array(c["com_m"]),
                       np.array([0., 0., -c["earth_gravity_m_s2"]]))
    conflict = lp.conflict()
    assert conflict == ["normal_cap"]
    assert not lp.solve(conflict)
    assert lp.solve([])


def test_solver_unknown_is_not_labeled_infeasible(baseline, monkeypatch):
    monkeypatch.setattr(study, "linprog", lambda *a, **kw: SimpleNamespace(success=False, status=4, message="unknown"))
    lp = study.WrenchLP(baseline, study.rover.nominal_feet(baseline), tuple(range(6)),
                       np.array(baseline["com_m"]), np.array([0., 0., -9.80665]))
    with pytest.raises(RuntimeError, match="Indeterminate"):
        lp.solve()


def test_forged_success_force_witness_is_rejected(baseline, monkeypatch):
    real = study.rover.allocate
    def forged(*args):
        r = real(*args)
        assert r["feasible"]
        r["forces_n"] = np.zeros_like(r["forces_n"]).tolist()
        r["force_residual_n"] = r["moment_residual_nm"] = 0.
        return r
    monkeypatch.setattr(study.rover, "allocate", forged)
    with pytest.raises(ValueError, match="witness violates"):
        study.case_result(baseline, study.rover.nominal_feet(baseline), tuple(range(6)),
                          np.array(baseline["com_m"]), np.array([0., 0., -9.80665]))


def test_margin_classified_when_original_guard_returns_early(baseline):
    _, _, _, feet, active = next(study.poses(baseline, {"id": "baseline"}))
    supports = tuple(i for i in active if i != 1)
    concurrent = []
    for *_, com, gravity in study.load_cases(baseline):
        r = study.case_result(baseline, feet, supports, com, gravity)
        if r["margin_m"] < .04 - 1e-9 and not r["allocation"]["feasible"]:
            concurrent.append(r)
            assert {"wrench_infeasible", "support_margin_m"} <= set(r["reasons"])
    assert concurrent


def test_missing_scenarios_and_existing_output_refused(tmp_path):
    with pytest.raises(ValueError, match="coverage"):
        runner.check_coverage({})
    with pytest.raises(ValueError, match="existing output"):
        runner.run(tmp_path)


def test_paired_ids_compare_physical_swing_and_loss_not_phase(baseline):
    ids = []
    for order in ([0, 3, 1, 4, 2, 5], [5, 2, 4, 1, 3, 0]):
        rows = {}
        for phase, sample, swing, _, active in study.poses(baseline, {"id": "test", "order": order}):
            for lost in (-1, *active):
                for sx, sy, gid, *_ in study.load_cases(baseline):
                    rows[(swing, sample, lost, sx, sy, gid)] = phase
        runner.check_coverage(rows)
        ids.append(rows)
    assert set(ids[0]) == set(ids[1])
    assert ids[0] != ids[1]


def test_committed_results_bound_to_inputs_and_safety_blocks():
    path = study.SPEC.with_name("results.json")
    if not path.exists():
        pytest.skip("Full experiment artifacts not generated yet")
    r = json.loads(path.read_text())
    assert r["complete"] and all(r["controls"].values())
    assert r["spec_sha256"] == study.sha256(study.SPEC)
    for name, expected in r["source_sha256"].items():
        assert study.sha256(study.SPEC.parent.parent / name) == expected
    for name, expected in r["frozen_inputs_sha256"].items():
        assert study.sha256(ROOT / name) == expected
    assert r["raw_cases_sha256"] == study.sha256(path.with_name("cases.csv.gz"))
    assert r["poses_sha256"] == study.sha256(path.with_name("poses.json"))
    assert not any(r[k] for k in ("hardware_motion_allowed", "fabrication_released", "dynamic_recovery_proven", "automatic_recovery_allowed"))
    assert r["independent_encoding_disagreements"] == 0
    spec, _ = study.frozen_inputs()
    assert [v["parameters"] for v in r["variants"]] == spec["candidates"]
    b = r["variants"][0]
    assert b["counts"] == {"nominal_cases":1080,"nominal_rejected":0,"loss_cases":5400,"loss_rejected":2925}
    assert [b["phases"][str(p)]["loss_rejected"] for p in range(6)] == [542,540,368,383,544,548]


def test_capped_polygon_vertices_exclude_com_despite_uncapped_inclusion():
    from explain_support_loss import capped_polygon, polygon_margin
    feet = np.array([[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]])
    capped = capped_polygon(feet, 100., 30.)
    assert polygon_margin(capped, [0., 0.])[0] > 0
    assert polygon_margin(capped, [.9, 0.])[0] < 0
    assert capped_polygon(feet, 121., 30.).size == 0
    # Removing the cap recovers the ordinary square's feasible centroid region.
    uncapped = capped_polygon(feet, 100., 100.)
    assert polygon_margin(uncapped, [.9, 0.])[0] > 0


def test_family_bound_and_shaft_arm_limit_remain_binding():
    import check_support_family_bound as bound
    r = bound.run()
    assert r["family_minimum_required_normal_n"] == pytest.approx(356.65027108139117)
    assert all(v["exceeds_300n_cap"] for v in r["variants"].values())
    assert r["variants"]["baseline"]["original_400mm_shaft_arm_bound_satisfied"]
    assert not r["variants"]["reach_280mm"]["original_400mm_shaft_arm_bound_satisfied"]
    assert not r["hardware_motion_allowed"]
