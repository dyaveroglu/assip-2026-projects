#!/usr/bin/env python3
"""
Project 11 (CHIPS awards) -- Step 40: journal-track extensions.

Adds four real tables that deepen the null WITHOUT touching the student's
reserved contributions (primary-source date verification, entity->ticker
resolution, the news/confound timeline beyond the pre-existing AMKR flag,
second-event "funding agreement" dates, and required-private-co-investment
dollar amounts). Every moderator/statistic below uses OBSERVABLE data only:
CRSP returns, market caps, betas, SIC codes, and the grant-vs-grant+loan flag
that already lives in the raw award file.

  t6_hetero.csv    Cross-sectional heterogeneity of the announcement CAR by
                   observable moderators (award structure, firm size, relative
                   award size, core-semiconductor SIC, market beta): subgroup
                   mean CARs + difference-in-means test.
  t7_altmodels.csv Robustness of the mean CAR to the abnormal-return model and
                   the estimation window (market model / market-adjusted /
                   mean-adjusted; long/short windows), plus alternative test
                   statistics (cross-sectional t, Patell Z, BMP Z, generalized
                   sign Z) computed from the daily CRSP record.
  t8_randinf.csv   Design-based (randomization) inference: (a) 2,000 placebo
                   event dates -> null distribution of the mean CAR (tests H1
                   without the small-N t asymptotics); (b) 2,000 permutations of
                   the award-size vector -> null distribution of the OLS slope
                   and Spearman rho (tests H2 / diagnoses the t=32 leverage
                   point). Also writes fig3_randinf.pdf.
  t9_power.csv     Minimum detectable effect (80% power) for the mean CAR in
                   each window: shows the null is informative, not merely
                   underpowered given N=15.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex.
Reads the same processed panel as 20_regressions.py plus the raw CRSP daily file.
"""
import os, sys, bisect, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw')
PROC = os.path.join(HERE, 'data', 'processed')
OUT  = os.path.join(HERE, 'output', 'tables')
TEX  = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
for d in (OUT, TEX, FIG): os.makedirs(d, exist_ok=True)
LOG  = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)   # deterministic RI

def stars(t):
    a = abs(t) if pd.notna(t) else 0.0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

# ---------------------------------------------------------------------------
# Load the analytical panel (per-event CARs) + the raw daily CRSP record so we
# can recompute abnormal returns under alternative models and placebo dates.
# ---------------------------------------------------------------------------
df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))
df['announce_date'] = pd.to_datetime(df['announce_date'])
# merge SIC (siccd) from the award file (not present in cars.csv); 9999 = unclassified
aw = pd.read_csv(os.path.join(RAW, 'awards_with_permno.csv'))[['ticker', 'siccd', 'award_type']]
df = df.merge(aw, on='ticker', how='left', suffixes=('', '_aw'))
log(f'panel: {len(df)} events; SIC merged; grant+loan={int((df.award_type=="grant+loan").sum())}')

dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date'])
dsf['ret']  = pd.to_numeric(dsf['ret'], errors='coerce')
dsf = dsf.dropna(subset=['ret'])
mkt = pd.read_csv(os.path.join(RAW, 'crsp_market.csv'))
mkt['date'] = pd.to_datetime(mkt['date'])
mkt['mktret'] = pd.to_numeric(mkt['vwretd'], errors='coerce')
mkt = mkt[['date', 'mktret']].dropna().sort_values('date').reset_index(drop=True)
CAL = list(mkt['date']); CALPOS = {d: i for i, d in enumerate(CAL)}
MRET = mkt.set_index('date')['mktret']

