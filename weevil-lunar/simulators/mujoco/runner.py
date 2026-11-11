from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from simulators.common.artifact_paths import scenario_artifact_stem
    from simulators.common.receipts import SimulationReceipt, sha256_of_bytes, sha256_of_path, write_receipt
    from simulators.common.scenario_schema import SimulationScenario
    from simulators.mujoco.extract_metrics import trace_backed_metrics
    from simulators.mujoco.trace_harness import run_trace
else:
    from simulators.common.artifact_paths import scenario_artifact_stem
    from simulators.common.receipts import SimulationReceipt, sha256_of_bytes, sha256_of_path, write_receipt
    from simulators.common.scenario_schema import SimulationScenario
    from .extract_metrics import trace_backed_metrics
    from .trace_harness import run_trace


def run_scenario(scenario: SimulationScenario, output_root: Path | None = None) -> tuple[Path, Path]:
    """Compile and trace the same parameterized MuJoCo model, then write its receipt."""
    trace_path, trace_data = run_trace(scenario, output_root=output_root, save_compiled_model=True)
    model_path = Path(trace_data["metadata"]["model_artifact"])
    stem = scenario_artifact_stem("mujoco", scenario.scenario_id, output_root=output_root)
    compiled_path = Path(str(stem) + ".mjb")

    metrics = trace_backed_metrics(
        scenario,
        model_path=model_path,
        compiled_model_path=compiled_path,
        trace_data=trace_data,
    )
    metrics_path = Path(str(stem) + "_metrics.json")
    metrics_path.write_text(json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = SimulationReceipt(
        backend="mujoco",
        scenario_id=scenario.scenario_id,
        generated_at=datetime.now(UTC).isoformat(),
        model_artifact=str(model_path),
        model_hash=sha256_of_path(model_path),
        parameter_hash=sha256_of_bytes(json.dumps(scenario.to_dict(), sort_keys=True).encode("utf-8")),
        code_commit="unknown",
        engine_version=trace_data["metadata"]["engine_version"],
        metrics_path=str(metrics_path),
        status="partial",
        load_path=scenario.load_path,
        load_path_detail="scenario declares the load path; the trace applies gravity to the fixture masses",
        warnings=[
            "custom Python MuJoCo trace path active",
            "fixture body masses and foot geometry come from the MJCF template",
            "reaction/contact-force values are still proxy-level rather than full wrench decomposition",
            "some geometry/penetration fields remain proxies",
        ],
        assumption_notes=[
            "Python MuJoCo saved the compiled model used by the trace",
            f"custom per-step trace written to {trace_path}",
            "trace harness uses Python mujoco bindings for per-step contact/state capture",
        ],
    )
    receipt_path = write_receipt(receipt, output_root=output_root)
    return metrics_path, receipt_path


if __name__ == "__main__":
    demo = SimulationScenario(
        scenario_id="demo_single_leg_incline_hold",
        backend="mujoco",
        body_mass_kg=30.0,
        gravity_m_s2=1.62,
        leg_count=6,
        stance_legs=1,
        foot_radius_m=0.05,
        foot_geometry_kind="sphere",
        terrain_class="mare",
        slope_deg=25.0,
        preload_normal_n=20.0,
        notes=["demo Python trace-backed run"],
    )
    m, r = run_scenario(demo)
    print(f"Wrote {m}")
    print(f"Wrote {r}")
