#!/usr/bin/env python3
"""Validate ICD contract catalog YAML against JSON schema + policy checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema
import yaml

DEFAULT_CATALOG = Path("icd/contract_catalog_v0.2.yaml")
DEFAULT_SCHEMA = Path("icd/contract_catalog.schema.json")


class ValidationError(Exception):
    """Raised when catalog fails policy checks."""


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError(f"Catalog must be a mapping: {path}")
    return data


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationError(f"Schema must be an object: {path}")
    return data


def _policy_checks(catalog: dict) -> None:
    contracts = catalog.get("contracts", [])

    messages_seen: set[str] = set()
    for idx, contract in enumerate(contracts):
        message = contract.get("message")
        if message in messages_seen:
            raise ValidationError(f"Duplicate contract message '{message}' at index {idx}")
        messages_seen.add(message)

        fields = contract.get("fields", [])
        field_names: set[str] = set()
        for field in fields:
            name = field.get("name")
            if name in field_names:
                raise ValidationError(f"Duplicate field '{name}' in message '{message}'")
            field_names.add(name)

            ftype = field.get("type")
            if ftype == "number":
                min_v = field.get("min")
                max_v = field.get("max")
                if min_v is not None and max_v is not None and min_v > max_v:
                    raise ValidationError(
                        f"Invalid range in '{message}.{name}': min ({min_v}) > max ({max_v})"
                    )



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    catalog = _load_yaml(args.catalog)
    schema = _load_json(args.schema)

    jsonschema.validate(instance=catalog, schema=schema)
    _policy_checks(catalog)

    print(f"OK: ICD contract catalog is valid ({args.catalog})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
