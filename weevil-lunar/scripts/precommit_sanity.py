#!/usr/bin/env python3
"""Pre-commit sanity checks for repo hygiene in mixed-workspace setups."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FORBIDDEN_FRAGMENTS = ["__pycache__/", ".pytest_cache/", ".ruff_cache/", ".coverage", "htmlcov/"]
ALLOWED_PREFIXES = ["weevil-lunar/"]


def _staged_files() -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def main() -> int:
    staged = _staged_files()
    if not staged:
        print("[sanity] no staged files")
        return 0

    bad = [p for p in staged if any(tok in p for tok in FORBIDDEN_FRAGMENTS)]
    if bad:
        print("[sanity] forbidden staged artifacts detected:")
        for p in bad:
            print(f"  - {p}")
        return 1

    outside = [p for p in staged if not any(p.startswith(prefix) for prefix in ALLOWED_PREFIXES)]
    if outside:
        print("[sanity] staged files outside expected project scope (weevil-lunar/):")
        for p in outside:
            print(f"  - {p}")
        print("[sanity] use explicit path-scoped git add to avoid cross-project commits")
        return 1

    print(f"[sanity] OK ({len(staged)} staged files in weevil-lunar scope)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
