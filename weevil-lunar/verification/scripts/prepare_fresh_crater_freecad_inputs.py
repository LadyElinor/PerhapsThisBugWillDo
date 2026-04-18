#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
GENERATED_YAML = ROOT / "cad" / "generated" / "weevil_leg_params_fresh_crater_2026-04-18.yaml"
BASE_CSV = ROOT / "cad" / "generated" / "freecad_spreadsheet_template_fresh_crater_2026-04-18.csv"
PHASE2_CSV = ROOT / "cad" / "generated" / "phase2_template_aliases_fresh_crater_2026-04-18.csv"
RECEIPT_JSON = ROOT / "cad" / "generated" / "fresh_crater_freecad_input_receipt_2026-04-18.json"
RECEIPT_MD = ROOT / "cad" / "generated" / "fresh_crater_freecad_input_receipt_2026-04-18.md"


def main() -> None:
    if not GENERATED_YAML.exists():
        raise FileNotFoundError(f"missing generated crater params: {GENERATED_YAML}")

    cmd = [
        PY,
        "cad/scripts/generate_csvs_from_yaml.py",
        "--yaml",
        str(GENERATED_YAML),
        "--base-csv",
        str(BASE_CSV),
        "--phase2-csv",
        str(PHASE2_CSV),
    ]
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    receipt = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "generated_yaml": str(GENERATED_YAML),
        "freecad_spreadsheet_csv": str(BASE_CSV),
        "phase2_alias_csv": str(PHASE2_CSV),
        "freecad_cmd_available": False,
        "next_macro": "cad/Phase2_Templates.FCMacro",
        "macro_csv_override_required": True,
        "notes": [
            "FreeCADCmd was not available on PATH during automation.",
            "Prepared crater-specific CSV inputs for manual or later automated FreeCAD macro execution.",
        ],
    }

    RECEIPT_JSON.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    RECEIPT_MD.write_text(
        "\n".join(
            [
                "# Fresh Crater FreeCAD Input Receipt",
                "",
                f"- timestamp_utc: {receipt['timestamp_utc']}",
                f"- generated_yaml: `{GENERATED_YAML}`",
                f"- freecad_spreadsheet_csv: `{BASE_CSV}`",
                f"- phase2_alias_csv: `{PHASE2_CSV}`",
                f"- freecad_cmd_available: `{receipt['freecad_cmd_available']}`",
                f"- next_macro: `{receipt['next_macro']}`",
                f"- macro_csv_override_required: `{receipt['macro_csv_override_required']}`",
                "",
                "## Notes",
                "- FreeCADCmd was not available on PATH during this run.",
                "- These crater-specific CSVs are ready to feed into `Phase2_Templates.FCMacro` after swapping or parameterizing its CSV paths.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {BASE_CSV}")
    print(f"Wrote {PHASE2_CSV}")
    print(f"Wrote {RECEIPT_JSON}")
    print(f"Wrote {RECEIPT_MD}")
    print("STATUS=pass")


if __name__ == "__main__":
    main()
