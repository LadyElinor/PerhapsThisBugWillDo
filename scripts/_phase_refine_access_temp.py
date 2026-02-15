import itertools
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("results/reachability_refine")
ROOT.mkdir(parents=True, exist_ok=True)
DATE = "2026-02-15-refine"
SEEDS = 60
TPROBE = 500
EPS = 1e-12


def sigmoid(z):
    z = np.clip(z, -50, 50)
    return 1.0 / (1.0 + np.exp(-z))


def fit_logit_l2(X, y, l2=1e-3, max_iter=100, tol=1e-7):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    b = np.zeros(X.shape[1])
    for _ in range(max_iter):
        p = sigmoid(X @ b)
        W = p * (1 - p)
        g = X.T @ (p - y)
        reg = np.zeros_like(b)
        reg[1:] = l2 * b[1:]
        g += reg
        H = (X.T * W) @ X
        for i in range(1, X.shape[1]):
            H[i, i] += l2
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            step = np.linalg.pinv(H) @ g
        b_new = b - step
        if np.max(np.abs(b_new - b)) < tol:
            b = b_new
            break
        b = b_new
    return b


def auc_binary(y, score):
    y = np.asarray(y)
    s = np.asarray(score, float)
    m = np.isfinite(s)
    y = y[m]
    s = s[m]
    if len(s) == 0 or len(np.unique(y)) < 2:
        return np.nan
    r = pd.Series(s).rank(method="average").to_numpy()
    n1 = np.sum(y == 1)
    n0 = np.sum(y == 0)
    R1 = np.sum(r[y == 1])
    U = R1 - n1 * (n1 + 1) / 2
    return float(U / (n1 * n0))


def wquantile(x, w, q):
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x = x[m]
    w = w[m]
    if len(x) == 0:
        return np.nan
    s = np.argsort(x)
    x = x[s]
    w = w[s]
    cw = np.cumsum(w)
    t = q * cw[-1]
    i = np.searchsorted(cw, t, side="left")
    i = min(max(i, 0), len(x) - 1)
    return float(x[i])


