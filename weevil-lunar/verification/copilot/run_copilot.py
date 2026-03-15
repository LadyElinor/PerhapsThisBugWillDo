#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

REQ_RE = re.compile(r"\bREQ-[A-Z]+-\d{3}\b")
SEV_WEIGHT = {"high": 5, "medium": 2, "low": 1}


@dataclass
class Finding:
    finding_type: str
    severity: str
    requirement_id: str
    detail: str
    recommendation: str


def load_aliases(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out[row["legacy_requirement_id"].strip()] = row["canonical_requirement_id"].strip()
    return out


def extract_requirements_from_docs(root: Path) -> set[str]:
    reqs: set[str] = set()
    for sp in [root / "specs", root / "docs"]:
        if not sp.exists():
            continue
        for fp in sp.rglob("*.md"):
            txt = fp.read_text(encoding="utf-8", errors="ignore")
            reqs.update(REQ_RE.findall(txt))
    return reqs


def normalize(req: str, aliases: dict[str, str]) -> str:
    return aliases.get(req, req)


def _load_suppressions(path: Path) -> dict:
    if not path.exists():
        return {
            "suppress_missing_report_prefixes": [],
            "suppress_status_contains": [],
            "suppress_stale_report_prefixes": [],
        }
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "suppress_missing_report_prefixes": data.get("suppress_missing_report_prefixes", []) or [],
        "suppress_status_contains": data.get("suppress_status_contains", []) or [],
        "suppress_stale_report_prefixes": data.get("suppress_stale_report_prefixes", []) or [],
    }


def _prefixed(path_str: str, prefixes: list[str]) -> bool:
    return any(path_str.startswith(p) for p in prefixes)


def _finding_key(fd: Finding) -> tuple[str, str, str]:
    return (fd.finding_type, fd.requirement_id, fd.detail)


