#!/usr/bin/env python3
"""
Project 13 - Step 20: price-discovery analysis on matched Kalshi/Polymarket pairs.

For each selected matched pair (same FOMC outcome on both venues, aligned hourly) we run:
  (a) descriptives      : level/return correlation, mean abs price gap, SDs
  (b) lead-lag CCF      : corr(dKalshi_t, dPoly_{t+k}); peak lag sign = who leads
  (c) Granger causality : VAR both directions, F-stat + p-value
  (d) Hasbrouck (1995)  : information share from a bivariate VECM with imposed
                          cointegrating vector (1,-1); upper/lower bounds + midpoint
  (e) Gonzalo-Granger   : permanent-transitory common-factor weights
  (f) spread stationarity (ADF) to confirm the two prices are cointegrated

Everything is written to output/tables/*.csv. No number is hand-entered anywhere.
"""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests, adfuller

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed')
OUT  = os.path.join(HERE, 'output', 'tables')
LOG  = os.path.join(HERE, 'logs', '20_analyze.log')
os.makedirs(OUT, exist_ok=True)
MAXLAG = 8       # max VECM/VAR lag considered (hours)
CCF_K  = 12      # lead-lag horizon (hours)

def log(m):
    print(m); open(LOG, 'a').write(str(m) + '\n')

# ---------- VECM estimation with imposed beta=(1,-1) ----------
def fit_vecm(p1, p2, k):
    """Delta p_t = alpha*z_{t-1} + sum Gamma_i Delta p_{t-i} + e_t, z=p1-p2."""
    p1 = np.asarray(p1, float); p2 = np.asarray(p2, float)
    d1 = np.diff(p1); d2 = np.diff(p2)               # length T-1
    z  = (p1 - p2)[:-1]                              # z_{t-1} aligned to d_t, length T-1
    T = len(d1)
    y1 = d1[k:]; y2 = d2[k:]                          # dependent, length T-k
    n = len(y1)
    X = [np.ones(n), z[k:]]                           # const + EC term z_{t-1}
    for i in range(1, k + 1):
        X.append(d1[k - i:T - i]); X.append(d2[k - i:T - i])
    X = np.column_stack(X)
    b1, *_ = np.linalg.lstsq(X, y1, rcond=None)
    b2, *_ = np.linalg.lstsq(X, y2, rcond=None)
    e1 = y1 - X @ b1; e2 = y2 - X @ b2
    Omega = np.cov(np.vstack([e1, e2]))
    alpha = np.array([b1[1], b2[1]])                 # EC loadings
    # Gamma_i 2x2 : rows eqn(1,2), cols (d1_{t-i}, d2_{t-i})
    G = []
    for i in range(1, k + 1):
        c = 2 + 2 * (i - 1)
        G.append(np.array([[b1[c], b1[c + 1]], [b2[c], b2[c + 1]]]))
    # AIC
    ll = -0.5 * n * (2 * np.log(2 * np.pi) + np.log(np.linalg.det(Omega)) + 2)
    npar = X.shape[1] * 2
    aic = -2 * ll + 2 * npar
    return alpha, G, Omega, aic, n

def hasbrouck_is(alpha, Omega):
    """Kalshi(index0) info-share lower/upper bounds; psi ~ alpha_perp=(a2,-a1)."""
    a1, a2 = alpha
    psi = np.array([a2, -a1])                        # common long-run row (up to scale)
    var = float(psi @ Omega @ psi)
    if var <= 0 or not np.isfinite(var):
        return np.nan, np.nan
    def is_kalshi(order):
        perm = np.array(order)
        Op = Omega[np.ix_(perm, perm)]
        try:
            M = np.linalg.cholesky(Op)
        except np.linalg.LinAlgError:
            return np.nan
        f = psi[perm] @ M
        isp = f ** 2 / var
        out = np.zeros(2)
        for pos, i in enumerate(perm):
            out[i] = isp[pos]
        return out[0]
    a = is_kalshi([0, 1]); b = is_kalshi([1, 0])
    return (min(a, b), max(a, b))

def gonzalo_granger(alpha):
    a1, a2 = alpha
    denom = a2 - a1
    if abs(denom) < 1e-9:
        return np.nan
    return a2 / denom                                # GG weight of Kalshi

