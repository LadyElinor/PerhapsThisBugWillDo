from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from simulators.common.artifact_paths import scenario_artifact_stem
from simulators.common.scenario_schema import SimulationScenario
from simulators.mujoco.runner import run_scenario as run_mujoco
from simulators.ode.runner import run_scenario as run_ode


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_value(metrics: dict[str, Any], key: str) -> Any:
    node = metrics.get(key, {})
    if not node.get("available", False):
        return None
    return node.get("value")


def _build_summary(mj_metrics: dict[str, Any], od_metrics: dict[str, Any], mj_receipt: dict[str, Any], od_receipt: dict[str, Any]) -> dict[str, Any]:
    mj_completed = bool(_metric_value(mj_metrics, "completed")) and mj_receipt.get("status") != "error"
    od_completed = bool(_metric_value(od_metrics, "completed")) and od_receipt.get("status") not in {"error", "missing"}

    mj_runtime_live = mj_receipt.get("status") != "missing" and "custom Python MuJoCo trace path active" in mj_receipt.get("warnings", [])
    od_runtime_live = od_receipt.get("status") != "missing" and "placeholder backend path" not in od_receipt.get("warnings", [])

    mj_slip = _metric_value(mj_metrics, "slip_distance_m")
    od_slip = _metric_value(od_metrics, "slip_distance_m")
    missing_comparables = [
        key
        for key in [
            "normal_reaction_n",
            "tangential_reaction_n",
            "slip_distance_m",
            "slip_velocity_m_s",
            "stance_stable_duration_s",
        ]
        if _metric_value(mj_metrics, key) is None or _metric_value(od_metrics, key) is None
    ]

    disagreement_flags: list[str] = []
    if mj_completed and not od_completed:
        disagreement_flags.append("backend completion mismatch")
    if mj_runtime_live and not od_runtime_live:
        disagreement_flags.append("backend runtime-live mismatch")
    if mj_slip is not None and od_slip is not None and abs(float(mj_slip) - float(od_slip)) > 1e-6:
        disagreement_flags.append("slip distance disagreement")
    if od_receipt.get("status") == "partial":
        disagreement_flags.append("ODE remains partial / blocked-runtime")

    evidence_label = "comparative"
    if not missing_comparables and not disagreement_flags:
        evidence_label = "backend-consistent"

    return {
        "evidence_label": evidence_label,
        "backend_status": {
            "mujoco": mj_receipt.get("status"),
            "ode": od_receipt.get("status"),
        },
        "completed": {
            "mujoco": mj_completed,
            "ode": od_completed,
        },
        "runtime_live": {
            "mujoco": mj_runtime_live,
            "ode": od_runtime_live,
        },
        "missing_comparable_metrics": missing_comparables,
        "disagreement_flags": disagreement_flags,
        "notes": [
            "Comparative report is non-validating and governed by simulation_governance.md",
            "Missing or blocked-runtime backend metrics are surfaced explicitly rather than normalized away",
        ],
    }


def generate_comparative_report(scenario: SimulationScenario, output_root: Path | None = None) -> Path:
    scenario.validate()
    mj_metrics_path, mj_receipt_path = run_mujoco(scenario, output_root=output_root)
    od_metrics_path, od_receipt_path = run_ode(scenario, output_root=output_root)

    mj_metrics = _load_json(mj_metrics_path)
    od_metrics = _load_json(od_metrics_path)
    mj_receipt = _load_json(mj_receipt_path)
    od_receipt = _load_json(od_receipt_path)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scenario": scenario.to_dict(),
        "summary": _build_summary(mj_metrics, od_metrics, mj_receipt, od_receipt),
        "backends": {
            "mujoco": {
                "metrics_path": str(mj_metrics_path),
                "receipt_path": str(mj_receipt_path),
                "metrics": mj_metrics,
                "receipt": mj_receipt,
            },
            "ode": {
                "metrics_path": str(od_metrics_path),
                "receipt_path": str(od_receipt_path),
                "metrics": od_metrics,
                "receipt": od_receipt,
            },
        },
    }

    stem = scenario_artifact_stem("parity", scenario.scenario_id, output_root=output_root)
    report_path = Path(str(stem) + "_comparative_report.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


if __name__ == "__main__":
    demo = SimulationScenario(
        scenario_id="demo_single_leg_incline_hold",
        backend="comparative",
        body_mass_kg=30.0,
        gravity_m_s2=1.62,
        leg_count=6,
        stance_legs=1,
        foot_radius_m=0.05,
        foot_geometry_kind="sphere",
        terrain_class="mare",
        slope_deg=25.0,
        preload_normal_n=20.0,
        notes=["demo comparative report run"],
    )
    out = generate_comparative_report(demo)
    print(f"Wrote {out}")
