"""Independent numerical and physical contracts for the COTS design model."""

import copy
import importlib.util
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from models.cots_rover import (
    DEFAULT_CONFIG,
    allocate,
    evaluate,
    gait_samples,
    hip,
    ik,
    jacobian,
    load_config,
    mass_budget,
    nominal_feet,
    points,
    power_checks,
    structural_checks,
    support_margin,
)


@pytest.fixture
def cfg():
    return load_config()


def test_inverse_kinematics_and_jacobian(cfg):
    rng = np.random.default_rng(40517)
    for leg in range(6):
        for _ in range(20):
            target = nominal_feet(cfg)[leg] + rng.uniform([-0.025, -0.015, 0], [0.025, 0.015, 0.035])
            q = ik(cfg, leg, target)
            np.testing.assert_allclose(points(cfg, leg, q)[3], target, atol=1e-12)
            eps = 1e-6
            numerical = np.column_stack(
                [
                    (points(cfg, leg, q + np.eye(3)[j] * eps)[3] - points(cfg, leg, q - np.eye(3)[j] * eps)[3])
                    / (2 * eps)
                    for j in range(3)
                ]
            )
            np.testing.assert_allclose(jacobian(cfg, leg, q), numerical, atol=1e-9)
            force = np.array([11.0, -7.0, 85.0])
            dq = np.array([0.03, -0.02, 0.05])
            assert np.dot(jacobian(cfg, leg, q).T @ force, dq) == pytest.approx(np.dot(force, numerical @ dq))


def test_contact_equilibrium_and_no_free_preload(cfg):
    feet = nominal_feet(cfg)
    g = np.array([0.6, -0.2, -cfg["earth_gravity_m_s2"]])
    com = np.array(cfg["com_m"])
    out = allocate(cfg, feet, tuple(range(6)), com, g)
    assert out["feasible"]
    forces = np.array(out["forces_n"])
    np.testing.assert_allclose(forces.sum(axis=0), -cfg["gross_mass_kg"] * g, atol=1e-7)
    np.testing.assert_allclose(np.cross(feet - com, forces).sum(axis=0), np.zeros(3), atol=1e-7)
    assert np.all(forces[:, 2] >= 0)
    assert np.all(np.abs(forces[:, :2]).sum(axis=1) <= 0.5 * forces[:, 2] + 1e-8)
    assert out["max_torque_nm"] <= cfg["actuator"]["design_torque_limit_nm"] + 1e-8


def test_no_tensile_contact_or_unlimited_friction(cfg):
    feet = nominal_feet(cfg)
    g = np.array([0.0, 0.0, -cfg["earth_gravity_m_s2"]])
    outside = allocate(cfg, feet, tuple(range(6)), np.array([2.0, 0.0, 0.3]), g)
    assert not outside["feasible"]
    steep = allocate(cfg, feet, tuple(range(6)), np.array(cfg["com_m"]), np.array([8.0, 0.0, -9.0]))
    assert not steep["feasible"]
    assert support_margin(np.zeros((3, 3)), np.array([0.0, 0.0, 0.3]), g) == -math.inf


def test_gravity_force_scaling_is_not_soil_validation(cfg):
    feet = nominal_feet(cfg)
    outputs = [
        allocate(cfg, feet, tuple(range(6)), np.array(cfg["com_m"]), np.array([0.0, 0.0, -g]))
        for g in (cfg["earth_gravity_m_s2"], cfg["moon_gravity_m_s2"])
    ]
    assert all(o["feasible"] for o in outputs)
    ratio = cfg["moon_gravity_m_s2"] / cfg["earth_gravity_m_s2"]
    assert np.array(outputs[1]["forces_n"])[:, 2].sum() == pytest.approx(
        ratio * np.array(outputs[0]["forces_n"])[:, 2].sum()
    )


def test_gait_is_periodic_and_stance_feet_remain_on_ground(cfg):
    samples = list(gait_samples(cfg, 20))
    np.testing.assert_allclose(samples[0][1], samples[-1][1], atol=1e-12)
    for phase in range(5):
        np.testing.assert_allclose(samples[phase * 21 + 20][1], samples[(phase + 1) * 21][1], atol=1e-12)
    for _, feet, active in samples:
        assert len(active) == 5
        np.testing.assert_allclose(feet[list(active), 2], cfg["foot_pivot_height_m"], atol=1e-12)
    # Body advance + relative stance translation = zero world-frame foot displacement.
    phase = samples[:21]
    for i in phase[0][2]:
        assert phase[-1][1][i, 0] - phase[0][1][i, 0] == pytest.approx(-cfg["screening"]["step_length_m"] / 5)


