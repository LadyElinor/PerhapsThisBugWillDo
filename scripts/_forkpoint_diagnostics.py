#!/usr/bin/env python3
import argparse
import os
import numpy as np
import pandas as pd

POLICIES = ["greedy", "anneal", "tempered"]


def require_cols(df: pd.DataFrame, cols: list[str], name: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")


def concentration(df: pd.DataFrame, mode_col: str):
    rows = []
    for pol, g in df.groupby("policy"):
        counts = g.groupby(mode_col).size().sort_values(ascending=False)
        if counts.sum() <= 0:
            rows.append({"policy": pol, "top1": np.nan, "top3": np.nan, "n": 0, "unique_modes": 0})
            continue
        p = counts / counts.sum()
        rows.append(
            {
                "policy": pol,
                "top1": float(p.iloc[0]),
                "top3": float(p.iloc[:3].sum()),
                "n": int(counts.sum()),
                "unique_modes": int((counts > 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def concentration_weighted(df: pd.DataFrame, mode_col: str, w_col: str = "accepted_weight"):
    rows = []
    for pol, g in df.groupby("policy"):
        w = g.groupby(mode_col)[w_col].sum().sort_values(ascending=False)
        tot = float(w.sum())
        if tot <= 0:
            rows.append({"policy": pol, "top1_w": np.nan, "top3_w": np.nan, "w_total": 0.0, "unique_modes_w": 0})
            continue
        p = w / tot
        rows.append(
            {
                "policy": pol,
                "top1_w": float(p.iloc[0]),
                "top3_w": float(p.iloc[:3].sum()),
                "w_total": tot,
                "unique_modes_w": int((w > 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def classify_fork(late_ratio: float, flips: int, acc: pd.DataFrame, access: pd.DataFrame):
    if (late_ratio < 0.05) and (flips == 0):
        return "early_saturation"
    acc_rng = float(acc["top1"].max() - acc["top1"].min()) if not acc.empty else np.nan
    access_rng = float(access["top1"].max() - access["top1"].min()) if not access.empty else np.nan
    if np.isfinite(acc_rng) and np.isfinite(access_rng):
        if acc_rng >= 0.05 and access_rng < 0.03:
            return "acceptance_steering"
        if acc_rng < 0.03 and access_rng < 0.03:
            return "connectivity_invariant_barrier_limited"
    return "mixed_or_uncertain"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", required=True)
    ap.add_argument("--exits", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", default="")
    ap.add_argument("--mode-col", default="", help="mode column to use; default mode_key if present else mode_id")
    args = ap.parse_args()

    if not os.path.exists(args.pilot):
        raise FileNotFoundError(f"pilot file not found: {args.pilot}")
    if not os.path.exists(args.exits):
        raise FileNotFoundError(f"exits file not found: {args.exits}")

    pilot = pd.read_csv(args.pilot)
    exits = pd.read_csv(args.exits)

    require_cols(pilot, ["seed", "dynamics_policy", "budget", "reached_target", "escape_time"], "pilot")
    require_cols(exits, ["seed", "policy", "accessible", "accepted"], "exits")

    mode_col = args.mode_col or ("mode_key" if "mode_key" in exits.columns else "mode_id")
    if mode_col not in exits.columns:
        raise ValueError(f"mode column missing: {mode_col}")

    # Guardrails
    for pol in POLICIES:
        if pol not in set(exits["policy"].astype(str).unique()):
            raise ValueError(f"missing policy in exits: {pol}")
    if exits[mode_col].nunique() < 2:
        raise ValueError("degenerate exits: <2 unique modes")

    # First-hit aggregation from pilot
    p = pilot.copy()
    p["budget"] = pd.to_numeric(p["budget"], errors="coerce")
    p["reached_target"] = pd.to_numeric(p["reached_target"], errors="coerce").fillna(0)
    p["escape_time"] = pd.to_numeric(p["escape_time"], errors="coerce")

    rates = []
    for pol, g in p.groupby("dynamics_policy"):
        g2 = g.pivot_table(index=["seed", "dynamics_policy"], columns="budget", values="reached_target", aggfunc="max")
        r1000 = float(g2[1000].mean()) if 1000 in g2.columns else np.nan
        r10000 = float(g2[10000].mean()) if 10000 in g2.columns else np.nan
        fl = int(((g2.get(1000, 0) == 0) & (g2.get(10000, 0) == 1)).sum()) if (1000 in g2.columns and 10000 in g2.columns) else 0
        rates.append({"policy": pol, "rate_1000": r1000, "rate_10000": r10000, "flips_1000_10000": fl})

    # late ratio from first-hit rows
    rows = []
    for _, g in p.sort_values("budget").groupby(["seed", "dynamics_policy"]):
        hit = g[g["reached_target"] == 1]
        if len(hit):
            r = hit.sort_values(["escape_time", "budget"]).iloc[0]
            rows.append(float(r["escape_time"]))
    fh = np.array(rows, dtype=float)
    total_hits = int(np.isfinite(fh).sum())
    late = int(np.sum(fh > 1000))
    late_ratio = float(late / max(total_hits, 1))
    flips_total = int(sum(r["flips_1000_10000"] for r in rates))

    acc = concentration(exits[exits["accepted"] == 1], mode_col)
    access = concentration(exits[exits["accessible"] == 1], mode_col)
    w = concentration_weighted(exits, mode_col, w_col="accepted_weight") if "accepted_weight" in exits.columns else pd.DataFrame()

    verdict = classify_fork(late_ratio, flips_total, acc, access)

    out_dir = os.path.dirname(args.out_md)
    os.makedirs(out_dir, exist_ok=True)

    lines = []
    lines.append("# Fork-Point Diagnostics")
    lines.append("")
    lines.append(f"- pilot: `{args.pilot}`")
    lines.append(f"- exits: `{args.exits}`")
    lines.append(f"- mode_col: `{mode_col}`")
    lines.append("")
    lines.append("## Core diagnostics")
    lines.append(f"- late_ratio (escape_time>1000 among hits): **{late_ratio:.4f}** ({late}/{total_hits})")
    lines.append(f"- flips_1000_to_10000: **{flips_total}**")
    lines.append(f"- fork_verdict: **{verdict}**")
    lines.append("")

    lines.append("## Reachability lift by policy")
    for r in sorted(rates, key=lambda x: x["policy"]):
        lines.append(f"- {r['policy']}: {r['rate_1000']:.3f} -> {r['rate_10000']:.3f} (flips={r['flips_1000_10000']})")
    lines.append("")

    lines.append("## Concentration (accepted-only)")
    for _, r in acc.sort_values("policy").iterrows():
        lines.append(f"- {r['policy']}: top1={r['top1']:.3f}, top3={r['top3']:.3f}, n={int(r['n'])}, unique_modes={int(r['unique_modes'])}")
    lines.append("")

    lines.append("## Concentration (accessible-only)")
    for _, r in access.sort_values("policy").iterrows():
        lines.append(f"- {r['policy']}: top1={r['top1']:.3f}, top3={r['top3']:.3f}, n={int(r['n'])}, unique_modes={int(r['unique_modes'])}")
    lines.append("")

    if not w.empty:
        lines.append("## Concentration (weighted by accepted_weight)")
        for _, r in w.sort_values("policy").iterrows():
            lines.append(f"- {r['policy']}: top1_w={r['top1_w']:.3f}, top3_w={r['top3_w']:.3f}, w_total={r['w_total']:.3f}, unique_modes={int(r['unique_modes_w'])}")
        lines.append("")

    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    out_csv = args.out_csv or os.path.join(out_dir, "forkpoint_summary.csv")
    merged = acc.merge(access, on="policy", suffixes=("_accepted", "_accessible"), how="outer")
    if not w.empty:
        merged = merged.merge(w, on="policy", how="left")
    merged["late_ratio"] = late_ratio
    merged["flips_1000_10000_total"] = flips_total
    merged["fork_verdict"] = verdict
    merged.to_csv(out_csv, index=False)

    print(f"Wrote fork diagnostics: {args.out_md}")
    print(f"Wrote fork summary csv: {out_csv}")


if __name__ == "__main__":
    main()