def run_cell(cell_dir: Path, access_mult: float, low_t: int):
    anneal_t, tempered_t = (0.6, 0.8) if low_t else (0.9, 1.2)
    cmd = [
        "python", "scripts/pilot_runner.py",
        "--chosen", "results/reachability/preflight/chosen_settings.json",
        "--out-root", str(cell_dir).replace("\\", "/"),
        "--date", DATE,
        "--seeds", str(SEEDS),
        "--physics-mode-signature", "mode_energy",
        "--physics-energy-bins", "4",
        "--physics-probe-grid", str(TPROBE),
        "--physics-barrier-mult", "1.0",
        "--physics-access-mult", str(access_mult),
        "--anneal-temp", str(anneal_t),
        "--tempered-temp", str(tempered_t),
    ]
    subprocess.run(cmd, check=True)

    pilot = pd.read_csv(cell_dir / "physics" / f"pilot_{DATE}.csv")
    exits = pd.read_csv(cell_dir / "physics" / f"exits_{DATE}.csv")

    # first-hit times
    p = pilot.copy()
    for c in ["budget", "reached_target", "escape_time"]:
        p[c] = pd.to_numeric(p[c], errors="coerce")
    bmax = int(np.nanmax(p["budget"].to_numpy()))
    fh = []
    for (s, pol), g in p.sort_values("budget").groupby(["seed", "dynamics_policy"]):
        hit = g[g["reached_target"] == 1]
        tau = np.nan
        if len(hit):
            r = hit.sort_values(["escape_time", "budget"]).iloc[0]
            tau = float(r["escape_time"])
        fh.append({"seed": s, "policy": pol, "tau": tau})
    fh = pd.DataFrame(fh)

    rows = []
    tmap = {"anneal": anneal_t, "tempered": tempered_t, "greedy": 0.0}
    ex_t = exits[exits["probe_time"] == TPROBE]
    for (s, pol), g in ex_t.groupby(["seed", "policy"]):
        if pol not in ["anneal", "tempered"]:
            continue
        a = g[g["accessible"] == 1].copy()
        M_acc_w = float(a["accepted_weight"].sum()) if len(a) else 0.0
        dE = wquantile(a["deltaE_plus"].to_numpy(), a["accepted_weight"].to_numpy(), 0.9) if len(a) else np.nan
        T = tmap[pol]
        dEoT = (dE / T) if (np.isfinite(dE) and T > 0) else np.nan
        rows.append({"seed": s, "policy": pol, "M_acc_w": M_acc_w, "dE_over_T": dEoT})
    f = pd.DataFrame(rows).merge(fh, on=["seed", "policy"], how="left")
    f = f[(f["tau"].isna()) | (f["tau"] > TPROBE)].copy()
    f["escape_later"] = ((~f["tau"].isna()) & (f["tau"] <= bmax) & (f["tau"] > TPROBE)).astype(int)
    f["x_macc"] = np.log(f["M_acc_w"] + EPS)

    y = f["escape_later"].to_numpy(int)
    prevalence = float(y.mean()) if len(y) else np.nan
    auc_m = auc_binary(y, f["x_macc"].to_numpy(float))

    fd = f[np.isfinite(f["dE_over_T"])].copy()
    yd = fd["escape_later"].to_numpy(int)
    auc_d = auc_binary(yd, fd["dE_over_T"].to_numpy(float)) if len(fd) else np.nan

    auc_c = np.nan
    if len(fd) >= 20 and len(np.unique(yd)) >= 2:
        X = np.column_stack([np.ones(len(fd)), fd["x_macc"].to_numpy(float), fd["dE_over_T"].to_numpy(float)])
        b = fit_logit_l2(X, yd, l2=1e-3)
        ph = sigmoid(X @ b)
        auc_c = auc_binary(yd, ph)

    dauc = (auc_c - auc_m) if (np.isfinite(auc_c) and np.isfinite(auc_m)) else np.nan
    if np.isfinite(dauc):
        if dauc < 0.02:
            cls = "ONSET-DOMINATED"
        elif dauc < 0.05:
            cls = "TRANSITIONAL"
        else:
            cls = "BARRIER-EMERGENT"
    else:
        cls = "UNDEFINED"

    dEvals = fd["dE_over_T"].to_numpy(float)
    dE_p10 = float(np.nanquantile(dEvals, 0.10)) if len(dEvals) else np.nan
    dE_p90 = float(np.nanquantile(dEvals, 0.90)) if len(dEvals) else np.nan

    macc = f["M_acc_w"].to_numpy(float)
    macc_med = float(np.nanmedian(macc)) if len(macc) else np.nan
    macc_p10 = float(np.nanquantile(macc, 0.10)) if len(macc) else np.nan
    macc_p90 = float(np.nanquantile(macc, 0.90)) if len(macc) else np.nan

    return {
        "N_at_risk": int(len(f)),
        "prevalence": prevalence,
        "AUC_M_acc_w": auc_m,
        "AUC_dE_over_T": auc_d,
        "AUC_combined": auc_c,
        "dAUC_combined_minus_Macc": dauc,
        "M_acc_w_median": macc_med,
        "M_acc_w_p10": macc_p10,
        "M_acc_w_p90": macc_p90,
        "dE_over_T_p10": dE_p10,
        "dE_over_T_p90": dE_p90,
        "cell_class": cls,
    }


def main():
    cells = []
    cid = 0
    for access_mult, low_t in itertools.product([0.60, 0.65, 0.70], [0, 1]):
        cid += 1
        cell_id = f"cell_{cid:02d}"
        out = ROOT / cell_id
        out.mkdir(parents=True, exist_ok=True)
        print(f"Running {cell_id}: access_mult={access_mult}, low_t={low_t}")
        m = run_cell(out, access_mult, low_t)
        cells.append({
            "cell_id": cell_id,
            "barrier_mult": 1.0,
            "access_mult": access_mult,
            "temp_level": "low" if low_t else "baseline",
            **m,
        })

    df = pd.DataFrame(cells).sort_values("dAUC_combined_minus_Macc", ascending=False)
    out_csv = ROOT / "refine_summary_t500.csv"
    df.to_csv(out_csv, index=False)

    md = ["# Local Refinement Sweep (t=500)", "", "```", df.to_string(index=False), "```", ""]
    md.append("Legend: ONSET-DOMINATED (<0.02), TRANSITIONAL (0.02-0.05), BARRIER-EMERGENT (>=0.05)")
    out_md = ROOT / "REFINE_READOUT.md"
    out_md.write_text("\n".join(md), encoding="utf-8")

    print(df.to_string(index=False))
    print(f"WROTE {out_csv}")
    print(f"WROTE {out_md}")


if __name__ == "__main__":
    main()
