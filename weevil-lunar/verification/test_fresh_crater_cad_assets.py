#!/usr/bin/env python3
"""Check admitted fresh-crater CAD candidate assets."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml


CFG_PATH = Path("cad/assets/fresh_crater_candidates.yaml")


def main() -> None:
    assert CFG_PATH.exists(), f"missing config: {CFG_PATH}"
    data = yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))
    assets = data.get("assets", [])

    rows = []
    for asset in assets:
        normalized = asset.get("normalized_step_path")
        synthetic = bool(asset.get("synthetic", False))
        exists = True if synthetic and not normalized else Path(str(normalized)).exists()
        role_ok = str(asset.get("intended_role", "")) in {"leg_module", "actuator", "assembly_snapshot", "analysis_only"}
        evidence_ok = str(asset.get("evidence_tier", "")) == "geometry_only"
        synthetic_contract_ok = (synthetic and normalized is None) or ((not synthetic) and normalized is not None)
        passed = exists and role_ok and evidence_ok and synthetic_contract_ok
        rows.append(
            {
                "asset_id": asset.get("asset_id"),
                "intended_role": asset.get("intended_role"),
                "synthetic": synthetic,
                "exists": exists,
                "role_ok": role_ok,
                "evidence_ok": evidence_ok,
                "synthetic_contract_ok": synthetic_contract_ok,
                "pass": passed,
            }
        )

    report_dir = Path("verification/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "fresh_crater_cad_assets.csv"
    md_path = report_dir / "fresh_crater_cad_assets.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    passed = sum(1 for r in rows if r["pass"])
    status = "pass" if passed == total else "fail"

    lines = [
        "# Fresh Crater CAD Asset Check",
        "",
        f"- total: {total}",
        f"- passed: {passed}",
        f"- status: **{status.upper()}**",
        "",
        "| asset_id | exists | role_ok | evidence_ok | synthetic_contract_ok | pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['asset_id']} | {int(bool(r['exists']))} | {int(bool(r['role_ok']))} | {int(bool(r['evidence_ok']))} | {int(bool(r['synthetic_contract_ok']))} | {int(bool(r['pass']))} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")
    print(f"STATUS={status}")


if __name__ == "__main__":
    main()
