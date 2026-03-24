from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_icd_contract_catalog_validator_passes() -> None:
    proc = _run("verification/scripts/validate_icd_contract_catalog.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_icd_contract_catalog_validator_rejects_duplicate_message(tmp_path: Path) -> None:
    src = ROOT / "icd" / "contract_catalog_v0.2.yaml"
    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    data["contracts"].append(data["contracts"][0])

    bad_catalog = tmp_path / "bad_catalog.yaml"
    bad_catalog.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    proc = _run(
        "verification/scripts/validate_icd_contract_catalog.py",
        "--catalog",
        str(bad_catalog),
    )
    assert proc.returncode != 0
    assert "Duplicate contract message" in (proc.stdout + proc.stderr)


def test_build_gate_receipt_template_validator_passes() -> None:
    proc = _run("verification/scripts/validate_build_gate_receipt_template.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_perception_protocol_validator_passes() -> None:
    proc = _run("verification/scripts/validate_perception_eval_protocol_bins.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_perception_protocol_validator_rejects_missing_bin(tmp_path: Path) -> None:
    src = ROOT / "docs" / "PERCEPTION_EVAL_PROTOCOL_ILLUMINATION_TERRAIN_BINS_v0.1.md"
    text = src.read_text(encoding="utf-8").replace("I3_high_glare", "I3_removed")
    bad_doc = tmp_path / "bad_protocol.md"
    bad_doc.write_text(text, encoding="utf-8")

    proc = _run(
        "verification/scripts/validate_perception_eval_protocol_bins.py",
        "--doc",
        str(bad_doc),
    )
    assert proc.returncode != 0
    assert "I3_high_glare" in (proc.stdout + proc.stderr)


def test_nasa_jpl_retry_queue_validator_passes() -> None:
    proc = _run("verification/scripts/check_nasa_jpl_retry_queue.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr
