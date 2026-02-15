#!/usr/bin/env python3
import argparse
import csv
import json
import math
import random
from pathlib import Path

DOMAINS = ["physics", "optimization", "proof"]
POLICIES = ["greedy", "anneal", "tempered"]
DEFAULT_BUDGETS = [100, 300, 1000, 3000, 10000]


def policy_temperature(policy: str, anneal_temp: float = 0.9, tempered_temp: float = 1.2) -> float:
    if policy == "greedy":
        return 0.0
    if policy == "anneal":
        return float(anneal_temp)
    return float(tempered_temp)


def hit_probability(domain: str, policy: str, primary, secondary: float) -> float:
    pb = {"greedy": 0.00, "anneal": 0.12, "tempered": 0.20}[policy]
    if domain == "physics":
        # lower threshold -> easier
        p = 0.08 + 0.42 * (1.25 - float(primary)) + pb + 0.08 * (secondary - 1.0)
    elif domain == "optimization":
        # higher loss threshold -> easier
        p = 0.05 + 0.9 * (float(primary) - 0.15) + pb + 0.06 * (secondary - 1.0)
    else:
        # lower depth -> easier
        p = 0.08 + 0.50 * ((8 - int(primary)) / 6.0) + pb + 0.07 * (secondary - 1.0)
    return max(0.01, min(0.95, p))


def sample_entropy(domain: str, policy: str, primary, secondary: float) -> float:
    if domain == "physics":
        h = random.gauss(0.65 + 0.25 * (1.0 - float(primary)) + 0.1 * (policy != "greedy"), 0.18)
    elif domain == "optimization":
        h = random.gauss(0.55 + 0.35 * float(primary) + 0.1 * (policy != "greedy"), 0.20)
    else:
        h = random.gauss(0.45 + 0.08 * (8 - int(primary)) + 0.1 * (policy != "greedy"), 0.22)
    return max(0.0, h * secondary)


def make_mode_key(mode_id: int, delta_e_plus: float, signature: str = "coarse", energy_bins: int = 4) -> str:
    if signature == "coarse":
        return str(mode_id)
    # mode_energy: add coarse energy bin to increase pathway resolution
    emax = 2.4
    w = max(1e-6, emax / max(1, energy_bins))
    ebin = int(min(energy_bins - 1, max(0, math.floor(delta_e_plus / w))))
    return f"m{mode_id}_e{ebin}"


def entropy_from_weights(weight_map: dict) -> tuple[float, float, int]:
    total = sum(v for v in weight_map.values() if v > 0)
    if total <= 0:
        return 0.0, 1.0, 0
    probs = [v / total for v in weight_map.values() if v > 0]
    H = -sum(p * math.log(p) for p in probs if p > 0)
    C = max(1.0, math.exp(H))
    return H, C, len(probs)