def _load_previous_finding_keys(path: Path) -> set[tuple[str, str, str]]:
    if not path.exists():
        return set()
    out: set[tuple[str, str, str]] = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out.add(
                (
                    (row.get("finding_type") or "").strip(),
                    (row.get("requirement_id") or "").strip(),
                    (row.get("detail") or "").strip(),
                )
            )
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", default=".")
    p.add_argument("--stale-days", type=int, default=14)
    p.add_argument("--max-weighted-score", type=int, default=10)
    p.add_argument("--suppressions", default="verification/copilot/suppressions.yaml")
    args = p.parse_args()

    root = Path(args.repo_root)
    ver = root / "verification"
    reports = ver / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    trace_path = ver / "requirements_traceability.csv"
    alias_path = ver / "requirement_aliases.csv"
    suppressions = _load_suppressions(root / args.suppressions)

    aliases = load_aliases(alias_path)
    spec_reqs_raw = extract_requirements_from_docs(root)
    spec_reqs = {normalize(r, aliases) for r in spec_reqs_raw}

    trace_rows = []
    with trace_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            row = {k: (v or "").strip() for k, v in row.items()}
            row["requirement_id_norm"] = normalize(row["requirement_id"], aliases)
            trace_rows.append(row)

    trace_reqs = {r["requirement_id_norm"] for r in trace_rows}
    previous_keys = _load_previous_finding_keys(reports / "copilot_findings.csv")
    findings: list[Finding] = []

    for req in sorted(spec_reqs - trace_reqs):
        findings.append(
            Finding(
                "missing_mapping",
                "high",
                req,
                "Requirement present in specs/docs but missing from requirements_traceability.csv",
                "Add traceability row mapping this requirement to test + report evidence.",
            )
        )

    for req in sorted(trace_reqs - spec_reqs):
        findings.append(
            Finding(
                "traceability_orphan",
                "medium",
                req,
                "Requirement appears in traceability but not found in current specs/docs scan.",
                "Confirm requirement still active or add alias/placement in specs.",
            )
        )

    now = datetime.now(timezone.utc)

    for row in trace_rows:
        req = row["requirement_id_norm"]
        result_file = row.get("result_file", "")
        status_l = row.get("status", "").lower()

        if any(k in status_l for k in ["fail", "partial", "baseline-fail"]):
            if not any(s in status_l for s in suppressions["suppress_status_contains"]):
                findings.append(
                    Finding(
                        "weak_status",
                        "medium",
                        req,
                        f"Traceability status is '{row.get('status', '')}'.",
                        "Promote to pass with stronger evidence or mark as open risk with mitigation plan.",
                    )
                )

        if result_file:
            rp = root / result_file
            if not rp.exists():
                if not _prefixed(result_file, suppressions["suppress_missing_report_prefixes"]):
                    findings.append(
                        Finding(
                            "missing_report",
                            "high",
                            req,
                            f"Result file not found: {result_file}",
                            "Regenerate report or fix path in traceability row.",
                        )
                    )
            else:
                age_days = (now - datetime.fromtimestamp(rp.stat().st_mtime, tz=timezone.utc)).total_seconds() / 86400.0
                if age_days > args.stale_days and not _prefixed(result_file, suppressions["suppress_stale_report_prefixes"]):
                    findings.append(
                        Finding(
                            "stale_report",
                            "low",
                            req,
                            f"Report is stale ({age_days:.1f} days old): {result_file}",
                            "Re-run verification harness to refresh evidence.",
                        )
                    )

    out_csv = reports / "copilot_findings.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["finding_type", "severity", "requirement_id", "detail", "recommendation"])
        w.writeheader()
        for fd in findings:
            w.writerow(fd.__dict__)

    by_sev = {"high": 0, "medium": 0, "low": 0}
    by_type: dict[str, int] = {}
    weighted_score = 0
    for fd in findings:
        by_sev[fd.severity] += 1
        by_type[fd.finding_type] = by_type.get(fd.finding_type, 0) + 1
        weighted_score += SEV_WEIGHT.get(fd.severity, 1)

    new_high_findings = [
        fd for fd in findings if fd.severity == "high" and _finding_key(fd) not in previous_keys
    ]

    status_pass = weighted_score <= args.max_weighted_score

    status_csv = reports / "copilot_status.csv"
    with status_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp_utc",
                "total_findings",
                "high",
                "medium",
                "low",
                "weighted_score",
                "max_weighted_score",
                "pass",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "timestamp_utc": now.isoformat(),
                "total_findings": len(findings),
                "high": by_sev["high"],
                "medium": by_sev["medium"],
                "low": by_sev["low"],
                "weighted_score": weighted_score,
                "max_weighted_score": args.max_weighted_score,
                "pass": status_pass,
            }
        )

    summary_json = reports / "copilot_summary.json"
    summary_json.write_text(
        json.dumps(
            {
                "timestamp": now.isoformat(),
                "counts": {"total": len(findings), **by_sev},
                "by_type": by_type,
                "weighted_score": weighted_score,
                "max_weighted_score": args.max_weighted_score,
                "pass": status_pass,
                "new_high_count": len(new_high_findings),
                "new_high_examples": [
                    {
                        "finding_type": fd.finding_type,
                        "requirement_id": fd.requirement_id,
                        "detail": fd.detail,
                    }
                    for fd in new_high_findings[:20]
                ],
                "suppressions": suppressions,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    out_md = reports / "copilot_findings.md"
    lines = [
        "# Verification Copilot Findings",
        "",
        "Automated consistency scan across specs/docs requirements, traceability, and report artifacts.",
        "",
        f"- suppressions file: {args.suppressions}",
        f"- weighted score: {weighted_score} / {args.max_weighted_score}",
        f"- copilot status: **{'PASS' if status_pass else 'FAIL'}**",
        "",
        f"- total findings: {len(findings)}",
        f"- high: {by_sev['high']}",
        f"- medium: {by_sev['medium']}",
        f"- low: {by_sev['low']}",
        f"- new high findings since last run: {len(new_high_findings)}",
        f"- stale threshold (days): {args.stale_days}",
        "",
        "## New high findings since last run",
        "",
    ]
    if new_high_findings:
        lines.extend([
            "| type | requirement | detail |",
            "|---|---|---|",
        ])
        for fd in new_high_findings[:50]:
            lines.append(f"| {fd.finding_type} | {fd.requirement_id or '-'} | {fd.detail.replace('|', '/')} |")
        if len(new_high_findings) > 50:
            lines.append(f"| ... | ... | truncated {len(new_high_findings)-50} additional new high findings |")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## All findings",
        "",
        "| type | severity | requirement | detail |",
        "|---|---|---|---|",
    ])
    for fd in findings[:400]:
        lines.append(f"| {fd.finding_type} | {fd.severity} | {fd.requirement_id or '-'} | {fd.detail.replace('|', '/')} |")
    if len(findings) > 400:
        lines.append(f"| ... | ... | ... | truncated {len(findings)-400} additional findings |")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {status_csv}")
    print(f"Wrote {summary_json}")
    print(f"Wrote {out_md}")
    print(f"FINDINGS={len(findings)}")
    print(f"WEIGHTED_SCORE={weighted_score}")


if __name__ == "__main__":
    main()
