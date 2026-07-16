from __future__ import annotations

from pathlib import Path

WEEVIL_ROOT = Path(__file__).resolve().parents[2]
SIM_RESULTS_ROOT = WEEVIL_ROOT / "results" / "simulation"


def backend_results_dir(backend: str, output_root: Path | None = None) -> Path:
    root = output_root if output_root is not None else SIM_RESULTS_ROOT
    path = Path(root) / backend
    path.mkdir(parents=True, exist_ok=True)
    return path


def scenario_artifact_stem(backend: str, scenario_id: str, output_root: Path | None = None) -> Path:
    safe = scenario_id.replace("/", "_").replace(" ", "_")
    return backend_results_dir(backend, output_root=output_root) / safe
