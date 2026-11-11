from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mujoco
import numpy as np

from simulators.common.artifact_paths import scenario_artifact_stem
from simulators.common.scenario_schema import SimulationScenario

from .adapters import materialize_scenario_model


def _quat_to_euler_deg(quat: np.ndarray) -> tuple[float, float, float]:
    w, x, y, z = quat.tolist()
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = np.degrees(np.arctan2(sinr_cosp, cosr_cosp))

    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        pitch = np.degrees(np.sign(sinp) * (np.pi / 2.0))
    else:
        pitch = np.degrees(np.arcsin(sinp))

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.degrees(np.arctan2(siny_cosp, cosy_cosp))
    return roll, pitch, yaw


def _contact_force_proxy(model: mujoco.MjModel, data: mujoco.MjData) -> tuple[float, float, float, float]:
    if data.ncon <= 0:
        return 0.0, 0.0, 0.0, 0.0

    total_normal = 0.0
    total_tangential = 0.0
    max_normal = 0.0
    max_tangential = 0.0
    force = np.zeros(6, dtype=float)
    for i in range(data.ncon):
        mujoco.mj_contactForce(model, data, i, force)
        normal = abs(float(force[0]))
        tangential = float(np.linalg.norm(force[1:3]))
        total_normal += normal
        total_tangential += tangential
        max_normal = max(max_normal, normal)
        max_tangential = max(max_tangential, tangential)
    return total_normal, total_tangential, max_normal, max_tangential


def run_trace(scenario: SimulationScenario, output_root: Path | None = None, *, save_compiled_model: bool = False) -> tuple[Path, dict[str, Any]]:
    scenario.validate()
    model_path = materialize_scenario_model(scenario, output_root)
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    stem = scenario_artifact_stem("mujoco", scenario.scenario_id, output_root=output_root)
    if save_compiled_model:
        mujoco.mj_saveModel(model, str(stem) + ".mjb", None)
    # World-body plane orientation is fixed. Read its normal back from the engine.
    mujoco.mj_forward(model, data)
    plane_id, = np.flatnonzero(model.geom_type == mujoco.mjtGeom.mjGEOM_PLANE)
    normal = data.geom_xmat[plane_id].reshape(3, 3)[:, 2]
    applied_slope = float(np.degrees(np.arctan2(normal[0], normal[2])))

    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "foot")
    if body_id < 0:
        raise ValueError("foot body not found in MuJoCo model")

    nstep = max(1, int(round(scenario.duration_s / scenario.timestep_s)))
    steps: list[dict[str, Any]] = []
    initial_x = float(data.xpos[body_id, 0])
    foot_x_velocities: list[float] = []
    contact_force_normal_proxies: list[float] = []
    contact_force_tangential_proxies: list[float] = []
    contact_presence: list[bool] = []
    body_pitch_deg: list[float] = []
    body_roll_deg: list[float] = []

    prev_foot_x = initial_x
    observer = mujoco.MjData(model)
    state_kind = mujoco.mjtState.mjSTATE_INTEGRATION
    state = np.empty(mujoco.mj_stateSize(model, state_kind))

    for step_idx in range(nstep):
        mujoco.mj_step(model, data)

        # mj_step advances time and joint state; derived geometry can still be
        # from the force evaluation. Recompute on a separate data object so
        # recording cannot change the integrator's warm start.
        mujoco.mj_getState(model, data, state, state_kind)
        mujoco.mj_setState(model, observer, state, state_kind)
        mujoco.mj_forward(model, observer)
        foot_pos = np.array(observer.xpos[body_id], dtype=float)
        foot_x = float(foot_pos[0])

        slip_velocity = abs((foot_x - prev_foot_x) / model.opt.timestep)
        foot_x_velocities.append(slip_velocity)
        prev_foot_x = foot_x

        total_normal_proxy, total_tangential_proxy, max_normal_proxy, max_tangential_proxy = _contact_force_proxy(model, observer)
        contact_force_normal_proxies.append(total_normal_proxy)
        contact_force_tangential_proxies.append(total_tangential_proxy)
        has_contact = observer.ncon > 0
        contact_presence.append(has_contact)

        torso_quat = np.array(observer.xquat[1], dtype=float) if model.nbody > 1 else np.array([1.0, 0.0, 0.0, 0.0])
        roll_deg, pitch_deg, _ = _quat_to_euler_deg(torso_quat)
        body_pitch_deg.append(float(pitch_deg))
        body_roll_deg.append(float(roll_deg))

        steps.append(
            {
                "step": step_idx,
                "time_s": float(data.time),
                "foot_pos": foot_pos.tolist(),
                "foot_x_m": foot_x,
                "slip_velocity_m_s": slip_velocity,
                "contact_count": int(observer.ncon),
                "contact_present": has_contact,
                "contact_force_normal_proxy_n": total_normal_proxy,
                "contact_force_tangential_proxy_n": total_tangential_proxy,
                "contact_force_normal_proxy_peak_n": max_normal_proxy,
                "contact_force_tangential_proxy_peak_n": max_tangential_proxy,
                "body_pitch_deg": float(pitch_deg),
                "body_roll_deg": float(roll_deg),
            }
        )

    final_x = prev_foot_x
    slip_distance = abs(final_x - initial_x)
    contact_steps = sum(1 for c in contact_presence if c)
    contact_persistence_ratio = contact_steps / nstep if nstep else 0.0

    trace = {
        "metadata": {
            "backend": "mujoco",
            "engine_version": mujoco.__version__,
            "scenario_id": scenario.scenario_id,
            "model_artifact": str(model_path),
            "requested_slope_deg": scenario.slope_deg,
            "applied_slope_deg": applied_slope,
            "applied_gravity_m_s2": model.opt.gravity.tolist(),
            "timestep_s": float(model.opt.timestep),
            "duration_s": scenario.duration_s,
            "elapsed_s": float(data.time),
            "sampling_phase": "post_step",
            "solver_iterations": int(model.opt.iterations),
        },
        "summary": {
            "completed": True,
            "total_steps": nstep,
            "contact_steps": contact_steps,
            "contact_persistence_ratio": contact_persistence_ratio,
            "initial_foot_x_m": initial_x,
            "final_foot_x_m": final_x,
            "slip_distance_m": slip_distance,
            "max_slip_velocity_m_s": max(foot_x_velocities) if foot_x_velocities else 0.0,
            "mean_contact_normal_proxy_n": float(np.mean(contact_force_normal_proxies)) if contact_force_normal_proxies else 0.0,
            "max_contact_normal_proxy_n": float(np.max(contact_force_normal_proxies)) if contact_force_normal_proxies else 0.0,
            "mean_contact_tangential_proxy_n": float(np.mean(contact_force_tangential_proxies)) if contact_force_tangential_proxies else 0.0,
            "max_contact_tangential_proxy_n": float(np.max(contact_force_tangential_proxies)) if contact_force_tangential_proxies else 0.0,
            "max_body_pitch_deg": float(np.max(np.abs(body_pitch_deg))) if body_pitch_deg else 0.0,
            "max_body_roll_deg": float(np.max(np.abs(body_roll_deg))) if body_roll_deg else 0.0,
        },
        "steps": steps,
    }

    trace_path = Path(str(stem) + "_trace.json")
    trace_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    return trace_path, trace
