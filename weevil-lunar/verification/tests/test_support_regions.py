"""Independent controls for constraint preservation and robust-loss quantifiers."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "verification/cots"))
import support_loss_analysis as study
import support_regions as regions
from models.cots_support_audit import ContactEvidence, assess_support_evidence, audit_allocation


@pytest.fixture
def inputs():
    _, c = study.frozen_inputs()
    feet = study.rover.nominal_feet(c)
    active, com, g = tuple(range(6)), np.array(c["com_m"]), np.array([0.,0.,-c["earth_gravity_m_s2"]])
    r = study.rover.allocate(c, feet, active, com, g, c["screening"]["load_factor"])
    return c, feet, active, com, g, r


def test_true_force_witness_passes_without_hardware_permission(inputs):
    out = audit_allocation(*inputs)
    assert out["accepted"] and not out["hardware_motion_allowed"]
    assert not out["dynamic_recovery_proven"]


def test_componentwise_friction_cone_cannot_replace_original_l1(inputs):
    c, feet, active, com, g, r = inputs
    normal = c["gross_mass_kg"]*c["screening"]["load_factor"]*(-g[2])/6
    forces = np.column_stack([feet[:,:2]*normal*.5/np.abs(feet[:,:2]).max(), np.full(6,normal)])
    # A purported import's square cone admits these balanced radial forces.
    assert np.all(np.abs(forces[:,:2]) <= .5*forces[:,2,None]+1e-10)
    assert np.linalg.norm(forces.sum(axis=0)+c["gross_mass_kg"]*c["screening"]["load_factor"]*g) < 1e-8
    assert np.linalg.norm(np.cross(feet-com,forces).sum(axis=0)) < 1e-8
    r["forces_n"] = forces.tolist()
    assert "friction_pyramid" in audit_allocation(c,feet,active,com,g,r)["reasons"]


def test_leg_self_weight_is_not_omitted(inputs):
    c, feet, active, com, g, r = inputs
    forces = np.array(r["forces_n"])
    contact_only = np.array([np.abs(study.rover.jacobian(c,i,study.rover.ik(c,i,feet[i])).T @ f)
                             for i,f in zip(active,forces)])
    c["actuator"]["design_torque_limit_nm"] = float(contact_only.max()+1e-5)
    r["torque_bounds_nm"] = contact_only.tolist()
    r["max_torque_nm"] = float(contact_only.max())
    out = audit_allocation(c,feet,active,com,g,r)
    assert "max_torque_nm" in out["reasons"]
    assert "misreported_torque_bounds" in out["reasons"]


@pytest.mark.parametrize("bad_forces", [[[0.,0.,0.]]*6, [[0.,0.,float("nan")]]*6, [[0.,0.,1.]]*5, "bad"])
def test_forged_success_cannot_be_admitted(inputs,bad_forces):
    *args, r = inputs
    r["forces_n"] = bad_forces
    r["force_residual_n"] = r["moment_residual_nm"] = 0.
    assert not audit_allocation(*args,r)["accepted"]


@pytest.mark.parametrize("value,reason", [(-1.,"unilateral_normal"),(301.,"max_normal_n")])
def test_raw_normal_limits_enforced(inputs,value,reason):
    *args, r = inputs
    r["forces_n"][0][2] = value
    assert reason in audit_allocation(*args,r)["reasons"]


def test_support_identity_and_reported_utilization_are_checked(inputs):
    *args, r = inputs
    r["active"] = [True,1,2,3,4,5]
    r["peak_utilization"] = 0.
    reasons = audit_allocation(*args,r)["reasons"]
    assert {"witness_support_identities","misreported_peak_utilization"} <= set(reasons)


def test_contact_plan_does_not_confirm_touchdown(inputs):
    c = inputs[0]
    obs = [ContactEvidence(True,True,False,0.)]*6
    obs[0] = replace(obs[0],load_confirmed=False)
    out = assess_support_evidence(c,tuple(range(6)),obs)
    assert not out["evidence_sufficient_for_offline_analysis"]
    assert 0 not in out["usable_supports"]
    assert "leg1:load_unconfirmed" in out["reasons"]
    assert not out["hardware_motion_allowed"] and not out["automatic_recovery_allowed"]


@pytest.mark.parametrize("change,reason", [({"age_ms":40.},"stale_contact"),({"slipping":True},"suspected_slip"),({"touching":False},"no_contact")])
def test_uncertain_support_is_removed(inputs,change,reason):
    obs = [ContactEvidence(True,True,False,0.)]*6
    obs[2] = replace(obs[2],**change)
    out = assess_support_evidence(inputs[0],(0,1,2,3,4),obs)
    assert out["usable_supports"] == [0,1,3,4]
    assert f"leg3:{reason}" in out["reasons"]


@pytest.mark.parametrize("change", [{"age_ms":float("nan")},{"age_ms":True},{"load_confirmed":1}])
def test_malformed_contact_evidence_fails_closed(inputs,change):
    obs = [ContactEvidence(True,True,False,0.)]*6
    obs[0] = replace(obs[0],**change)
    with pytest.raises(ValueError,match="Malformed"):
        assess_support_evidence(inputs[0],tuple(range(6)),obs)


def test_square_region_positive_control():
    a = np.array([[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]])
    out = regions.solve_region(a,np.ones(4))
    assert out["status"] == "NECESSARY_REGION_ONLY"
    assert out["signed_inradius_m"] == pytest.approx(1.)
    assert not out["hardware_motion_allowed"]


def test_separate_per_loss_positions_do_not_imply_common_feasibility():
    a = np.array([[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]])
    b1, b2 = np.array([-.2,1.,1.,1.]), np.array([1.,-.2,1.,1.])
    assert regions.solve_region(a,b1)["status"] == "NECESSARY_REGION_ONLY"
    assert regions.solve_region(a,b2)["status"] == "NECESSARY_REGION_ONLY"
    common = regions.solve_region(np.vstack([a,a]),np.r_[b1,b2])
    assert common["status"] == "EMPTY"
    assert common["signed_inradius_m"] == pytest.approx(-.2)
    cert = common["empty_certificate"]
    assert cert["combined_rhs_m"] < 0 and cert["normal_cancellation_residual"] < 1e-8


def test_solver_unknown_and_invalid_dual_cannot_certify_empty(monkeypatch):
    a = np.array([[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]])
    b = np.array([-.2,-.2,1.,1.])
    real = regions.linprog
    def forged(*args,**kwargs):
        r = real(*args,**kwargs)
        r.ineqlin.marginals[:] = 0.
        return r
    monkeypatch.setattr(regions,"linprog",forged)
    with pytest.raises(ValueError,match="dual"):
        regions.solve_region(a,b)
    monkeypatch.setattr(regions,"linprog",lambda *a,**k:SimpleNamespace(success=False,status=4,message="unknown"))
    with pytest.raises(RuntimeError,match="indeterminate"):
        regions.solve_region(a,b)


def test_region_rejects_nonplanar_supports(inputs):
    feet = inputs[1].copy()
    feet[0,2] += .001
    with pytest.raises(ValueError,match="coplanar"):
        regions.region_constraints(inputs[0],feet,(0,1,2,3,4))


def test_mechanism_bound_has_numerical_crosscheck_and_relaxed_positive_control(inputs):
    c = inputs[0]
    out = regions.mechanism_certificate(c)
    assert out["closed"] and out["normal_lower_bound_n"] > 300
    assert len(out["witnesses"]) == 6
    assert out["relaxed_lp_forces_n"][0] == pytest.approx(out["normal_lower_bound_n"])
    c["com_uncertainty_xy_m"] = [0.,0.]
    assert not regions.mechanism_certificate(c,0.)["closed"]


@pytest.mark.parametrize("key,value", [("hip_height_m",.29),("leg_azimuth_deg",[0]*6),("com_m",[0.,0.,.30])])
def test_geometry_changes_cannot_reuse_certificate(inputs,key,value):
    c = inputs[0]
    c[key] = value
    with pytest.raises(ValueError,match="premises changed"):
        regions.mechanism_certificate(c)


def test_saved_certificate_tampering_is_rejected():
    from check_support_region_artifacts import verify_region
    a = np.array([[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]])
    b = np.array([-.2,-.2,1.,1.])
    out = regions.solve_region(a,b)
    verify_region(a,b,out)
    bad = copy.deepcopy(out)
    bad["empty_certificate"]["terms"][0]["weight"] = 0.
    with pytest.raises(ValueError,match="certificate"):
        verify_region(a,b,bad)
    bad = copy.deepcopy(out)
    bad["center_body_translation_xy_m"] = [100.,100.]
    with pytest.raises(ValueError,match="primal"):
        verify_region(a,b,bad)


def test_existing_results_directory_is_never_overwritten(tmp_path):
    import run_support_region_02 as runner
    with pytest.raises(ValueError,match="existing output"):
        runner.run(tmp_path)


def test_committed_region_metadata_is_bound_to_frozen_inputs():
    import run_support_region_02 as runner
    path = runner.SPEC.with_name("results.json")
    if not path.exists(): pytest.skip("Full artifacts not generated yet")
    spec,_ = runner.frozen_inputs()
    r = json.loads(path.read_text())
    assert r["spec_sha256"] == study.sha256(runner.SPEC)
    assert r["frozen_inputs_sha256"] == spec["frozen_inputs_sha256"]
    assert r["common_region_counts"] == {"EMPTY":30}
    assert all(r[k] is False for k in runner.RELEASE)
