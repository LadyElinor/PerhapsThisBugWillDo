#!/usr/bin/env python3
"""Validate run config YAML against v0.2 JSON schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "experiments" / "schemas" / "run_config.schema.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", help="Path to run config YAML")
    args = ap.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Missing config: {config_path}")

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    validate(instance=config, schema=schema)

    print(f"Run config valid: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
