#!/usr/bin/env python3
"""Generate deterministic CAD export receipt for interface freeze handoff."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARAMS_PATH = ROOT / "cad" / "weevil_leg_params.yaml"
EXPORT_SOURCE_DIR = ROOT / "cad" / "export"
EXPORT_RECEIPT_DIR = ROOT / "cad" / "exports" / "latest"

FORMAT_MAP = {
    ".step": "STEP",
    ".stp": "STEP",
    ".urdf": "URDF",
    ".stl": "STL",
    ".csv": "CSV",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit_hash() -> str:
    val = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", val):
        raise RuntimeError(f"Unexpected git hash format: {val}")
    return val


def parse_yaml_version() -> str:
    for line in PARAMS_PATH.read_text(encoding="utf-8").splitlines():
        if "version:" in line:
            v = line.split(":", 1)[1].strip().strip('"')
            if v:
                return v
    return "unknown"


def collect_artifacts() -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for p in sorted(EXPORT_SOURCE_DIR.glob("**/*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in FORMAT_MAP:
            continue
        rel = p.relative_to(ROOT).as_posix()
        artifacts.append({
            "path": rel,
            "format": FORMAT_MAP[p.suffix.lower()],
            "sha256": sha256(p),
        })
    return artifacts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interface-version", default="v0.4")
    ap.add_argument("--cots-profile-id", default="rm-v1")
    ap.add_argument("--freecad-version", default="FreeCAD-unknown")
    ap.add_argument(
        "--notes",
        default="Auto-generated export receipt for interface freeze handoff.",
    )
    args = ap.parse_args()

    artifacts = collect_artifacts()
    if not artifacts:
        raise SystemExit("No export artifacts found under cad/export")

    total_bytes = sum((ROOT / a["path"]).stat().st_size for a in artifacts)
    receipt = {
        "schema_version": "1.1",
        "timestamp_utc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "git_commit_hash": git_commit_hash(),
        "yaml_version": parse_yaml_version(),
        "interface_version": args.interface_version,
        "cots_profile_id": args.cots_profile_id,
        "param_source": "cad/weevil_leg_params.yaml",
        "params_hash_sha256": sha256(PARAMS_PATH),
        "exporter_tool": "cad/scripts/generate_export_receipt.py + Phase2_Export.FCMacro",
        "freecad_version": args.freecad_version,
        "exported_files": artifacts,
        "total_artifact_count": len(artifacts),
        "total_artifact_size_bytes": total_bytes,
        "notes": args.notes,
    }

    EXPORT_RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    versioned = EXPORT_RECEIPT_DIR / f"export_receipt_{args.interface_version}.json"
    latest = EXPORT_RECEIPT_DIR / "export_receipt_latest.json"

    versioned.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(versioned, latest)

    print(f"Wrote {versioned}")
    print(f"Updated {latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