def test_bad_inputs_fail_explicitly(cfg, tmp_path):
    with pytest.raises(ValueError, match="outside link reach"):
        ik(cfg, 0, np.array([4.0, 0.0, 0.0]))
    with pytest.raises(ValueError, match="Nonfinite"):
        ik(cfg, 0, np.array([np.nan, 0.0, 0.0]))
    feet = nominal_feet(cfg)
    for active, gravity in [
        ((0, 0, 1), [0, 0, -9.8]),
        ((0, 1, 6), [0, 0, -9.8]),
        ((0, 1, 2), [0, 0, 0]),
        ((0, 1, 2), [np.nan, 0, -9.8]),
    ]:
        with pytest.raises(ValueError, match="support inputs"):
            allocate(cfg, feet, active, np.array(cfg["com_m"]), np.array(gravity))
    cfg["power"]["operating_cutoff_v"] = float("nan")
    f = tmp_path / "invalid.json"
    f.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="Nonfinite"):
        load_config(f)


def test_structure_accounts_for_leg_moment_and_material(cfg):
    base = structural_checks(cfg)
    longer = copy.deepcopy(cfg)
    longer["structure"]["shaft_load_eccentricity_m"] *= 1.5
    altered = structural_checks(longer)
    assert altered["shaft_von_mises_pa"] > base["shaft_von_mises_pa"]
    assert altered["bearing_reaction_n"] > base["bearing_reaction_n"]
    assert base["shaft_bending_moment_nm"] > 100  # A hub-only bending model must not pass.
    weak = copy.deepcopy(cfg)
    weak["structure"]["shaft_yield_requirement_pa"] = 250e6
    assert structural_checks(weak)["shaft_yield_factor"] < 1


def test_power_protection_does_not_depend_on_software_limit(cfg):
    baseline = power_checks(cfg)
    cfg["power"]["motor_mechanical_power_limit_w"] = 1
    assert power_checks(cfg)["regen_bound_w"] == baseline["regen_bound_w"]
    assert baseline["resistor_absorption_min_w"] > baseline["independent_joint_mechanical_bound_w"]
    assert baseline["resistor_instantaneous_max_w"] > cfg["power"]["brake_resistor_nominal_w"]
    assert baseline["can_utilization"] == pytest.approx(0.29)


def test_baseline_screen_and_mass_budget(cfg):
    r = evaluate(cfg)
    assert r["analytical_checks_pass"], r["checks"]
    assert r["load_cases"] == 1944
    assert r["failure_count"] == 0
    assert not r["hardware_validated"] and not r["flight_qualified"]
    assert r["mass_budget"]["reserve_fraction"] >= 0.05
    assert r["gait"]["peak_joint_speed_rad_s"] <= cfg["joint_velocity_limit_rad_s"]
    saved = json.loads((DEFAULT_CONFIG.parent / "analysis.json").read_text())
    assert saved["worst"]["torque_nm"] == pytest.approx(r["worst"]["torque_nm"], rel=1e-6)
    overweight = copy.deepcopy(cfg)
    overweight["gross_mass_kg"] = 40
    assert mass_budget(overweight)["reserve_kg"] < 0


def _rotation(axis, angle):
    axis = np.array(axis, float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + math.sin(angle) * cross + (1 - math.cos(angle)) * (cross @ cross)


def test_urdf_chains_match_world_geometry(cfg, tmp_path):
    source = DEFAULT_CONFIG.parents[2] / "cad/scripts/build_cots_rover.py"
    spec = importlib.util.spec_from_file_location("cots_cad", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    f = tmp_path / "rover.urdf"
    module.urdf(cfg, f)
    root = ET.parse(f).getroot()
    joints = root.findall("joint")
    assert len(root.findall("link")) == 25 and len(joints) == 24
    assert sum(j.attrib["type"] == "revolute" for j in joints) == 18
    feet = nominal_feet(cfg)
    for leg in range(6):
        q = ik(cfg, leg, feet[leg])
        transform = np.eye(4)
        transform[:3, 3] = [0, 0, cfg["hip_height_m"]]
        for rank, suffix in enumerate(("yaw", "pitch", "knee", "ankle_frame")):
            j = root.find(f"joint[@name='L{leg + 1}_{suffix}']")
            o = j.find("origin")
            xyz = np.fromstring(o.attrib["xyz"], sep=" ")
            roll, pitch, yaw = np.fromstring(o.attrib["rpy"], sep=" ")
            m = np.eye(4)
            m[:3, 3] = xyz
            m[:3, :3] = _rotation([0, 0, 1], yaw) @ _rotation([0, 1, 0], pitch) @ _rotation([1, 0, 0], roll)
            if rank < 3:
                m[:3, :3] = m[:3, :3] @ _rotation(np.fromstring(j.find("axis").attrib["xyz"], sep=" "), q[rank])
            transform = transform @ m
        np.testing.assert_allclose(transform[:3, 3], feet[leg], atol=1e-12)
