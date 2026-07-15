from __future__ import annotations

from pathlib import Path

WEEVIL_ROOT = Path(__file__).resolve().parents[2]
SIM_RESULTS_ROOT = WEEVIL_ROOT / "results" / "simulation"


def backend_results_dir(backend: str) -> Path:
    path = SIM_RESULTS_ROOT / backend
    path.mkdir(parents=True, exist_ok=True)
    return path


def scenario_artifact_stem(backend: str, scenario_id: str) -> Path:
    safe = scenario_id.replace("/", "_").replace(" ", "_")
    return backend_results_dir(backend) / safe
