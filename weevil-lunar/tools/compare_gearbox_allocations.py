#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import yaml

ROVER_MASS_KG = 15.0
GRAVITY_MOON = 1.62
GAIT_CYCLE_TIME_S = 2.0
MOTOR_EFFICIENCY = 0.85
DENSITY_KG_PER_MM3 = 7.85e-6
LEVER_ARM_M = 0.10

APEX_AE_TORQUE_CONTINUOUS_NM = {
    "ae050": 55.0,
    "ae060": 97.5,
    "ae070": 140.0,
    "ae090": 320.0,
}

JOINT_DEMAND_WEIGHT = {"hip": 1.00, "knee": 0.65, "ankle": 0.35}


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def inertia_trace(i: List[List[float]]) -> float:
    return float(i[0][0] + i[1][1] + i[2][2])


def infer_torque_nominal_nm(gearbox_key: str) -> float:
    k = gearbox_key.lower()
    if "ae050" in k:
        return APEX_AE_TORQUE_CONTINUOUS_NM["ae050"]
    if "ae060" in k:
        return APEX_AE_TORQUE_CONTINUOUS_NM["ae060"]
    if "ae070" in k:
        return APEX_AE_TORQUE_CONTINUOUS_NM["ae070"]
    if "ae090" in k:
        return APEX_AE_TORQUE_CONTINUOUS_NM["ae090"]
    return 100.0


def status_from_margin(margin_nm: float) -> str:
    if margin_nm >= 0:
        return "PASS"
    if margin_nm >= -0.5:
        return "MARGINAL"
    return "FAIL"


def _collect_joint_terms(cfg_name: str, cfg: Dict[str, str], gearboxes: Dict[str, Any], base_dir: Path):
    total_reflected_inertia = 0.0
    total_mass = 0.0
    for joint in ("hip", "knee", "ankle"):
        key = cfg.get(joint)
        if not key:
            continue
        gb = gearboxes.get(key)
        if not gb:
            raise ValueError(f"Missing gearbox key '{key}' for {cfg_name}.{joint}")
        params = load_json(base_dir / gb["params_json"])
        volume = float(params.get("volume", params.get("mass_proxy_density_1", 0.0)))
        total_mass += volume * DENSITY_KG_PER_MM3
        Itr = inertia_trace(params["inertia_tensor"])
        reflected = (Itr * 1e-9) / (50.0 * 50.0)
        total_reflected_inertia += reflected
    return total_reflected_inertia, total_mass


def _joint_torque_margins(
    cfg: Dict[str, str],
    demand_total_nm: float,
    derate: float,
    ankle_demand_mult: float,
) -> Tuple[float, float, float, float]:
    margins: Dict[str, float] = {}
    for joint in ("hip", "knee", "ankle"):
        key = cfg.get(joint, "")
        avail_nm = infer_torque_nominal_nm(key) * derate
        req_nm = demand_total_nm * JOINT_DEMAND_WEIGHT[joint]
        if joint == "ankle":
            req_nm *= ankle_demand_mult
        margins[joint] = avail_nm - req_nm
    overall = min(margins.values())
    return margins["hip"], margins["knee"], margins["ankle"], overall


def estimate_proxy(cfg_name: str, cfg: Dict[str, str], gearboxes: Dict[str, Any], base_dir: Path, slope_deg: float, derate: float, ankle_demand_mult: float) -> Dict[str, Any]:
    total_reflected_inertia, total_mass = _collect_joint_terms(cfg_name, cfg, gearboxes, base_dir)
    slope_term = total_mass * GRAVITY_MOON * math.sin(math.radians(slope_deg)) * LEVER_ARM_M
    dynamic_term = total_mass * (2.0 * math.pi / GAIT_CYCLE_TIME_S) ** 2 * LEVER_ARM_M
    torque_req_nm = max(slope_term, dynamic_term)
    energy = torque_req_nm / MOTOR_EFFICIENCY
    t_hip, t_knee, t_ankle, t_overall = _joint_torque_margins(cfg, torque_req_nm, derate, ankle_demand_mult)
    reach = max(0.0, 100.0 - total_reflected_inertia * 4.0e4)
    return {
        "configuration": cfg_name,
        "mode": "proxy",
        "slope_deg": slope_deg,
        "reachability_margin_pct": round(reach, 2),
        "reflected_inertia_penalty": round(total_reflected_inertia, 8),
        "energy_per_gait_cycle_j": round(energy, 4),
        "torque_margin_overall_nm": round(t_overall, 4),
        "torque_margin_hip": round(t_hip, 4),
        "torque_margin_knee": round(t_knee, 4),
        "torque_margin_ankle": round(t_ankle, 4),
        "status": status_from_margin(t_overall),
        "derate": derate,
        "ankle_demand_mult": ankle_demand_mult,
    }


