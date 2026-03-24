#!/usr/bin/env python3
"""Validate build gate receipt template against schema and basic path policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema

DEFAULT_TEMPLATE = Path("verification/templates/build_gate_receipt_template.json")
DEFAULT_SCHEMA = Path("verification/data_schema/build_gate_receipt.schema.json")


class ValidationError(Exception):
    """Raised when template fails policy checks."""


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError(f"Expected JSON object: {path}")
    return data


def _policy_checks(template: dict, repo_root: Path) -> None:
    traceability = template.get("traceability", {})
    for key in ("icd_catalog", "icd_schema"):
        rel_path = traceability.get(key)
        if not isinstance(rel_path, str):
            raise ValidationError(f"traceability.{key} must be a path string")
        full = repo_root / rel_path
        if not full.exists():
            raise ValidationError(f"Referenced traceability path missing: {rel_path}")

    evidence = template.get("evidence", [])
    if not evidence:
        raise ValidationError("At least one evidence item is required")
    for item in evidence:
        path = item.get("path")
        if not isinstance(path, str):
            raise ValidationError("Each evidence item must contain a string path")
        if path.startswith("/") or path.startswith(".."):
            raise ValidationError(f"Evidence path must be repo-relative and safe: {path}")



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    template = _load_json(args.template)
    schema = _load_json(args.schema)

    jsonschema.validate(instance=template, schema=schema)
    _policy_checks(template, repo_root=Path("."))

    print(f"OK: build gate receipt template is valid ({args.template})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
