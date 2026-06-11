"""Pytest collection guard for verification/.

The top-level ``test_*.py`` files in this directory are verification
HARNESSES (report generators with a ``main()``), not pytest tests. Without
this guard, ``pytest verification/`` silently collects zero tests from them
and returns a false green. Excluding them here makes the boundary explicit:
pytest owns ``verification/tests/``; harnesses are executed and evaluated by
``run_verification_suite.py`` under the contracts in
``harness_manifest.yaml`` (from which this ignore list is derived, so the
two can never disagree).
"""

from __future__ import annotations

from pathlib import Path

import yaml

_MANIFEST = Path(__file__).resolve().parent / "harness_manifest.yaml"


def _harness_filenames() -> list[str]:
    data = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
    names: list[str] = []
    for spec in data.get("harnesses", {}).values():
        script = Path(spec.get("script", ""))
        if script.parts and script.parts[0] == "verification":
            names.append(script.name)
    return names


collect_ignore = _harness_filenames()
