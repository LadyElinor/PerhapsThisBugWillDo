#!/usr/bin/env python3
"""Validate (and optionally regenerate) NASA-JPL prioritized retry queue artifacts."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

QUEUE_CSV = Path("analysis/nasa_jpl_retry_queue_prioritized.csv")
QUEUE_MD = Path("analysis/nasa_jpl_retry_queue_prioritized.md")
GENERATOR = Path("tools/build_nasa_jpl_retry_queue.py")

EXPECTED_HEADERS = ["repo", "priority", "priority_reason", "status", "last_error", "suggested_action"]


class ValidationError(Exception):
    """Raised when retry queue artifact validation fails."""


def _run_generator() -> None:
    subprocess.run([sys.executable, str(GENERATOR)], check=True)


def _validate_csv(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"Missing queue CSV: {path}")

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED_HEADERS:
            raise ValidationError(f"Unexpected CSV headers in {path}: {reader.fieldnames}")

        rows = list(reader)

    if not rows:
        raise ValidationError("Retry queue CSV is empty")

    last_key: tuple[int, str, str] | None = None
    for row in rows:
        repo = row["repo"]
        status = row["status"]
        suggested_action = row["suggested_action"]
        priority = int(row["priority"])

        if status not in {"pending_retry", "recovered"}:
            raise ValidationError(f"Invalid status for {repo}: {status}")
        if priority < 0 or priority > 3:
            raise ValidationError(f"Invalid priority for {repo}: {priority}")

        if status == "pending_retry" and suggested_action != "retry_when_rate_limit_resets":
            raise ValidationError(f"pending_retry row must suggest retry_when_rate_limit_resets: {repo}")

        if status == "recovered" and not suggested_action.startswith("defer"):
            raise ValidationError(f"recovered row must suggest defer: {repo}")

        key = (-priority, status, repo)
        if last_key is not None and key < last_key:
            raise ValidationError("Retry queue CSV is not stably sorted by (-priority, status, repo)")
        last_key = key


def _validate_md(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"Missing queue markdown summary: {path}")

    text = path.read_text(encoding="utf-8")
    required = [
        "# NASA-JPL Retry Queue (Prioritized)",
        "## Priority policy",
        "## Top pending items",
    ]
    for token in required:
        if token not in text:
            raise ValidationError(f"Missing section in markdown summary: {token}")


def _ensure_clean_outputs() -> None:
    diff = subprocess.run(
        ["git", "diff", "--", str(QUEUE_CSV), str(QUEUE_MD)],
        capture_output=True,
        text=True,
        check=False,
    )
    if diff.returncode != 0:
        raise ValidationError("Failed to run git diff for queue outputs")
    if diff.stdout.strip():
        raise ValidationError(
            "Retry queue artifacts changed after regeneration. Commit updated analysis outputs."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Regenerate queue artifacts before validating and enforce clean output drift check.",
    )
    args = parser.parse_args()

    if args.rebuild:
        _run_generator()

    _validate_csv(QUEUE_CSV)
    _validate_md(QUEUE_MD)

    if args.rebuild:
        _ensure_clean_outputs()

    print("OK: NASA-JPL retry queue artifacts valid")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