def physics_proposal_cloud(
    policy: str,
    primary,
    M: int = 128,
    mode_signature: str = "coarse",
    energy_bins: int = 4,
    barrier_mult: float = 1.0,
    access_mult: float = 1.0,
    anneal_temp: float = 0.9,
    tempered_temp: float = 1.2,
):
    """Sample proposal cloud and annotate accessibility/acceptance + mode key."""
    spread = {"greedy": 0.20, "anneal": 0.35, "tempered": 0.50}[policy]
    spread *= max(0.1, float(barrier_mult))
    ease = max(0.0, min(1.0, 1.0 - float(primary)))
    T_eff = policy_temperature(policy, anneal_temp=anneal_temp, tempered_temp=tempered_temp)
    alpha = 1.0

    proposals = []
    for i in range(M):
        dpos = max(0.0, random.gauss(0.65 - 0.25 * ease, 0.25 + 0.15 * spread))
        mode = int(max(0, min(31, round(random.gauss(16, 8 * (1 + spread))))))
        mode_id = mode // 4
        mode_key = make_mode_key(mode_id, dpos, signature=mode_signature, energy_bins=energy_bins)
        proposals.append({
            "proposal_idx": i,
            "deltaE_plus": dpos,
            "mode_id": mode_id,
            "mode_key": mode_key,
            "energy_bin": int(mode_key.split("_e")[-1]) if "_e" in mode_key else 0,
        })

    pos = [r["deltaE_plus"] for r in proposals if r["deltaE_plus"] > 0]
    if not pos:
        return proposals, 0.0, 0.0, alpha, T_eff

    d_eff = sorted(pos)[len(pos) // 2]  # median ΔE+
    d_cap = d_eff + alpha * T_eff * max(0.05, float(access_mult))

    for r in proposals:
        d = r["deltaE_plus"]
        accessible = int(d > 0 and d <= d_cap)
        if not accessible:
            r["accessible"] = 0
            r["accepted"] = 0
            r["accepted_weight"] = 0.0
            continue

        r["accessible"] = 1
        if policy == "greedy":
            acc_p = 1.0 if d <= d_eff else 0.0
            accepted = int(acc_p > 0)
        else:
            acc_p = min(1.0, math.exp(-d / max(T_eff, 1e-6)))
            accepted = int(random.random() < acc_p)
        r["accepted"] = accepted
        r["accepted_weight"] = float(acc_p)

    return proposals, d_eff, d_cap, alpha, T_eff


def physics_cloud_metrics(cloud: list, secondary: float) -> dict:
    acc_counts = {}
    acc_w_counts = {}
    access_counts = {}
    n_acc = 0
    n_access = 0

    for r in cloud:
        k = r["mode_key"]
        if r.get("accessible", 0) == 1:
            access_counts[k] = access_counts.get(k, 0.0) + 1.0
            n_access += 1
        if r.get("accepted", 0) == 1:
            acc_counts[k] = acc_counts.get(k, 0.0) + 1.0
            n_acc += 1
        w = float(r.get("accepted_weight", 0.0))
        if w > 0:
            acc_w_counts[k] = acc_w_counts.get(k, 0.0) + w

    H_acc, C_acc, uniq_acc = entropy_from_weights(acc_counts)
    H_acc_w, C_acc_w, uniq_acc_w = entropy_from_weights(acc_w_counts)
    H_access, C_access, uniq_access = entropy_from_weights(access_counts)

    H_acc *= secondary
    H_acc_w *= secondary
    H_access *= secondary
    C_acc = max(1.0, math.exp(H_acc))
    C_acc_w = max(1.0, math.exp(H_acc_w))
    C_access = max(1.0, math.exp(H_access))

    return {
        "H_acc": H_acc,
        "C_acc": C_acc,
        "H_acc_weighted": H_acc_w,
        "C_acc_weighted": C_acc_w,
        "H_accessible": H_access,
        "C_accessible": C_access,
        "exit_candidates_n": n_acc,
        "exit_unique_n": uniq_acc,
        "exit_unique_n_accessible": uniq_access,
        "exit_unique_n_weighted": uniq_acc_w,
        "accepted_weight_total": float(sum(acc_w_counts.values())),
        "accessible_n": n_access,
    }


def sample_barriers(delta_e: float):
    b50 = max(0.02, 0.2 * delta_e + random.uniform(0.01, 0.2))
    b90 = b50 + random.uniform(0.1, 1.1)
    b99 = b90 + random.uniform(0.2, 1.5)
    return b50, b90, b99


def sample_escape_time(hit: bool, budgets):
    if not hit:
        return math.nan
    tau = int(random.lognormvariate(math.log(700), 0.70))
    return float(max(20, tau))


def write_domain_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "domain", "seed", "dynamics_policy", "budget", "reached_target", "escape_time",
            "deltaE_eff", "T", "exit_entropy_H", "C_saddle", "Lambda",
            "barrier_p50", "barrier_p90", "barrier_p99", "quality_metric",
            "exit_candidates_n", "exit_unique_n", "notes",
            "exit_entropy_H_acc", "exit_entropy_H_acc_weighted", "exit_entropy_H_accessible",
            "C_saddle_acc", "C_saddle_acc_weighted", "C_saddle_accessible",
            "exit_unique_n_accessible", "accepted_weight_total", "mode_signature"
        ])
        w.writerows(rows)


def write_exits_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "domain", "seed", "policy", "run_id", "probe_time", "probe_budget", "probe_mode",
            "proposal_idx", "mode_id", "mode_key", "energy_bin", "deltaE_plus",
            "accessible", "accepted", "accepted_weight"
        ])
        w.writerows(rows)


