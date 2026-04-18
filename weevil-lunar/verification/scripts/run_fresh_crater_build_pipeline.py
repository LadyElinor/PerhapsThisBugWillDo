#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
GENERATED = ROOT / "cad" / "generated" / "weevil_leg_params_fresh_crater_2026-04-18.yaml"

STEPS = [
    [PY, "verification/scripts/validate_fresh_crater_variants.py"],
    [PY, "verification/scripts/retrieve_fresh_crater_variant.py"],
    [PY, "verification/scripts/evaluate_fresh_crater_variants.py"],
    [PY, "verification/scripts/select_fresh_crater_variant.py", "--mission-intent", "baseline", "--runtime-energy-reserve", "0.30", "--runtime-telemetry-buffer-s", "180"],
    [PY, "verification/scripts/generate_fresh_crater_build_preset.py"],
    [PY, "verification/scripts/materialize_fresh_crater_leg_params.py"],
    [PY, "cad/scripts/validate_weevil_leg_params.py", "--path", str(GENERATED)],
    [PY, "verification/test_fresh_crater_preset_integrity.py"],
]


def main() -> None:
    for step in STEPS:
        print(f"RUNNING={' '.join(step)}")
        result = subprocess.run(step, cwd=ROOT)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
    print("STATUS=pass")


if __name__ == "__main__":
    main()
