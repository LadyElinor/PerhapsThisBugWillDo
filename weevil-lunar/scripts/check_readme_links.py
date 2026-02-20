#!/usr/bin/env python3
"""Check local README markdown links resolve to existing files."""

from __future__ import annotations

import re
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    local_links = [
        link for link in links if not link.startswith("http") and not link.startswith("#")
    ]

    missing: list[str] = []
    for link in local_links:
        target = (root / link).resolve()
        if not target.exists():
            missing.append(link)

    if missing:
        print("Missing README links:")
        for m in missing:
            print(f"- {m}")
        return 1

    print(f"README link check passed ({len(local_links)} local links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
