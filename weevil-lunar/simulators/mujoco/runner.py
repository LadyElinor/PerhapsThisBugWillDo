from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from simulators.common.artifact_paths import scenario_artifact_stem
    from simulators.common.receipts import SimulationReceipt, sha256_of_bytes, sha256_of_path, write_receipt
    from simulators.common.scenario_schema import SimulationScenario
    from simulators.mujoco.adapters import scenario_to_model_path
    from simulators.mujoco.extract_metrics import trace_backed_metrics
    from simulators.mujoco.trace_harness import run_trace
else:
    from simulators.common.artifact_paths import scenario_artifact_stem
    from simulators.common.receipts import SimulationReceipt, sha256_of_bytes, sha256_of_path, write_receipt
    from simulators.common.scenario_schema import SimulationScenario
    from .adapters import scenario_to_model_path
    from .extract_metrics import trace_backed_metrics
    from .trace_harness import run_trace


MUJOCO_BUNDLE_ROOT = Path(r"C:\Users\arren\.openclaw\workspace\0sourceforge\mujoco-3.10.0-windows-x86_64")
COMPILE_EXE = MUJOCO_BUNDLE_ROOT / "bin" / "compile.exe"
DLL_DIR = MUJOCO_BUNDLE_ROOT / "bin"
ENGINE_VERSION = "mujoco-python-trace-backed"


def _mujoco_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(DLL_DIR) + os.pathsep + env.get("PATH", "")
    return env


def _compile_model(model_path: Path, compiled_path: Path) -> None:
    compiled_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(COMPILE_EXE), str(model_path), str(compiled_path)],
        check=True,
        env=_mujoco_env(),
        capture_output=True,
        text=True,
    )


def run_scenario(scenario: SimulationScenario, output_root: Path | None = None) -> tuple[Path, Path]:
    """Python trace-backed MuJoCo runner for the narrow incline-hold tranche.

    Real actions performed here:
    1. compile MJCF -> MJB using MuJoCo compile.exe
    2. run a custom Python MuJoCo per-step trace harness
    3. extract slip/contact metrics from the resulting trace artifact
    """
    scenario.validate()
    if not COMPILE_EXE.exists():
        raise FileNotFoundError(f"MuJoCo compile executable not found: {COMPILE_EXE}")

    model_path = scenario_to_model_path(scenario)
    stem = scenario_artifact_stem("mujoco", scenario.scenario_id, output_root=output_root)
    compiled_path = Path(str(stem) + ".mjb")

    _compile_model(model_path, compiled_path)
    trace_path, trace_data = run_trace(scenario, output_root=output_root)

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
        engine_version=ENGINE_VERSION,
        metrics_path=str(metrics_path),
        status="partial",
        warnings=[
            "custom Python MuJoCo trace path active",
            "reaction/contact-force values are still proxy-level rather than full wrench decomposition",
            "some geometry/penetration fields remain proxies",
        ],
        assumption_notes=[
            "MuJoCo compile.exe used to produce real .mjb artifact",
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