def leadlag(d1, d2, K):
    d1 = (d1 - d1.mean()); d2 = (d2 - d2.mean())
    s1 = d1.std(); s2 = d2.std()
    if s1 == 0 or s2 == 0:
        return {k: np.nan for k in range(-K, K + 1)}
    n = len(d1); res = {}
    for k in range(-K, K + 1):
        if k >= 0:
            a = d1[:n - k]; b = d2[k:]
        else:
            a = d1[-k:]; b = d2[:n + k]
        res[k] = float(np.mean(a * b) / (s1 * s2))
    return res                                        # k>0: Kalshi leads Poly

def granger_pair(d1, d2, k):
    """Return (F_kalshi->poly, p, F_poly->kalshi, p)."""
    try:
        # cause Kalshi -> effect Poly: array [effect, cause] = [d2, d1]
        r1 = grangercausalitytests(np.column_stack([d2, d1]), maxlag=[k], verbose=False)
        F1, p1 = r1[k][0]['ssr_ftest'][0], r1[k][0]['ssr_ftest'][1]
        r2 = grangercausalitytests(np.column_stack([d1, d2]), maxlag=[k], verbose=False)
        F2, p2 = r2[k][0]['ssr_ftest'][0], r2[k][0]['ssr_ftest'][1]
        return F1, p1, F2, p2
    except Exception:
        return (np.nan,) * 4

def pick_k(p1, p2):
    best, bk = np.inf, 2
    for k in range(1, MAXLAG + 1):
        try:
            _, _, _, aic, n = fit_vecm(p1, p2, k)
            if np.isfinite(aic) and aic < best and n > 30:
                best, bk = aic, k
        except Exception:
            continue
    return bk

