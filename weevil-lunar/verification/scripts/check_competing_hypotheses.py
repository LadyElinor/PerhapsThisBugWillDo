#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

INPUT = Path("verification/templates/competing_hypotheses_matrix.csv")
OUT_DIR = Path("verification/reports")

HIGH_RISK_PREFIXES = ("RISK-",)
MIN_HYPOTHESES_PER_RISK = 2


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not INPUT.exists():
        raise FileNotFoundError(f"missing {INPUT}")

    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    by_risk: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        rid = (r.get("risk_id") or "").strip()
        by_risk[rid].append(r)

    out_rows = []
    overall_pass = True
    for rid, rs in sorted(by_risk.items()):
        hyp_ids = { (r.get("hypothesis_id") or "").strip() for r in rs if (r.get("hypothesis_id") or "").strip() }
        has_disconfirm = all((r.get("disconfirming_test") or "").strip() for r in rs)
        has_pred_sig = all((r.get("predicted_signature") or "").strip() for r in rs)
        count_ok = len(hyp_ids) >= MIN_HYPOTHESES_PER_RISK
        # only enforce count gate for risk-like IDs
        enforce = rid.startswith(HIGH_RISK_PREFIXES)
        row_pass = has_disconfirm and has_pred_sig and (count_ok if enforce else True)
        overall_pass = overall_pass and row_pass
        out_rows.append(
            {
                "risk_id": rid,
                "hypothesis_count": len(hyp_ids),
                "has_predicted_signatures": has_pred_sig,
                "has_disconfirming_tests": has_disconfirm,
                "enforced": enforce,
                "pass": row_pass,
            }
        )

    out_csv = OUT_DIR / "competing_hypotheses_check.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "risk_id",
                "hypothesis_count",
                "has_predicted_signatures",
                "has_disconfirming_tests",
                "enforced",
                "pass",
            ],
        )
        w.writeheader()
        w.writerows(out_rows)

    out_md = OUT_DIR / "competing_hypotheses_check.md"
    lines = [
        "# Competing Hypotheses Check",
        "",
        f"- risks evaluated: {len(out_rows)}",
        f"- minimum hypotheses per enforced risk: {MIN_HYPOTHESES_PER_RISK}",
        f"- status: **{'PASS' if overall_pass else 'FAIL'}**",
        "",
        "| risk | count | predicted signatures | disconfirm tests | enforced | pass |",
        "|---|---:|---|---|---|---|",
    ]
    for r in out_rows:
        lines.append(
            f"| {r['risk_id']} | {r['hypothesis_count']} | {r['has_predicted_signatures']} | {r['has_disconfirming_tests']} | {r['enforced']} | {r['pass']} |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print(f"STATUS={'pass' if overall_pass else 'fail'}")


if __name__ == "__main__":
    main()
