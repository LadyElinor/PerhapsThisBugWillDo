#!/usr/bin/env python3
"""Run every registered verification harness and emit execution receipts.

For each harness in verification/harness_manifest.yaml this runner:
  1. executes the script as a subprocess (MPLBACKEND=Agg, cwd=weevil-lunar),
  2. records exit code and wall time,
  3. evaluates each declared report under its schema contract,
  4. computes the harness's combined status.

Output: verification/reports/receipts.json (plus a human-readable
receipts.md), containing per-report SHA-256 hashes, the git commit, and a
timestamp -- the executed evidence that run_gate_check.py and
sync_traceability.py consume. The runner records; the gate enforces:
this script exits 0 even on failing harnesses so the receipts themselves
are always produced. Use `run_gate_check.py --strict` to gate.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import (  # noqa: E402
    MANIFEST_PATH,
    WEEVIL_ROOT,
    combine,
    evaluate_report,
    load_manifest,
    resolve_report_path,
    sha256_of,
    write_receipts,
)


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=WEEVIL_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except OSError:
        return "unknown"


def run_harness(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    cmd = [sys.executable] + list(spec.get("run") or [spec["script"]])
    data_source = spec["data_source"]
    env = dict(os.environ, MPLBACKEND="Agg")
    t0 = time.monotonic()
    proc = subprocess.run(cmd, cwd=WEEVIL_ROOT, env=env, capture_output=True, text=True)
    duration = round(time.monotonic() - t0, 3)

    reports: list[dict[str, Any]] = []
    statuses: list[str] = []
    for rspec in spec.get("reports", []):
        path = resolve_report_path(rspec["file"])
        status, detail = evaluate_report(rspec, path)
        statuses.append(status)
        reports.append(
            {
                "file": rspec["file"],
                "sha256": sha256_of(path) if path.exists() else None,
                "status": status,
                "detail": detail,
            }
        )

    if proc.returncode != 0:
        status = "error"
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        detail = f"exit {proc.returncode}: " + " | ".join(tail)
    else:
        status = combine(statuses)
        detail = "; ".join(r["detail"] for r in reports)

    blocked_by_finding = list(spec.get("blocked_by_finding", []))
    evidence_pass = status == "pass" and data_source in {"backend", "hardware"}
    contract_pass = status == "pass"

    return {
        "script": spec["script"],
        "command": cmd[1:],
        "data_source": data_source,
        "blocked_by_finding": blocked_by_finding,
        "exit_code": proc.returncode,
        "duration_s": duration,
        "reports": reports,
        "status": status,
        "contract_pass": contract_pass,
        "evidence_pass": evidence_pass,
        "detail": detail,
    }


def main() -> int:
    manifest = load_manifest()
    harnesses = manifest.get("harnesses", {})

    results: dict[str, Any] = {}
    for name in sorted(harnesses):
        results[name] = run_harness(name, harnesses[name])
        print(f"[{results[name]['status']:>7}] {name} ({results[name]['duration_s']}s)")

    summary: dict[str, int] = {}
    for r in results.values():
        summary[r["status"]] = summary.get(r["status"], 0) + 1

    by_data_source: dict[str, int] = {}
    for r in results.values():
        by_data_source[r["data_source"]] = by_data_source.get(r["data_source"], 0) + 1

    data = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "manifest": str(MANIFEST_PATH.relative_to(WEEVIL_ROOT)),
        "harnesses": results,
        "summary": summary,
        "contract_summary": {
            "pass": sum(1 for r in results.values() if r["contract_pass"]),
            "not_pass": sum(1 for r in results.values() if not r["contract_pass"]),
        },
        "evidence_summary": {
            "pass": sum(1 for r in results.values() if r["evidence_pass"]),
            "not_pass": sum(1 for r in results.values() if not r["evidence_pass"]),
        },
        "data_sources": by_data_source,
    }
    write_receipts(data)

    md = [
        "# Verification Suite Receipts",
        "",
        f"- generated: {data['generated_at']}",
        f"- commit: {data['git_commit']}",
        f"- contract pass harnesses: {data['contract_summary']['pass']}",
        f"- evidence pass harnesses: {data['evidence_summary']['pass']}",
        "",
        "| harness | status | data_source | contract_pass | evidence_pass | detail |",
        "|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        md.append(f"| {name} | {r['status']} | {r['data_source']} | {r['contract_pass']} | {r['evidence_pass']} | {r['detail']} |")
    md_path = WEEVIL_ROOT / "verification" / "reports" / "receipts.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"\nSummary: {summary}")
    print(f"Wrote {WEEVIL_ROOT / 'verification' / 'reports' / 'receipts.json'}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