def main():
    open(LOG, 'w').close()
    panel = pd.read_csv(os.path.join(PROC, 'matched_panel.csv'))
    sel = pd.read_csv(os.path.join(PROC, 'pairs_selected.csv'))
    pairs = [p for p in panel['pair'].unique()]
    log(f'analysing {len(pairs)} selected pairs')
    sumrows, hbrows, grrows, llrows = [], [], [], []
    ccf_acc = {k: [] for k in range(-CCF_K, CCF_K + 1)}
    for pair in pairs:
        g = panel[panel.pair == pair].sort_values('ts')
        meeting, outcome = g.meeting.iloc[0], g.outcome.iloc[0]
        p1 = g.kalshi_p.clip(1e-4, 1 - 1e-4).values
        p2 = g.poly_p.clip(1e-4, 1 - 1e-4).values
        d1 = np.diff(p1); d2 = np.diff(p2)
        n = len(p1)
        # descriptives
        corr_lvl = float(np.corrcoef(p1, p2)[0, 1])
        corr_ret = float(np.corrcoef(d1, d2)[0, 1]) if d1.std() > 0 and d2.std() > 0 else np.nan
        gap = float(np.mean(np.abs(p1 - p2)))
        # spread stationarity
        try:
            adf_p = float(adfuller(p1 - p2, maxlag=6, autolag=None)[1])
        except Exception:
            adf_p = np.nan
        sumrows.append(dict(pair=pair, meeting=meeting, outcome=outcome, n=n,
                            kalshi_mean=round(float(p1.mean()), 3), poly_mean=round(float(p2.mean()), 3),
                            corr_level=round(corr_lvl, 3), corr_return=round(corr_ret, 3),
                            mean_abs_gap=round(gap, 4), kalshi_ret_sd=round(float(d1.std()), 4),
                            poly_ret_sd=round(float(d2.std()), 4), adf_spread_p=round(adf_p, 4)))
        # lead-lag
        ll = leadlag(d1, d2, CCF_K)
        for k, v in ll.items():
            if np.isfinite(v): ccf_acc[k].append(v)
        peak_k = max(ll, key=lambda k: abs(ll[k]) if np.isfinite(ll[k]) else -1)
        llrows.append(dict(pair=pair, meeting=meeting, outcome=outcome,
                           peak_lag=peak_k, peak_corr=round(ll[peak_k], 3),
                           ccf_0=round(ll[0], 3),
                           leads='Kalshi' if peak_k > 0 else ('Polymarket' if peak_k < 0 else 'Contemp')))
        # VECM / Hasbrouck / GG / Granger
        k = pick_k(p1, p2)
        alpha, G, Omega, aic, nvecm = fit_vecm(p1, p2, k)
        lo, hi = hasbrouck_is(alpha, Omega)
        gg = gonzalo_granger(alpha)
        F1, gp1, F2, gp2 = granger_pair(d1, d2, k)
        hbrows.append(dict(pair=pair, meeting=meeting, outcome=outcome, k=k, n=nvecm,
                           alpha_kalshi=round(float(alpha[0]), 4), alpha_poly=round(float(alpha[1]), 4),
                           IS_kalshi_lo=round(lo, 3), IS_kalshi_hi=round(hi, 3),
                           IS_kalshi_mid=round((lo + hi) / 2, 3),
                           IS_poly_mid=round(1 - (lo + hi) / 2, 3),
                           GG_kalshi=round(gg, 3) if np.isfinite(gg) else np.nan))
        grrows.append(dict(pair=pair, meeting=meeting, outcome=outcome, k=k,
                           F_kalshi_to_poly=round(F1, 2), p_kalshi_to_poly=round(gp1, 4),
                           F_poly_to_kalshi=round(F2, 2), p_poly_to_kalshi=round(gp2, 4)))
        log(f'  {pair:18s} k={k} IS_kalshi=[{lo:.2f},{hi:.2f}] mid={(lo+hi)/2:.2f} '
            f'GG={gg:.2f} peaklag={peak_k} Fk->p={F1:.1f}(p={gp1:.3f}) Fp->k={F2:.1f}(p={gp2:.3f})')
    sumdf = pd.DataFrame(sumrows); hbdf = pd.DataFrame(hbrows)
    grdf = pd.DataFrame(grrows); lldf = pd.DataFrame(llrows)
    sumdf.to_csv(os.path.join(OUT, 't2_sumstats.csv'), index=False)
    lldf.to_csv(os.path.join(OUT, 't3_leadlag.csv'), index=False)
    grdf.to_csv(os.path.join(OUT, 't4_granger.csv'), index=False)
    hbdf.to_csv(os.path.join(OUT, 't5_hasbrouck.csv'), index=False)
    # pooled CCF for figure
    ccf = pd.DataFrame({'lag': list(ccf_acc.keys()),
                        'mean_ccf': [np.mean(v) if v else np.nan for v in ccf_acc.values()],
                        'n': [len(v) for v in ccf_acc.values()]}).sort_values('lag')
    ccf.to_csv(os.path.join(OUT, 'ccf_pooled.csv'), index=False)
    # sample / summary table
    samp = (sumdf.groupby('meeting').agg(pairs=('pair', 'nunique'),
             obs=('n', 'sum'), mean_gap=('mean_abs_gap', 'mean'),
             mean_corr=('corr_level', 'mean')).reset_index())
    samp.to_csv(os.path.join(OUT, 't1_sample.csv'), index=False)
    # headline averages
    hv = hbdf.dropna(subset=['IS_kalshi_mid'])
    summary = dict(
        n_pairs=len(hbdf),
        mean_IS_kalshi=round(float(hv.IS_kalshi_mid.mean()), 3),
        median_IS_kalshi=round(float(hv.IS_kalshi_mid.median()), 3),
        wmean_IS_kalshi=round(float(np.average(hv.IS_kalshi_mid, weights=hv.n)), 3),
        mean_IS_poly=round(1 - float(hv.IS_kalshi_mid.mean()), 3),
        mean_GG_kalshi=round(float(hbdf.GG_kalshi.dropna().mean()), 3),
        pairs_kalshi_leads=int((hv.IS_kalshi_mid > 0.5).sum()),
        pairs_poly_leads=int((hv.IS_kalshi_mid < 0.5).sum()),
        mean_corr_level=round(float(sumdf.corr_level.mean()), 3),
        mean_abs_gap=round(float(sumdf.mean_abs_gap.mean()), 4),
        frac_spread_stationary=round(float((sumdf.adf_spread_p < 0.05).mean()), 3))
    pd.DataFrame([summary]).to_csv(os.path.join(OUT, 't6_summary.csv'), index=False)
    log('SUMMARY: ' + str(summary))

if __name__ == '__main__':
    main()