# ---------------------------------------------------------------------------
# Core recompute engine: abnormal returns in an event window under one of three
# models, given a firm's daily returns and an event date, plus the estimation
# residual SD and the market-return leverage quantities Patell needs.
# ---------------------------------------------------------------------------
def firm_ar(sub, ev, window, model='mm', est=(-252, -46), min_obs=100):
    """Return dict with cumulative AR over `window`, per-day ARs, estimation
    residual SD s, L, and (for Patell) market SS + est-window daily ARs.
    None if the estimation/event window does not fully fit the calendar."""
    pos = bisect.bisect_left(CAL, ev)
    if pos >= len(CAL):
        return None
    g = sub[sub.date.isin(CALPOS)].copy()
    g['rel'] = g.date.map(CALPOS) - pos
    e = g[(g.rel >= est[0]) & (g.rel <= est[1])]
    if len(e) < min_obs:
        return None
    m_e = MRET.loc[e.date.values].values.astype(float)
    y_e = e.ret.values.astype(float)
    if model == 'mm':
        X = np.column_stack([np.ones(len(m_e)), m_e])
        (alpha, beta), *_ = np.linalg.lstsq(X, y_e, rcond=None)
        resid_e = y_e - (alpha + beta * m_e)
    elif model == 'madj':          # market-adjusted: alpha=0, beta=1
        alpha, beta = 0.0, 1.0
        resid_e = y_e - m_e
    elif model == 'meanadj':       # mean-adjusted: constant expected return
        alpha, beta = float(y_e.mean()), 0.0
        resid_e = y_e - alpha
    else:
        raise ValueError(model)
    L = len(e)
    s = float(np.sqrt((resid_e ** 2).sum() / (L - 2)))
    mbar = float(m_e.mean()); ss_m = float(((m_e - mbar) ** 2).sum())
    ev_rows = g[(g.rel >= window[0]) & (g.rel <= window[1])]
    if ev_rows.empty:
        return None
    m_ev = MRET.loc[ev_rows.date.values].values.astype(float)
    ar_ev = ev_rows.ret.values.astype(float) - (alpha + beta * m_ev)
    frac_pos_est = float((resid_e > 0).mean())
    return dict(car=float(ar_ev.sum()), ar_ev=ar_ev, m_ev=m_ev, s=s, L=L,
                mbar=mbar, ss_m=ss_m, frac_pos_est=frac_pos_est, n_ev=len(ar_ev))

WIN = {'car_m1_1': (-1, 1), 'car_0_1': (0, 1), 'car_0_3': (0, 3),
       'car_m1_5': (-1, 5), 'car_m5_5': (-5, 5), 'car_pre': (-10, -3)}

def event_stats(model, window):
    """Mean/median/t and (market-model) Patell Z, BMP Z, generalized-sign Z
    over all firms for the given model + window."""
    cars, csar, fpos = [], [], []
    for _, a in df.iterrows():
        sub = dsf[dsf.permno == a.permno]
        r = firm_ar(sub, a.announce_date, window, model=model)
        if r is None:
            continue
        cars.append(r['car'])
        # Patell standardized cumulative AR (window length W): sum of daily SAR / sqrt(W)
        var_day = r['s'] ** 2 * (1.0 + 1.0 / r['L'] + (r['m_ev'] - r['mbar']) ** 2 / r['ss_m'])
        sar = r['ar_ev'] / np.sqrt(var_day)
        csar.append(float(sar.sum() / np.sqrt(r['n_ev'])))
        fpos.append(r['frac_pos_est'])
    cars = np.array(cars); csar = np.array(csar); fpos = np.array(fpos)
    n = len(cars)
    mean = cars.mean(); med = np.median(cars); npos = int((cars > 0).sum())
    t = mean / (cars.std(ddof=1) / np.sqrt(n))
    # Patell Z: sum CSAR / sqrt(sum (L-2)/(L-4)); L=207 -> ~1.0
    adj = (207 - 2) / (207 - 4)
    patell = csar.sum() / np.sqrt(n * adj)
    # BMP: cross-sectional t of the standardized CARs (robust to event-induced var.)
    bmp = csar.mean() / (csar.std(ddof=1) / np.sqrt(n))
    # Generalized sign Z: vs estimation-window positivity rate
    phat = float(fpos.mean())
    gsign = (npos - n * phat) / np.sqrt(n * phat * (1 - phat))
    return dict(model=model, window=window, n=n, mean=mean, median=med,
                t=t, npos=npos, patell=patell, bmp=bmp, gsign=gsign)