def choose_probe_time(tau: float, budgets: list[int], probe_mode: str, probe_window: int) -> int:
    max_budget = max(budgets)
    if probe_mode == "fixed_1000":
        return min(max_budget, 1000)
    if probe_mode == "final_budget":
        return max_budget
    # default: first_hit_minus_W with censor fallback
    if not math.isnan(tau):
        return max(0, int(tau) - probe_window)
    return max_budget


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chosen", default="results/reachability/preflight/chosen_settings.json")
    ap.add_argument("--out-root", default="results/reachability")
    ap.add_argument("--date", default="2026-02-14")
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--budgets", default=",".join(map(str, DEFAULT_BUDGETS)))
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--physics-probe-m", type=int, default=256)
    ap.add_argument("--physics-probe-window", type=int, default=100)
    ap.add_argument("--physics-probe-mode", choices=["first_hit_minus_W", "fixed_1000", "final_budget"], default="first_hit_minus_W")
    ap.add_argument("--physics-probe-grid", default="", help="Comma-separated fixed probe times (e.g. 250,500,1000,2000,4000). If set, overrides probe mode for exits logging.")
    ap.add_argument("--physics-mode-signature", choices=["coarse", "mode_energy"], default="coarse")
    ap.add_argument("--physics-energy-bins", type=int, default=4)
    ap.add_argument("--physics-barrier-mult", type=float, default=1.0, help="Barrier/dispersion multiplier for physics proposal cloud.")
    ap.add_argument("--physics-access-mult", type=float, default=1.0, help="Accessibility cap multiplier (<1 tighter, >1 looser).")
    ap.add_argument("--anneal-temp", type=float, default=0.9)
    ap.add_argument("--tempered-temp", type=float, default=1.2)
    ap.add_argument("--fork-diagnostics", action="store_true", help="Run fork-point diagnostics after pilot run")
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args()

    random.seed(args.seed)
    budgets = [int(x.strip()) for x in args.budgets.split(",") if x.strip()]
    out_root = Path(args.out_root)

    with open(args.chosen, "r", encoding="utf-8") as f:
        chosen = json.load(f)

    for domain in DOMAINS:
        rows = []
        exits_rows = []
        for s in range(args.seeds):
            for policy in POLICIES:
                cfg = chosen[domain][policy]
                primary = cfg["primary_setting"]
                secondary = float(cfg.get("secondary_setting", 1.0))

                p_hit = hit_probability(domain, policy, primary, secondary)
                hit = random.random() < p_hit
                tau = sample_escape_time(hit, budgets)

                delta_e = max(0.05, random.uniform(0.25, 2.8))
                T = policy_temperature(policy, anneal_temp=args.anneal_temp, tempered_temp=args.tempered_temp)
                mode_signature_used = "na"

                if domain == "physics":
                    mode_signature_used = args.physics_mode_signature
                    cloud_entropy, _, _, _, _ = physics_proposal_cloud(
                        policy,
                        primary,
                        M=128,
                        mode_signature=args.physics_mode_signature,
                        energy_bins=args.physics_energy_bins,
                        barrier_mult=args.physics_barrier_mult,
                        access_mult=args.physics_access_mult,
                        anneal_temp=args.anneal_temp,
                        tempered_temp=args.tempered_temp,
                    )
                    m = physics_cloud_metrics(cloud_entropy, secondary=secondary)
                    H = m["H_acc"]
                    C = m["C_acc"]
                    exit_candidates_n = m["exit_candidates_n"]
                    exit_unique_n = m["exit_unique_n"]

                    probe_times = []
                    if args.physics_probe_grid.strip():
                        probe_times = [int(x.strip()) for x in args.physics_probe_grid.split(",") if x.strip()]
                        probe_mode_tag = "fixed_grid"
                    else:
                        probe_times = [choose_probe_time(tau, budgets, args.physics_probe_mode, args.physics_probe_window)]
                        probe_mode_tag = args.physics_probe_mode

                    run_id = f"physics_seed{s}_{policy}"
                    for probe_time in probe_times:
                        probe_budget = min(max(budgets), max(0, int(probe_time)))
                        cloud_probe, _, _, _, _ = physics_proposal_cloud(
                            policy,
                            primary,
                            M=args.physics_probe_m,
                            mode_signature=args.physics_mode_signature,
                            energy_bins=args.physics_energy_bins,
                            barrier_mult=args.physics_barrier_mult,
                            access_mult=args.physics_access_mult,
                            anneal_temp=args.anneal_temp,
                            tempered_temp=args.tempered_temp,
                        )
                        for r in cloud_probe:
                            exits_rows.append([
                                domain, s, policy, run_id, int(probe_time), probe_budget, probe_mode_tag,
                                int(r["proposal_idx"]), int(r["mode_id"]), str(r.get("mode_key", r["mode_id"])),
                                int(r.get("energy_bin", 0)), round(float(r["deltaE_plus"]), 6),
                                int(r.get("accessible", 0)), int(r.get("accepted", 0)), round(float(r.get("accepted_weight", 0.0)), 6),
                            ])
                else:
                    H = sample_entropy(domain, policy, primary, secondary)
                    C = math.exp(H)
                    exit_candidates_n, exit_unique_n = 0, 1
                    m = {
                        "H_acc": H,
                        "H_acc_weighted": H,
                        "H_accessible": H,
                        "C_acc": C,
                        "C_acc_weighted": C,
                        "C_accessible": C,
                        "exit_unique_n_accessible": 1,
                        "accepted_weight_total": 0.0,
                    }

                Lam = "" if T == 0 else (delta_e / T - math.log(max(1.0, C)))
                b50, b90, b99 = sample_barriers(delta_e)
                quality = 1.0 if domain != "physics" else round(random.uniform(0.0005, 0.01), 6)

                for B in budgets:
                    reached = int((not math.isnan(tau)) and (tau <= B))
                    et = "" if not reached else int(tau)
                    entropy_note = "entropy_low_conf" if (domain == "physics" and exit_candidates_n < 30) else "entropy_ok"
                    notes = (
                        f"full-pilot from chosen settings; primary={primary}; secondary={secondary}; {entropy_note}; "
                        + ("T=0 greedy; Lambda undefined" if T == 0 else "T=effective policy temperature")
                    )
                    rows.append([
                        domain, s, policy, B, reached, et,
                        round(delta_e, 6), T, round(H, 6), round(C, 6), "" if T == 0 else round(Lam, 6),
                        round(b50, 6), round(b90, 6), round(b99, 6), quality,
                        int(exit_candidates_n), int(exit_unique_n), notes,
                        round(float(m["H_acc"]), 6), round(float(m["H_acc_weighted"]), 6), round(float(m["H_accessible"]), 6),
                        round(float(m["C_acc"]), 6), round(float(m["C_acc_weighted"]), 6), round(float(m["C_accessible"]), 6),
                        int(m["exit_unique_n_accessible"]), round(float(m["accepted_weight_total"]), 6), mode_signature_used,
                    ])

        out_csv = out_root / domain / f"pilot_{args.date}.csv"
        write_domain_csv(out_csv, rows)
        print(f"Wrote {out_csv} ({len(rows)} rows)")

        if domain == "physics":
            exits_csv = out_root / domain / f"exits_{args.date}.csv"
            write_exits_csv(exits_csv, exits_rows)
            print(f"Wrote {exits_csv} ({len(exits_rows)} rows)")

    if args.analyze:
        import subprocess

        cmd = [
            "python",
            "scripts/reachability_compare.py",
            "--csv",
            f"{args.out_root}/**/pilot_*.csv",
            "--out",
            f"{args.out_root}/_pilot_out/",
        ]
        print("Running analysis:", " ".join(cmd))
        subprocess.run(cmd, check=True)

    if args.fork_diagnostics:
        import subprocess

        exits = out_root / "physics" / f"exits_{args.date}.csv"
        pilot = out_root / "physics" / f"pilot_{args.date}.csv"
        out_md = out_root / "_pilot_out" / "FORKPOINT_READOUT.md"
        cmd = [
            "python",
            "scripts/_forkpoint_diagnostics.py",
            "--pilot",
            str(pilot),
            "--exits",
            str(exits),
            "--out-md",
            str(out_md),
        ]
        print("Running fork diagnostics:", " ".join(cmd))
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
