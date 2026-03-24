#!/usr/bin/env python3
"""Build prioritized retry queue for failed nasa-jpl bulk ingest entries.

Reads local ingest logs only (no network I/O) and produces a reproducible queue CSV/MD.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

INGEST_LOG = Path("docs/external/_bulk_ingest_logs/nasa-jpl_ingest_1774316803.json")
RETRY_LOG = Path("docs/external/_bulk_ingest_logs/nasa-jpl_retry_relevance.json")
OUT_CSV = Path("analysis/nasa_jpl_retry_queue_prioritized.csv")
OUT_MD = Path("analysis/nasa_jpl_retry_queue_prioritized.md")

MISSION_PRIORITY = {
    "critical": [
        "ros2-ion",
        "ion-dtn",
        "ion-core",
        "visual-perception-engine",
        "lunasynth",
        "martian",
        "mbl_mars",
        "motor_model",
        "tasksat",
        "rosa",
        "rosco",
    ],
    "high": ["open-source-rover", "osr-rover-code", "blackbird", "landmark", "isaacsim"],
    "medium": ["urdf", "rover", "localization", "hazard", "sim"],
}


def _score_repo(repo: str) -> tuple[int, str]:
    r = repo.lower()
    for kw in MISSION_PRIORITY["critical"]:
        if kw in r:
            return 3, f"critical:{kw}"
    for kw in MISSION_PRIORITY["high"]:
        if kw in r:
            return 2, f"high:{kw}"
    for kw in MISSION_PRIORITY["medium"]:
        if kw in r:
            return 1, f"medium:{kw}"
    return 0, "low:generic"


def main() -> None:
    ingest = json.loads(INGEST_LOG.read_text(encoding="utf-8"))
    retry = json.loads(RETRY_LOG.read_text(encoding="utf-8"))

    recovered = {r["repo"]: r for r in retry.get("results", []) if r.get("ok")}

    failed = [r for r in ingest.get("repos", []) if not r.get("ok")]

    rows: list[dict[str, str | int]] = []
    for item in failed:
        repo = item.get("repo", "")
        priority, reason = _score_repo(repo)
        was_recovered = repo in recovered
        rows.append(
            {
                "repo": repo,
                "priority": priority,
                "priority_reason": reason,
                "status": "recovered" if was_recovered else "pending_retry",
                "last_error": item.get("error", ""),
                "suggested_action": "defer (already recovered)" if was_recovered else "retry_when_rate_limit_resets",
            }
        )

    rows.sort(key=lambda r: (-int(r["priority"]), str(r["status"]), str(r["repo"])))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["repo", "priority", "priority_reason", "status", "last_error", "suggested_action"],
        )
        w.writeheader()
        w.writerows(rows)

    pending = [r for r in rows if r["status"] == "pending_retry"]
    recovered_rows = [r for r in rows if r["status"] == "recovered"]

    md = [
        "# NASA-JPL Retry Queue (Prioritized)",
        "",
        f"- Source ingest failures: {len(failed)}",
        f"- Recovered via targeted retry log: {len(recovered_rows)}",
        f"- Remaining pending retry: {len(pending)}",
        "",
        "## Priority policy",
        "- 3 = critical lunar-weevil relevance (DTN/comms/perception/sim/mobility/task verification).",
        "- 2 = high architecture adjacency (rover/localization/isaacsim references).",
        "- 1 = medium possible relevance.",
        "- 0 = low/default.",
        "",
        "## Top pending items",
        "",
        "| repo | priority | reason |",
        "|---|---:|---|",
    ]
    for r in pending[:20]:
        md.append(f"| {r['repo']} | {r['priority']} | {r['priority_reason']} |")

    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