# ===========================================================================
# T6 -- Cross-sectional heterogeneity by OBSERVABLE moderators.
#   Subgroup mean CAR[-1,+1] + difference-in-means (Welch) t-test.
# ===========================================================================
log('T6 heterogeneity by observable moderators ...')
d6 = df.copy()
med_mcap = d6.mktcap_m.median(); med_rel = d6.award_pct_mktcap.median(); med_beta = d6.beta.median()
MODS = [
    ('Award structure: grant+loan vs grant-only', d6.award_type == 'grant+loan'),
    ('Firm size: above vs below median mkt cap',   d6.mktcap_m > med_mcap),
    ('Relative award: above vs below median',      d6.award_pct_mktcap > med_rel),
    ('Core semiconductor (SIC 3674) vs other',     d6.siccd == 3674),
    ('Market beta: above vs below median',         d6.beta > med_beta),
]
h6 = []
for name, hi in MODS:
    a = d6.loc[hi, 'car_m1_1'].dropna(); b = d6.loc[~hi, 'car_m1_1'].dropna()
    diff = a.mean() - b.mean()
    tt = stats.ttest_ind(a, b, equal_var=False)
    h6.append({'moderator': name, 'mean_hi': a.mean(), 'n_hi': len(a),
               'mean_lo': b.mean(), 'n_lo': len(b), 'diff': diff, 't_diff': tt.statistic})
    log(f'  {name:44s} hi={a.mean():+.4f}(n{len(a)}) lo={b.mean():+.4f}(n{len(b)}) '
        f'diff={diff:+.4f} t={tt.statistic:+.2f}')
t6 = pd.DataFrame(h6); t6.to_csv(os.path.join(OUT, 't6_hetero.csv'), index=False)

# ===========================================================================
# T7 -- Robustness to AR model / estimation window + alternative test stats.
#   Self-check: the market-model [-1,+1] row must reproduce +2.6% / t=0.99.
# ===========================================================================
log('T7 alternative models + test statistics ...')
# Panel A: mean CAR[-1,+1] across model + estimation-window variants
variantsA = [
    ('Market model (baseline)',       'mm',      (-252, -46), (-1, 1)),
    ('Market-adjusted ($\\beta=1$)',  'madj',    (-252, -46), (-1, 1)),
    ('Mean-adjusted',                 'meanadj', (-252, -46), (-1, 1)),
]
pa = []
for name, model, est, win in variantsA:
    cars = []
    for _, a in df.iterrows():
        r = firm_ar(dsf[dsf.permno == a.permno], a.announce_date, win, model=model, est=est)
        if r is not None: cars.append(r['car'])
    cars = np.array(cars); n = len(cars)
    t = cars.mean() / (cars.std(ddof=1) / np.sqrt(n))
    pa.append({'variant': name, 'mean': cars.mean(), 'median': np.median(cars),
               't': t, 'npos': int((cars > 0).sum()), 'n': n})
    log(f'  A {name:32s} mean={cars.mean():+.4f} t={t:+.2f} n={n}')
# alternative estimation-window lengths (market model)
for name, est in [('Market model, est.\\ $[-252,-11]$', (-252, -11)),
                  ('Market model, est.\\ $[-120,-11]$', (-120, -11))]:
    cars = []
    for _, a in df.iterrows():
        r = firm_ar(dsf[dsf.permno == a.permno], a.announce_date, (-1, 1), model='mm', est=est)
        if r is not None: cars.append(r['car'])
    cars = np.array(cars); n = len(cars)
    t = cars.mean() / (cars.std(ddof=1) / np.sqrt(n))
    pa.append({'variant': name, 'mean': cars.mean(), 'median': np.median(cars),
               't': t, 'npos': int((cars > 0).sum()), 'n': n})
    log(f'  A {name:32s} mean={cars.mean():+.4f} t={t:+.2f} n={n}')
t7a = pd.DataFrame(pa)
# SELF-CHECK
base = t7a.iloc[0]
assert abs(base['mean'] - 0.0264) < 0.002 and abs(base['t'] - 0.99) < 0.05, \
    f"market-model recompute mismatch: mean={base['mean']:.4f} t={base['t']:.2f}"
log(f'  SELF-CHECK ok: baseline market-model mean={base["mean"]:+.4f} t={base["t"]:.2f}')
t7a.to_csv(os.path.join(OUT, 't7_altmodels.csv'), index=False)

