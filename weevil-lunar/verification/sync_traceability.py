#!/usr/bin/env python3
"""Derive requirements_traceability.csv `status` from executed receipts.

The traceability CSV maps requirement IDs to verification evidence. Its
`status` column is DERIVED here from verification/reports/receipts.json --
never hand-typed -- closing the gap between asserted and instrumented
status.

Modes:
  --write  rewrite the CSV: derived status, normalized analysis_script
           paths, prior hand-typed status preserved in a `note` column when
           it diverges; regenerates traceability_sync_report.md.
  --check  exit nonzero if (a) any CSV status differs from the derived
           status, (b) any manifest harness is neither referenced by a
           traceability row nor declared in `pending_linkage`, or
           (c) any analysis_script path does not exist. CI mode.

Derived vocabulary: pass, partial, fail, expected-fail, drift, missing,
error, unmapped. `expected-fail` marks a gate declared as a documented
baseline failure in harness_manifest.yaml that is indeed failing.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import (  # noqa: E402
    WEEVIL_ROOT,
    gate_outcomes,
    load_manifest,
    load_receipts,
    resolve_report_path,
)

REQ_PATTERN = re.compile(r"\bREQ-[A-Z]+-\d{3}\b")

# Legacy path normalization: the contact tests moved during consolidation.
SCRIPT_ALIASES = {
    "results/GPT/Robotics/weevil_lunar_tests.py": "models/contact/weevil_lunar_tests.py",
}


def discover_requirements() -> dict[str, set[str]]:
    """Scan specs/ and docs/ for requirement IDs."""
    found: dict[str, set[str]] = {}
    for folder in ("specs", "docs"):
        for md in sorted((WEEVIL_ROOT / folder).glob("*.md")):
            for req in REQ_PATTERN.findall(md.read_text(encoding="utf-8")):
                found.setdefault(req, set()).add(f"{folder}/{md.name}")
    return found


def gate_table_context(manifest: dict[str, Any], harness: str) -> tuple[dict[str, bool], set[str]]:
    """(actual per-gate outcomes, declared expected_fail) for a harness."""
    spec = manifest["harnesses"][harness]
    for rspec in spec.get("reports", []):
        if rspec.get("kind") == "gate_table":
            return gate_outcomes(rspec, resolve_report_path(rspec["file"])), set(
                rspec.get("expected_fail", [])
            )
    return {}, set()


def derive_status(
    test_name: str,
    manifest: dict[str, Any],
    receipts: dict[str, Any],
) -> tuple[str, str, str, bool, list[str]]:
    """Return (derived_status, detail, data_source, evidence_pass, blocked_by_finding)."""
    test_map = manifest.get("traceability", {}).get("test_map", {})
    entry = test_map.get(test_name)
    if entry is None:
        return "unmapped", f"no test_map entry for '{test_name}'", "placeholder", False, []

    harness = entry["harness"]
    h = receipts.get("harnesses", {}).get(harness)
    if h is None:
        return "missing", f"harness '{harness}' absent from receipts", "placeholder", False, []

    data_source = h.get("data_source", "placeholder")
    evidence_pass = bool(h.get("evidence_pass", False))
    blocked_by_finding = list(h.get("blocked_by_finding", []))

    if h["exit_code"] != 0:
        return "error", f"harness '{harness}' exited {h['exit_code']}", data_source, evidence_pass, blocked_by_finding

    if "gate" in entry:
        outcomes, expected_fail = gate_table_context(manifest, harness)
        gid = entry["gate"]
        if gid not in outcomes:
            return "missing", f"gate '{gid}' absent from report", data_source, evidence_pass, blocked_by_finding
        actual = outcomes[gid]
        if gid in expected_fail:
            if actual:
                return "drift", f"gate '{gid}' declared expected-fail but passed", data_source, evidence_pass, blocked_by_finding
            return "expected-fail", f"gate '{gid}' failing as documented (baseline design gap)", data_source, evidence_pass, blocked_by_finding
        return ("pass" if actual else "fail"), f"gate '{gid}' {'passed' if actual else 'failed'}", data_source, evidence_pass, blocked_by_finding

    if "gate_prefix" in entry:
        outcomes, _ = gate_table_context(manifest, harness)
        prefix = entry["gate_prefix"]
        hits = {g: ok for g, ok in outcomes.items() if g.startswith(prefix)}
        if not hits:
            return "missing", f"no gates with prefix '{prefix}'", data_source, evidence_pass, blocked_by_finding
        n_ok = sum(hits.values())
        detail = f"{n_ok}/{len(hits)} gates pass under '{prefix}*'"
        if n_ok == len(hits):
            return "pass", detail, data_source, evidence_pass, blocked_by_finding
        return ("partial" if n_ok else "fail"), detail, data_source, evidence_pass, blocked_by_finding

    return h["status"], f"harness '{harness}' combined status", data_source, evidence_pass, blocked_by_finding


def analyze(
    manifest: dict[str, Any], receipts: dict[str, Any], rows: list[dict[str, str]]
) -> dict[str, Any]:
    problems: list[str] = []
    derived: list[tuple[dict[str, str], str, str, str, bool, list[str]]] = []
    referenced_harnesses: set[str] = set()
    test_map = manifest.get("traceability", {}).get("test_map", {})

    for row in rows:
        status, detail, data_source, evidence_pass, blocked_by_finding = derive_status(row["test_name"], manifest, receipts)
        derived.append((row, status, detail, data_source, evidence_pass, blocked_by_finding))
        entry = test_map.get(row["test_name"])
        if entry:
            referenced_harnesses.add(entry["harness"])
        if status != row["status"]:
            problems.append(
                f"status divergence: {row['requirement_id']}/{row['test_name']}: "
                f"csv='{row['status']}' derived='{status}' ({detail})"
            )
        script = SCRIPT_ALIASES.get(row["analysis_script"], row["analysis_script"])
        if not (WEEVIL_ROOT / script).exists() and not (WEEVIL_ROOT.parent / script).exists():
            problems.append(f"stale analysis_script: {row['analysis_script']}")

    pending = set(manifest.get("traceability", {}).get("pending_linkage", {}))
    unmapped = sorted(set(manifest.get("harnesses", {})) - referenced_harnesses - pending)
    for name in unmapped:
        problems.append(
            f"unmapped harness: '{name}' emits receipts but has no traceability row "
            f"and is not declared in pending_linkage"
        )

    reqs_in_docs = discover_requirements()
    reqs_in_csv = {r["requirement_id"] for r in rows}
    unlinked = sorted(set(reqs_in_docs) - reqs_in_csv)

    return {
        "derived": derived,
        "problems": problems,
        "pending": sorted(pending),
        "pending_reasons": dict(manifest.get("traceability", {}).get("pending_linkage", {})),
        "unlinked_requirements": unlinked,
        "reqs_in_docs": reqs_in_docs,
    }


def write_csv(csv_path: Path, analysis: dict[str, Any]) -> None:
    fieldnames = [
        "requirement_id",
        "spec_section",
        "test_name",
        "analysis_script",
        "result_file",
        "status",
        "data_source",
        "evidence_pass",
        "blocked_by_finding",
        "note",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for row, status, _detail, data_source, evidence_pass, blocked_by_finding in analysis["derived"]:
            note = row.get("note", "")
            if row["status"] != status and row["status"] not in ("", status):
                prior = f"prior hand status: {row['status']}"
                note = f"{note}; {prior}" if note else prior
            w.writerow(
                {
                    "requirement_id": row["requirement_id"],
                    "spec_section": row["spec_section"],
                    "test_name": row["test_name"],
                    "analysis_script": SCRIPT_ALIASES.get(row["analysis_script"], row["analysis_script"]),
                    "result_file": row["result_file"],
                    "status": status,
                    "data_source": data_source,
                    "evidence_pass": str(bool(evidence_pass)).lower(),
                    "blocked_by_finding": ",".join(blocked_by_finding),
                    "note": note,
                }
            )


def write_report(report_path: Path, analysis: dict[str, Any], receipts: dict[str, Any]) -> None:
    lines = [
        "# Traceability Sync Report",
        "",
        "Status column is derived from executed receipts "
        f"(commit {receipts.get('git_commit', 'unknown')}, {receipts.get('generated_at', 'unknown')}).",
        "",
        f"- Requirements found in docs/specs: {len(analysis['reqs_in_docs'])}",
        f"- Rows in traceability CSV: {len(analysis['derived'])}",
        f"- Harnesses pending requirement linkage (declared debt): {len(analysis['pending'])}",
        f"- Requirements with no traceability row: {len(analysis['unlinked_requirements'])}",
        "",
        "## Derived statuses",
        "",
        "| requirement | test | derived status | data_source | evidence_pass | blocked_by_finding | detail |",
        "|---|---|---|---|---|---|---|",
    ]
    for row, status, detail, data_source, evidence_pass, blocked_by_finding in analysis["derived"]:
        lines.append(
            f"| {row['requirement_id']} | {row['test_name']} | {status} | {data_source} | {str(bool(evidence_pass)).lower()} | {','.join(blocked_by_finding)} | {detail} |"
        )
    lines += ["", "## Harnesses pending requirement linkage", ""]
    if analysis["pending_reasons"]:
        lines += [f"- {name}: {reason}" for name, reason in sorted(analysis["pending_reasons"].items())]
    else:
        lines.append("- none")
    lines += ["", "## Requirements with no traceability row", ""]
    lines += [f"- {r}" for r in analysis["unlinked_requirements"]] or ["- none"]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="rewrite CSV with derived statuses")
    mode.add_argument("--check", action="store_true", help="fail on divergence (CI mode)")
    args = parser.parse_args()

    manifest = load_manifest()
    receipts = load_receipts()

    csv_path = WEEVIL_ROOT / manifest.get("traceability", {}).get(
        "csv", "verification/requirements_traceability.csv"
    )
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    analysis = analyze(manifest, receipts, rows)
    report_path = WEEVIL_ROOT / "verification" / "traceability_sync_report.md"

    if args.write:
        write_csv(csv_path, analysis)
        write_report(report_path, analysis, receipts)
        print(f"Wrote {csv_path}")
        print(f"Wrote {report_path}")
        for p in analysis["problems"]:
            print(f"  resolved/write: {p}")
        return 0

    for p in analysis["problems"]:
        print(f"TRACEABILITY CHECK: {p}")
    if analysis["unlinked_requirements"]:
        print(
            "TRACEABILITY NOTE: requirements without rows (not failing, tracked in report): "
            + ", ".join(analysis["unlinked_requirements"])
        )
    if analysis["problems"]:
        print(f"STATUS=fail ({len(analysis['problems'])} problem(s))")
        return 1
    print("STATUS=pass (CSV status matches executed receipts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
