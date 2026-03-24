#!/usr/bin/env python3
"""Validate perception eval protocol doc contains required illumination/terrain bins."""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_DOC = Path("docs/PERCEPTION_EVAL_PROTOCOL_ILLUMINATION_TERRAIN_BINS_v0.1.md")

REQUIRED_ILLUM = ["I0_shadow", "I1_grazing", "I2_nominal", "I3_high_glare"]
REQUIRED_TERRAIN = ["T0_compacted_flat", "T1_loose_fine", "T2_rocky_mixed", "T3_steep_sloped"]
REQUIRED_PHRASES = [
    "all 16 combinations",
    "Minimum samples per cell: 50 frames",
    "10 short sequences",
    "Stop-now recall >= 0.98",
    "Bohmian scope must remain untouched",
]


class ValidationError(Exception):
    """Raised when protocol doc is missing required governance content."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    args = parser.parse_args()

    text = args.doc.read_text(encoding="utf-8")

    missing = []
    for token in REQUIRED_ILLUM + REQUIRED_TERRAIN + REQUIRED_PHRASES:
        if token not in text:
            missing.append(token)

    if missing:
        print(f"ERROR: missing required protocol markers in {args.doc}:")
        for token in missing:
            print(f"  - {token}")
        return 1

    print(f"OK: perception eval protocol bins doc passes required marker checks ({args.doc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
