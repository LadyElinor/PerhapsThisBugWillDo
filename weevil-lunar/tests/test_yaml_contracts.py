from pathlib import Path

import yaml
from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]


def test_data_contract_yaml_parses() -> None:
    path = ROOT / "icd" / "data_contracts.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_data_contract_schema_validation() -> None:
    data_path = ROOT / "icd" / "data_contracts.yaml"
    schema_path = ROOT / "icd" / "data_contracts.schema.json"
    data = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    validate(instance=data, schema=schema)