def estimate_real_sim(cfg_name: str, cfg: Dict[str, str], gearboxes: Dict[str, Any], base_dir: Path, slope_deg: float, derate: float, ankle_demand_mult: float) -> Dict[str, Any]:
    root = base_dir / "weevil-lunar"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from models.lunar_integrated_weevil_leg import ContactModel, LegState, evaluate_leg_state, load_params, sample_states  # type: ignore

    total_reflected_inertia, _ = _collect_joint_terms(cfg_name, cfg, gearboxes, base_dir)
    params = load_params()
    contact = ContactModel(regolith_mu=0.55, internal_mu=0.004)
    evals = [evaluate_leg_state(s, params, contact) for s in sample_states(params)]
    reach = 100.0 * (sum(1 for e in evals if e.reachable) / max(1, len(evals)))

    slope_eval = evaluate_leg_state(LegState(0.0, 5.0, 30.0), params, contact)
    traction = slope_eval.traction_n
    demand_force = slope_eval.normal_n * math.sin(math.radians(slope_deg))
    torque_req_nm = max(0.0, demand_force - traction) * LEVER_ARM_M
    t_hip, t_knee, t_ankle, t_overall = _joint_torque_margins(cfg, torque_req_nm, derate, ankle_demand_mult)

    base_cycle_work = abs(traction) * 0.05
    inertia_cost = total_reflected_inertia * (2.0 * math.pi / GAIT_CYCLE_TIME_S) ** 2 * 1e3
    energy = (base_cycle_work + inertia_cost) / MOTOR_EFFICIENCY

    return {
        "configuration": cfg_name,
        "mode": "real_sim",
        "slope_deg": slope_deg,
        "reachability_margin_pct": round(reach, 2),
        "reflected_inertia_penalty": round(total_reflected_inertia, 8),
        "energy_per_gait_cycle_j": round(energy, 4),
        "torque_margin_overall_nm": round(t_overall, 4),
        "torque_margin_hip": round(t_hip, 4),
        "torque_margin_knee": round(t_knee, 4),
        "torque_margin_ankle": round(t_ankle, 4),
        "status": status_from_margin(t_overall),
        "derate": derate,
        "ankle_demand_mult": ankle_demand_mult,
    }


def print_markdown(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    headers = list(rows[0].keys())
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        print("| " + " | ".join(str(r[h]) for h in headers) + " |")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="weevil-lunar/configs/gearbox_allocations.yaml", type=Path)
    ap.add_argument("--output", default="weevil-lunar/results/comparisons/gearbox_comparison.csv", type=Path)
    ap.add_argument("--mode", choices=["proxy", "real_sim", "both"], default="real_sim")
    ap.add_argument("--derate", type=float, default=0.75)
    ap.add_argument("--ankle-demand-mult", type=float, default=1.0)
    ap.add_argument("--slopes", type=str, default="25")
    args = ap.parse_args()

    slopes = [float(x.strip()) for x in args.slopes.split(",") if x.strip()]
    data = load_yaml(args.config)
    gearboxes = data.get("gearboxes", {})
    configs = data.get("configurations", {})
    base_dir = Path.cwd()

    rows: List[Dict[str, Any]] = []
    for slope in slopes:
        for cfg_name, cfg in configs.items():
            if args.mode in ("proxy", "both"):
                rows.append(estimate_proxy(cfg_name, cfg, gearboxes, base_dir, slope, args.derate, args.ankle_demand_mult))
            if args.mode in ("real_sim", "both"):
                rows.append(estimate_real_sim(cfg_name, cfg, gearboxes, base_dir, slope, args.derate, args.ankle_demand_mult))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"[DONE] {args.output}")
    print_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
