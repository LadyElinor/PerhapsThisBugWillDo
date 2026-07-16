from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .artifact_paths import scenario_artifact_stem


@dataclass(frozen=True)
class SimulationReceipt:
    backend: str
    scenario_id: str
    generated_at: str
    model_artifact: str
    model_hash: str
    parameter_hash: str
    code_commit: str
    engine_version: str
    metrics_path: str
    status: str
    warnings: list[str] = field(default_factory=list)
    assumption_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_receipt(receipt: SimulationReceipt, output_root: Path | None = None) -> Path:
    stem = scenario_artifact_stem(receipt.backend, receipt.scenario_id, output_root=output_root)
    out_path = Path(str(stem) + "_receipt.json")
    out_path.write_text(json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_path
