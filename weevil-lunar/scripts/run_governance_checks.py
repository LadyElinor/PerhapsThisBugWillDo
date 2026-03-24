#!/usr/bin/env python3
"""Cross-platform runner for governance artifact checks."""

from __future__ import annotations

import subprocess
import sys

COMMANDS = [
    ["verification/scripts/validate_icd_contract_catalog.py"],
    ["verification/scripts/validate_build_gate_receipt_template.py"],
    ["verification/scripts/validate_perception_eval_protocol_bins.py"],
    ["verification/scripts/check_nasa_jpl_retry_queue.py"],
]


def main() -> int:
    for cmd in COMMANDS:
        full = [sys.executable, *cmd]
        print(f"[governance] running: {' '.join(full)}")
        result = subprocess.run(full, check=False)
        if result.returncode != 0:
            return result.returncode
    print("[governance] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