# Panel B: alternative test statistics (market model), two windows
pb = []
for win, wlab in [((-1, 1), 'CAR[-1,+1]'), ((0, 3), 'CAR[0,+3]')]:
    s = event_stats('mm', win)
    pb.append({'window': wlab, 'mean': s['mean'], 't': s['t'], 'patell': s['patell'],
               'bmp': s['bmp'], 'gsign': s['gsign'], 'npos': s['npos'], 'n': s['n']})
    log(f'  B {wlab}: t={s["t"]:+.2f} Patell={s["patell"]:+.2f} BMP={s["bmp"]:+.2f} '
        f'gsign={s["gsign"]:+.2f}')
t7b = pd.DataFrame(pb); t7b.to_csv(os.path.join(OUT, 't7_teststats.csv'), index=False)

# ===========================================================================
# T8 -- Design-based (randomization) inference.
#  (a) Placebo event dates: for each of 2,000 iterations, draw ONE common
#      random calendar offset that keeps every firm's full [-252,-46] estimation
#      window and [-1,+1] event window inside the CRSP file and away from the
#      true event, recompute each firm's placebo CAR, average -> null of the
#      mean CAR. Design-based p = share of |placebo mean| >= |actual|.
#  (b) Permuted award size: permute the award/mktcap vector across firms while
#      holding CARs fixed; recompute the OLS slope and Spearman rho -> null.
# ===========================================================================
log('T8 randomization / placebo inference ...')
actual_mean = df.car_m1_1.mean()

# Precompute, per firm, the set of admissible placebo day-0 positions: those
# whose [-252,-46] and [-1,+1] windows fit the calendar and exclude the true
# event window +/- 5 days. Draw a shared *percentile* so all firms move together
# but each maps it into its own admissible range (guarantees all 15 firms).
firm_days = {}
for _, a in df.iterrows():
    sub = dsf[dsf.permno == a.permno]
    days = sub[sub.date.isin(CALPOS)].date.map(CALPOS).sort_values().values
    truepos = bisect.bisect_left(CAL, a.announce_date)
    lo, hi = truepos - 5, truepos + 5
    ok = [p for p in days if (p - 252) >= days.min() and (p + 1) <= days.max()
          and not (lo <= p <= hi)]
    firm_days[a.permno] = (sub, np.array(sorted(ok)))

NPERM = 2000
placebo_means = []
for _ in range(NPERM):
    u = np.random.rand()                # shared quantile -> common pseudo-timing
    cars = []
    for _, a in df.iterrows():
        sub, ok = firm_days[a.permno]
        if len(ok) == 0: continue
        p = ok[int(u * (len(ok) - 1))]
        evdate = CAL[p]
        r = firm_ar(sub, evdate, (-1, 1), model='mm')
        if r is not None: cars.append(r['car'])
    if len(cars) == len(df):            # require all 15 firms
        placebo_means.append(np.mean(cars))
placebo_means = np.array(placebo_means)
p_mean = float(np.mean(np.abs(placebo_means) >= abs(actual_mean)))
log(f'  (a) placebo mean CAR: actual={actual_mean:+.4f}  n_valid={len(placebo_means)}  '
    f'RI p={p_mean:.3f}  perm95=[{np.percentile(placebo_means,2.5):+.4f},'
    f'{np.percentile(placebo_means,97.5):+.4f}]')

# (b) permuted award-size labels vs fixed CARs
dd = df.dropna(subset=['car_m1_1', 'award_pct_mktcap']).copy()
y = dd.car_m1_1.values; x = dd.award_pct_mktcap.values
actual_slope = np.polyfit(x, y, 1)[0]
actual_rho = stats.spearmanr(x, y).correlation
perm_slopes, perm_rhos = [], []
for _ in range(NPERM):
    xp = np.random.permutation(x)
    perm_slopes.append(np.polyfit(xp, y, 1)[0])
    perm_rhos.append(stats.spearmanr(xp, y).correlation)
