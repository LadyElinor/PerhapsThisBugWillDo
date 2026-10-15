#!/usr/bin/env python3
"""Report mechanically available screw travel without changing design parameters."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from models.lunar_integrated_weevil_leg import PARAMS_PATH, load_params, screw_travel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, default=PARAMS_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    params = load_params(args.params)
    travel = screw_travel(params)
    report = {
        "params_sha256": hashlib.sha256(args.params.read_bytes()).hexdigest(),
        "derived_from": "configured design parameters; not measured hardware",
        "screw": asdict(travel),
        "effective_tibia_length_endpoints_mm": [
            (params.tibia_stroke_mm - travel.available_travel_mm) / 2,
            (params.tibia_stroke_mm + travel.available_travel_mm) / 2,
        ],
        "decision": "Confirm intended operating travel before changing lead, stroke or rotation limits.",
    }
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
