#!/usr/bin/env python3
"""Shared receipts library for the Weevil-Lunar verification spine.

Single implementation of:
  * manifest loading (harness_manifest.yaml is the declared contract),
  * per-report evaluation under that contract (pass_column / threshold /
    gate_table kinds),
  * status combination semantics,
  * receipts.json read/write with content hashes.

Status vocabulary (severity order, worst wins when combining):
  error    schema mismatch, unreadable report, or script crashed --
            the *instrumentation* is broken, distinct from a failing test
  missing  expected report artifact absent or empty
  drift    a gate's actual outcome contradicts its declared expectation
            (an expected-fail that passes, or an expected-pass that fails,
            inside a gate_table)
  fail     all gating rows fail
  partial  some gating rows fail
  pass     everything consistent with declared expectations

The old aggregator hardcoded a column literally named `pass` and silently
reported `fail` on any report with a different schema. Here a schema
mismatch is `error` -- loudly distinguished from a real engineering failure.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

WEEVIL_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = WEEVIL_ROOT / "verification" / "harness_manifest.yaml"
REPORT_DIR = WEEVIL_ROOT / "verification" / "reports"
RECEIPTS_PATH = REPORT_DIR / "receipts.json"

SEVERITY = ["pass", "partial", "fail", "drift", "missing", "error"]

_TRUTHY = {"true", "1", "yes", "pass"}


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in _TRUTHY


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"unsupported or missing schema_version in {path}")
    return data


def resolve_report_path(file_field: str) -> Path:
    """Report paths resolve from verification/reports/ unless ../-prefixed."""
    if file_field.startswith("../"):
        return (WEEVIL_ROOT / file_field).resolve()
    return REPORT_DIR / file_field


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def combine(statuses: list[str]) -> str:
    """Worst status wins; an empty list is `missing` (nothing was produced)."""
    if not statuses:
        return "missing"
    return max(statuses, key=lambda s: SEVERITY.index(s) if s in SEVERITY else len(SEVERITY))


def _read_rows(path: Path) -> list[dict[str, str]] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def evaluate_report(spec: dict[str, Any], path: Path) -> tuple[str, str]:
    """Evaluate one report file under its declared contract.

    Returns (status, detail). Never raises on bad data: contract violations
    surface as `error` with a diagnostic detail string.
    """
    rows = _read_rows(path)
    if rows is None:
        return "missing", f"{path.name}: not found"
    if not rows:
        return "missing", f"{path.name}: empty"

    kind = spec.get("kind", "pass_column")

    if kind == "pass_column":
        cols = list(spec.get("pass_columns", ["pass"]))
        absent = [c for c in cols if c not in rows[0]]
        if absent:
            return "error", f"{path.name}: schema mismatch, missing columns {absent}"
        ok = sum(1 for r in rows if all(truthy(r[c]) for c in cols))
        detail = f"{path.name}: {ok}/{len(rows)} rows pass on {cols}"
        if ok == len(rows):
            return "pass", detail
        if ok > 0:
            return "partial", detail
        return "fail", detail

    if kind == "threshold":
        where = spec.get("where", {})
        metric = spec.get("metric", "")
        col, target = where.get("column"), where.get("equals")
        if not (col and metric) or target is None:
            return "error", f"{path.name}: threshold contract incomplete"
        if col not in rows[0] or metric not in rows[0]:
            return "error", f"{path.name}: schema mismatch, need columns [{col}, {metric}]"
        try:
            sel = [r for r in rows if float(r[col]) == float(target)]
            if not sel:
                return "error", f"{path.name}: no row where {col}=={target}"
            val = float(sel[0][metric])
        except ValueError as exc:
            return "error", f"{path.name}: non-numeric data ({exc})"
        lo, hi = spec.get("min"), spec.get("max")
        ok = (lo is None or val >= float(lo)) and (hi is None or val <= float(hi))
        bound = f"min={lo}" if hi is None else (f"max={hi}" if lo is None else f"min={lo},max={hi}")
        detail = f"{path.name}: {metric}={val} at {col}={target} ({bound})"
        return ("pass" if ok else "fail"), detail

    if kind == "gate_table":
        name_col = spec.get("name_column", "gate_id")
        pass_col = spec.get("pass_column", "passed")
        if name_col not in rows[0] or pass_col not in rows[0]:
            return "error", f"{path.name}: schema mismatch, need columns [{name_col}, {pass_col}]"
        expected_fail = set(spec.get("expected_fail", []))
        drift: list[str] = []
        seen: set[str] = set()
        for r in rows:
            gid = r[name_col]
            seen.add(gid)
            actual = truthy(r[pass_col])
            expected = gid not in expected_fail
            if actual != expected:
                drift.append(f"{gid}: expected {'pass' if expected else 'fail'}, got {'pass' if actual else 'fail'}")
        ghost = sorted(expected_fail - seen)
        if ghost:
            drift.extend(f"{g}: declared expected-fail but absent from report" for g in ghost)
        if drift:
            return "drift", f"{path.name}: " + "; ".join(drift)
        n_exp = len(expected_fail)
        return "pass", f"{path.name}: {len(rows)} gates consistent ({n_exp} documented expected-fail)"

    return "error", f"{path.name}: unknown report kind '{kind}'"


def gate_outcomes(spec: dict[str, Any], path: Path) -> dict[str, bool]:
    """Per-gate actual pass/fail map for a gate_table report (for sync)."""
    rows = _read_rows(path) or []
    name_col = spec.get("name_column", "gate_id")
    pass_col = spec.get("pass_column", "passed")
    out: dict[str, bool] = {}
    for r in rows:
        if name_col in r and pass_col in r:
            out[r[name_col]] = truthy(r[pass_col])
    return out


def load_receipts(path: Path = RECEIPTS_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found -- run `python verification/run_verification_suite.py` first"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def write_receipts(data: dict[str, Any], path: Path = RECEIPTS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
