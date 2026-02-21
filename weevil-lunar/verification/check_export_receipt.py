#!/usr/bin/env python3
"""Validate CAD export receipt presence, shape, freshness, and param hash consistency."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "cad" / "weevil_leg_params.yaml"
DEFAULT_RECEIPT = ROOT / "cad" / "exports" / "latest" / "export_receipt_v0.4.json"

REQUIRED_KEYS = {
    "schema_version",
    "timestamp_utc",
    "git_commit_hash",
    "yaml_version",
    "interface_version",
    "cots_profile_id",
    "params_hash_sha256",
    "exporter_tool",
    "freecad_version",
    "exported_files",
    "notes",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_ts(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", default=str(DEFAULT_RECEIPT))
    ap.add_argument("--max-age-days", type=int, default=7)
    args = ap.parse_args()

    receipt_path = Path(args.receipt)
    if not receipt_path.exists():
        raise SystemExit(f"Missing export receipt: {receipt_path}")

    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        raise SystemExit(f"Receipt missing required keys: {sorted(missing)}")

    if not re.fullmatch(r"[0-9a-f]{40}", data["git_commit_hash"]):
        raise SystemExit("git_commit_hash must be full 40-char hex")

    if len(str(data["cots_profile_id"]).strip()) < 3:
        raise SystemExit("cots_profile_id must be at least 3 characters")

    if len(data["notes"].strip()) < 10:
        raise SystemExit("notes must be at least 10 characters")

    expected_param_hash = sha256(PARAMS)
    if data["params_hash_sha256"] != expected_param_hash:
        raise SystemExit(
            "params_hash_sha256 mismatch: "
            f"receipt={data['params_hash_sha256']} current={expected_param_hash}"
        )

    artifacts = data.get("exported_files", [])
    if not artifacts:
        raise SystemExit("Receipt exported_files list is empty")

    for artifact in artifacts:
        p = ROOT / artifact["path"]
        if not p.exists():
            raise SystemExit(f"Missing artifact declared in receipt: {artifact['path']}")

    ts = parse_ts(data["timestamp_utc"])
    age_days = (dt.datetime.now(dt.timezone.utc) - ts).days
    if age_days > args.max_age_days:
        raise SystemExit(f"Receipt is stale: {age_days} days old (max {args.max_age_days})")

    print("Export receipt check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
