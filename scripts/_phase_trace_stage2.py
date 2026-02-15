import subprocess
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path('results/reachability_phase_trace')
ROOT.mkdir(parents=True, exist_ok=True)
DATE = '2026-02-15-phase-trace'
SEEDS = 120
TPROBE = 500
EPS = 1e-12

sweeps = [
    ('baseline', 0.90, 1.20, [0.63, 0.64, 0.65, 0.66]),
    ('high', 1.05, 1.40, [0.66, 0.67, 0.68, 0.69]),
]


def sigmoid(z):
    z = np.clip(z, -50, 50)
    return 1 / (1 + np.exp(-z))


def fit_logit_l2(X, y, l2=1e-3, max_iter=140, tol=1e-7):
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
        bn = b - step
        if np.max(np.abs(bn - b)) < tol:
            b = bn
            break
        b = bn
    return b


def auc_binary(y, score):
    y = np.asarray(y)
    s = np.asarray(score, float)
    m = np.isfinite(s)
    y = y[m]
    s = s[m]
    if len(s) == 0 or len(np.unique(y)) < 2:
        return np.nan
    r = pd.Series(s).rank(method='average').to_numpy()
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
    i = np.searchsorted(cw, t, side='left')
    i = min(max(i, 0), len(x) - 1)
    return float(x[i])


rows = []
cell = 0
for tlabel, Ta, Tt, accesses in sweeps:
    for acc in accesses:
        cell += 1
        cdir = ROOT / f'cell_{cell:02d}_{tlabel}_a{acc:.2f}'
        cdir.mkdir(parents=True, exist_ok=True)
        cmd = [
            'python', 'scripts/pilot_runner.py',
            '--chosen', 'results/reachability/preflight/chosen_settings.json',
            '--out-root', str(cdir).replace('\\', '/'),
            '--date', DATE,
            '--seeds', str(SEEDS),
            '--physics-mode-signature', 'mode_energy',
            '--physics-energy-bins', '4',
            '--physics-probe-grid', str(TPROBE),
            '--physics-barrier-mult', '1.0',
            '--physics-access-mult', str(acc),
            '--anneal-temp', str(Ta),
            '--tempered-temp', str(Tt),
        ]
        subprocess.run(cmd, check=True)

        pilot = pd.read_csv(cdir / 'physics' / f'pilot_{DATE}.csv')
        ex = pd.read_csv(cdir / 'physics' / f'exits_{DATE}.csv')

        p = pilot.copy()
        for c in ['budget', 'reached_target', 'escape_time']:
            p[c] = pd.to_numeric(p[c], errors='coerce')
        bmax = int(np.nanmax(p['budget'].to_numpy()))
        fh = []
        for (s, pol), g in p.sort_values('budget').groupby(['seed', 'dynamics_policy']):
            hit = g[g['reached_target'] == 1]
            tau = np.nan
            if len(hit):
                tau = float(hit.sort_values(['escape_time', 'budget']).iloc[0]['escape_time'])
            fh.append({'seed': s, 'policy': pol, 'tau': tau})
        fh = pd.DataFrame(fh)

        feats = []
        for (s, pol), g in ex[ex['probe_time'] == TPROBE].groupby(['seed', 'policy']):
            if pol not in ['anneal', 'tempered']:
                continue
            a = g[g['accessible'] == 1].copy()
            M = float(a['accepted_weight'].sum()) if len(a) else 0.0
            dE = wquantile(a['deltaE_plus'].to_numpy(), a['accepted_weight'].to_numpy(), 0.9) if len(a) else np.nan
            T = Ta if pol == 'anneal' else Tt
            dEoT = (dE / T) if np.isfinite(dE) else np.nan
            feats.append({'seed': s, 'policy': pol, 'x_macc': np.log(M + EPS), 'dE_over_T': dEoT})
        F = pd.DataFrame(feats).merge(fh, on=['seed', 'policy'], how='left')
        F = F[(F['tau'].isna()) | (F['tau'] > TPROBE)].copy()
        F['escape_later'] = ((~F['tau'].isna()) & (F['tau'] <= bmax) & (F['tau'] > TPROBE)).astype(int)

        y = F['escape_later'].to_numpy(int)
        prev = float(y.mean()) if len(y) else np.nan
        auc_m = auc_binary(y, F['x_macc'])
        fd = F[np.isfinite(F['dE_over_T'])].copy()
        yd = fd['escape_later'].to_numpy(int)
        auc_d = auc_binary(yd, fd['dE_over_T']) if len(fd) else np.nan
        auc_c = np.nan
        if len(fd) >= 20 and len(np.unique(yd)) >= 2:
            X = np.column_stack([np.ones(len(fd)), fd['x_macc'].to_numpy(float), fd['dE_over_T'].to_numpy(float)])
            b = fit_logit_l2(X, yd)
            ph = sigmoid(X @ b)
            auc_c = auc_binary(yd, ph)
        dauc = (auc_c - auc_m) if (np.isfinite(auc_c) and np.isfinite(auc_m)) else np.nan

        cls = 'onset-dominated'
        if np.isfinite(dauc):
            if dauc >= 0.05:
                cls = 'barrier-emergent'
            elif dauc >= 0.03:
                cls = 'transitional'

        de = fd['dE_over_T'].to_numpy(float)
        rows.append({
            'cell_id': cdir.name,
            'T_level': tlabel,
            'anneal_T': Ta,
            'tempered_T': Tt,
            'access_mult': acc,
            'N_at_risk': len(F),
            'prevalence': prev,
            'AUC_M_acc_w': auc_m,
            'AUC_dE_over_T': auc_d,
            'AUC_M_plus_dE': auc_c,
            'dAUC': dauc,
            'class': cls,
            'dE_over_T_p10': float(np.nanquantile(de, 0.10)) if len(de) else np.nan,
            'dE_over_T_p90': float(np.nanquantile(de, 0.90)) if len(de) else np.nan,
        })

out = pd.DataFrame(rows)
out_csv = ROOT / 'phase_trace_t500.csv'
out.to_csv(out_csv, index=False)

lines = ['# Phase Trace Readout (t=500, 120 seeds/cell)', '']
for tlabel in ['baseline', 'high']:
    d = out[out['T_level'] == tlabel].sort_values('access_mult')
    peak = d.loc[d['dAUC'].idxmax()]
    a03 = d[d['dAUC'] >= 0.03]['access_mult'].tolist()
    a05 = d[d['dAUC'] >= 0.05]['access_mult'].tolist()
    lines.append(f'## {tlabel}')
    lines.append(d.to_string(index=False))
    lines.append(f"peak_access={peak['access_mult']:.2f}, peak_dAUC={peak['dAUC']:.4f}")
    lines.append(f'accesses_dAUC>=0.03: {a03}')
    lines.append(f'accesses_dAUC>=0.05: {a05}')
    lines.append('')

out_md = ROOT / 'phase_trace_readout.md'
out_md.write_text('\n'.join(lines), encoding='utf-8')

print(out.sort_values(['T_level', 'access_mult']).to_string(index=False))
print('WROTE', out_csv)
print('WROTE', out_md)
