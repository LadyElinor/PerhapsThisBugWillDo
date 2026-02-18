"""Very small YAML subset parser for project parameter files.
Supports:
- nested mappings by indentation (2 spaces)
- scalars: str, int, float, bool
- inline lists: [a, b]
- comments with '#'
"""

from __future__ import annotations

import ast
from typing import Any


def _parse_scalar(text: str) -> Any:
    t = text.strip()
    if t in {"true", "True"}:
        return True
    if t in {"false", "False"}:
        return False
    if t.startswith("[") and t.endswith("]"):
        inner = t[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(p.strip()) for p in inner.split(",")]
    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
        return t[1:-1]
    try:
        return ast.literal_eval(t)
    except Exception:
        return t


def load_yaml_text(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        key, sep, val = line.strip().partition(":")
        if sep != ":":
            continue

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if val.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(val.strip())

    return root
