from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

from simulators.common.artifact_paths import scenario_artifact_stem
from simulators.common.receipts import SimulationReceipt, sha256_of_bytes, sha256_of_path, write_receipt
from simulators.common.scenario_schema import SimulationScenario

from .adapters import scenario_to_config_path
from .extract_metrics import placeholder_metrics


ENGINE_VERSION = "ode-source-present-headless-build-blocked"


def run_scenario(scenario: SimulationScenario, output_root: Path | None = None) -> tuple[Path, Path]:
    scenario.validate()
    config_path = scenario_to_config_path(scenario)
    metrics = placeholder_metrics()

    stem = scenario_artifact_stem("ode", scenario.scenario_id, output_root=output_root)
    metrics_path = Path(str(stem) + "_metrics.json")
    metrics_path.write_text(json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = SimulationReceipt(
        backend="ode",
        scenario_id=scenario.scenario_id,
        generated_at=datetime.now(UTC).isoformat(),
        model_artifact=str(config_path),
        model_hash=sha256_of_path(config_path),
        parameter_hash=sha256_of_bytes(json.dumps(scenario.to_dict(), sort_keys=True).encode("utf-8")),
        code_commit="unknown",
        engine_version=ENGINE_VERSION,
        metrics_path=str(metrics_path),
        status="partial",
        load_path=scenario.load_path,
        load_path_detail="scenario contract declares gravity-coupled boundary load derivation, but this ODE path remains placeholder / blocked-runtime",
        warnings=[
            "placeholder backend path",
            "ODE runtime execution remains blocked locally",
            "source tree is present and MSVC is installable, but no headless-ready ODE runtime binary path was completed in this tranche",
            "generated legacy Visual Studio 2008 project files are not directly consumable by current headless MSBuild flow",
        ],
        assumption_notes=[
            "artifact-only scaffold",
            "no physics execution performed in this tranche",
            "local check found ODE source/tests and premake tooling",
            "MSVC compiler became available after vcvars64 initialization",
            "premake4 successfully generated legacy vs2008 solution/project files",
            "current headless build attempt failed because modern MSBuild would not directly build generated .vcproj files and the legacy .sln did not load cleanly in this flow",
        ],
    )
    receipt_path = write_receipt(receipt, output_root=output_root)
    return metrics_path, receipt_path