perm_slopes = np.array(perm_slopes); perm_rhos = np.array(perm_rhos)
p_slope = float(np.mean(np.abs(perm_slopes) >= abs(actual_slope)))
p_rho = float(np.mean(np.abs(perm_rhos) >= abs(actual_rho)))
log(f'  (b) permuted slope: actual={actual_slope:+.5f} RI p={p_slope:.3f}; '
    f'Spearman rho={actual_rho:+.3f} RI p={p_rho:.3f}')

t8 = pd.DataFrame([
    {'test': 'Mean CAR[-1,+1] (placebo event dates)', 'statistic': 'Mean CAR',
     'actual': actual_mean, 'perm_q025': np.percentile(placebo_means, 2.5),
     'perm_q975': np.percentile(placebo_means, 97.5), 'p_ri': p_mean, 'nperm': len(placebo_means)},
    {'test': 'Scaling slope (permuted award size)', 'statistic': 'OLS slope',
     'actual': actual_slope, 'perm_q025': np.percentile(perm_slopes, 2.5),
     'perm_q975': np.percentile(perm_slopes, 97.5), 'p_ri': p_slope, 'nperm': NPERM},
    {'test': 'Rank scaling (permuted award size)', 'statistic': 'Spearman $\\rho$',
     'actual': actual_rho, 'perm_q025': np.percentile(perm_rhos, 2.5),
     'perm_q975': np.percentile(perm_rhos, 97.5), 'p_ri': p_rho, 'nperm': NPERM},
])
t8.to_csv(os.path.join(OUT, 't8_randinf.csv'), index=False)

# fig3: two-panel RI distributions
fig, axes = plt.subplots(1, 2, figsize=(10, 4.0))
ax = axes[0]
ax.hist(placebo_means * 100, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(actual_mean * 100, color='crimson', lw=2,
           label=f'Actual = {actual_mean*100:+.1f}\\%\n(RI $p$ = {p_mean:.2f})')
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo mean CAR[-1,+1] (\\%)'); ax.set_ylabel('Frequency')
ax.legend(frameon=False, fontsize=9)
ax.set_title('(a) Placebo event dates', fontsize=10)
ax = axes[1]
ax.hist(perm_slopes, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(actual_slope, color='crimson', lw=2,
           label=f'Actual slope = {actual_slope:+.4f}\n(RI $p$ = {p_slope:.2f})')
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Cross-sectional slope under permuted award size'); ax.set_ylabel('Frequency')
ax.legend(frameon=False, fontsize=9)
ax.set_title('(b) Permuted award-size labels', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_randinf.pdf')); plt.close(fig)

# ===========================================================================
# T9 -- Minimum detectable effect (80% power) for the mean CAR in each window.
#   MDE = (z_.975 + z_.80) * SE(mean CAR) ~= 2.80 * (SD/sqrt(N)).
# ===========================================================================
log('T9 minimum detectable effects ...')
Z = 1.959964 + 0.841621
WLAB = {'car_m1_1': 'CAR[-1,+1]', 'car_0_1': 'CAR[0,+1]', 'car_0_3': 'CAR[0,+3]',
        'car_m1_5': 'CAR[-1,+5]', 'car_m5_5': 'CAR[-5,+5]'}
t9 = []
for col, lab in WLAB.items():
    s = df[col].dropna(); n = len(s)
    se = s.std(ddof=1) / np.sqrt(n)
    mde = Z * se
    t9.append({'window': lab, 'mean': s.mean(), 'se': se, 't': s.mean() / se,
               'mde': mde, 'mde_excl_wolf': Z * (df[df.ticker != 'WOLF'][col].std(ddof=1)
                                                 / np.sqrt(n - 1))})
    log(f'  {lab:11s} mean={s.mean():+.4f} SE={se:.4f} MDE(80%)={mde:.4f}')
t9d = pd.DataFrame(t9); t9d.to_csv(os.path.join(OUT, 't9_power.csv'), index=False)

# ===========================================================================
# Render LaTeX for the four new tables
# ===========================================================================
# --- T6 heterogeneity
body = ''
for _, r in t6.iterrows():
    body += (f"{r['moderator']} & {r['mean_hi']*100:+.2f} & {r['n_hi']:.0f} & "
             f"{r['mean_lo']*100:+.2f} & {r['n_lo']:.0f} & {r['diff']*100:+.2f} & "
             f"{r['t_diff']:+.2f}{stars(r['t_diff'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lcccccc}
\toprule
& \multicolumn{2}{c}{High/Yes group} & \multicolumn{2}{c}{Low/No group} & & \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Moderator (observable) & Mean (\%) & $N$ & Mean (\%) & $N$ & Diff.\ (\%) & $t$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T7 Panel A (models/windows) + Panel B (test stats)
bodyA = ''
for _, r in t7a.iterrows():
    bodyA += (f"{r['variant']} & {r['mean']*100:+.2f} & {r['median']*100:+.2f} & "
              f"{r['t']:+.2f}{stars(r['t'])} & {r['npos']:.0f}/{r['n']:.0f} \\\\\n")
bodyB = ''
for _, r in t7b.iterrows():
    bodyB += (f"{r['window']} & {r['t']:+.2f}{stars(r['t'])} & {r['patell']:+.2f}{stars(r['patell'])} "
              f"& {r['bmp']:+.2f}{stars(r['bmp'])} & {r['gsign']:+.2f}{stars(r['gsign'])} \\\\\n")
w('tab_altmodels.tex', r"""\begin{tabular}{lcccc}
\multicolumn{5}{l}{\textit{Panel A: mean CAR$[-1,+1]$ across abnormal-return models and estimation windows}}\\
\toprule
Specification & Mean (\%) & Median (\%) & $t$-stat & \# pos. \\
\midrule
""" + bodyA + r"""\bottomrule
\end{tabular}

\vspace{6pt}

\begin{tabular}{lcccc}
\multicolumn{5}{l}{\textit{Panel B: alternative test statistics (market model)}}\\
\toprule
Window & Cross-sec.\ $t$ & Patell $Z$ & BMP $Z$ & Gen.\ sign $Z$ \\
\midrule
""" + bodyB + r"""\bottomrule
\end{tabular}""")

# --- T8 randomization inference
body = ''
for _, r in t8.iterrows():
    a = r['actual']
    astr = f"{a*100:+.2f}\\%" if r['statistic'] == 'Mean CAR' else f"{a:+.4f}"
    q0 = f"{r['perm_q025']*100:+.2f}, {r['perm_q975']*100:+.2f}" if r['statistic'] == 'Mean CAR' \
         else f"{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}"
    body += (f"{r['test']} & {r['statistic']} & {astr} & [{q0}] & {r['p_ri']:.3f} \\\\\n")
w('tab_randinf.tex', r"""\begin{tabular}{llccc}
\toprule
Test & Statistic & Actual & Perm.\ 95\% interval & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 power
body = ''
for _, r in t9d.iterrows():
    body += (f"{r['window']} & {r['mean']*100:+.2f} & {r['se']*100:.2f} & {r['t']:+.2f} & "
             f"{r['mde']*100:.2f} & {r['mde_excl_wolf']*100:.2f} \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lccccc}
\toprule
Window & Mean CAR (\%) & SE (\%) & $t$ & MDE(80\%) (\%) & MDE excl.\ WOLF (\%) \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{
    'ri_p_mean': p_mean, 'ri_p_slope': p_slope, 'ri_p_rho': p_rho,
    'placebo_lo': np.percentile(placebo_means, 2.5), 'placebo_hi': np.percentile(placebo_means, 97.5),
    'mde_m1_1': float(t9d[t9d.window == 'CAR[-1,+1]']['mde'].iloc[0]),
    'patell_m1_1': float(t7b[t7b.window == 'CAR[-1,+1]']['patell'].iloc[0]),
    'bmp_m1_1': float(t7b[t7b.window == 'CAR[-1,+1]']['bmp'].iloc[0]),
    'gsign_m1_1': float(t7b[t7b.window == 'CAR[-1,+1]']['gsign'].iloc[0]),
    'grantloan_mean': float(t6[t6.moderator.str.startswith('Award structure')]['mean_hi'].iloc[0]),
    'grantonly_mean': float(t6[t6.moderator.str.startswith('Award structure')]['mean_lo'].iloc[0]),
}]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE -- 4 extension tables + fig3 written.')
logf.close()
print('Extension tables written to', TEX)
