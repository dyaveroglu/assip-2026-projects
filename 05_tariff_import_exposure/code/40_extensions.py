#!/usr/bin/env python3
"""
Project 05 (Tariff / Import Exposure) - Step 40: journal-track extensions.

Adds four real tables that deepen the paired event-study result WITHOUT touching
the student's reserved contribution (hand-collected firm-level 10-K input
sourcing, the China-vs-rest April-9 split, and the finished-goods-importer flag;
see STUDENT_TASKS.md). All identification here uses OBSERVABLE firm/industry
characteristics and design-based inference only, never the firm-level sourcing
dimension the student will hand-collect.

  t7_hetero.csv   Heterogeneity of the exposure loading by observable pre-event
                  moderators (COGS/sales input-intensity, size, beta, leverage,
                  book/market): base loading and interaction, for BOTH the shock
                  and the pause.
  t8_placebo.csv  Falsification on non-tariff big-market-move days. Using the same
                  market model (alpha,beta from [-252,-46]), we recompute exposure
                  loadings on the largest generic up/down days in 2024. If exposure
                  is a tariff channel and not a residual beta/high-vol artifact, it
                  should NOT load on generic big-move days once beta is controlled.
  t9_ri.csv       Randomization inference at the level treatment varies. The 73
                  NAICS-3 industry intensity values are permuted across industries
                  1000x, remapped to firms, RE-STANDARDIZED, and the full-spec
                  exposure loading is recomputed for the shock, the pause, and the
                  opposite-signed spread D = pause - shock (the H3 discriminator).
                  Also writes fig3_randinf.pdf.
  t10_power.csv   Minimum detectable effects (80% power) for the shock, pause,
                  round-trip, and pre-window loadings: shows the estimates are
                  precise and the round-trip zero is an informative (not underpowered)
                  zero.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reads the same analytical panel and raw
returns as 20_regressions.py.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf
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
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)  # deterministic RI (Date.now-free environment)

def wins(s, p=0.01):
    lo, hi = s.quantile(p), s.quantile(1-p); return s.clip(lo, hi)
def z(s):
    return (s - s.mean()) / s.std()
def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))
CTRL = ['z_size', 'z_beta', 'z_cogs_int', 'z_lev', 'z_bm']

def run(dv, rhs, data, cluster='naics3'):
    d = data.dropna(subset=[dv] + rhs + [cluster]).copy()
    m = smf.ols(dv + ' ~ ' + ' + '.join(rhs), data=d).fit(
        cov_type='cluster', cov_kwds={'groups': d[cluster]})
    return m

# =====================================================================
# T7 - Heterogeneity by OBSERVABLE moderators.
#   For moderator M (pre-event, median split), add z_imp_intensity*modhi and
#   the modhi main effect. "Base" = loading for the low-M group; "x M" = extra
#   loading for the high-M group. Reported for the shock and the pause.
#   Moderators are observable firm characteristics ONLY: firm-level import
#   sourcing / China exposure is the student's reserved hand-collected variable
#   and is deliberately NOT used here.
# =====================================================================
log('T7 heterogeneity by observable moderators ...')
MODS = [
    ('High COGS/sales (input-heavy)', 'cogs_int'),
    ('Large firm (ln assets)',        'size'),
    ('High market beta',              'beta'),
    ('High leverage',                 'lev'),
    ('High book/market (value)',      'bm'),
]
h7 = []
for name, col in MODS:
    d = df.dropna(subset=[col]).copy()
    cut = d[col].median()
    d['modhi'] = (d[col] > cut).astype(int)
    d['zx'] = d['z_imp_intensity'] * d['modhi']
    for dv, dvlab in [('car_s01', 'shock'), ('car_p0', 'pause')]:
        try:
            m = run(dv, ['z_imp_intensity', 'zx', 'modhi'] + CTRL, d)
            h7.append({'moderator': name, 'outcome': dvlab,
                       'base': m.params['z_imp_intensity'], 't_base': m.tvalues['z_imp_intensity'],
                       'inter': m.params['zx'], 't_inter': m.tvalues['zx'], 'N': int(m.nobs)})
            log(f'  {name:32s} {dvlab:5s} base={m.params["z_imp_intensity"]:+.4f}'
                f'(t={m.tvalues["z_imp_intensity"]:+.2f}) xM={m.params["zx"]:+.4f}'
                f'(t={m.tvalues["zx"]:+.2f})')
        except Exception as e:
            log(f'  {name} {dvlab} ERR {str(e)[:80]}')
t7 = pd.DataFrame(h7); t7.to_csv(os.path.join(OUT, 't7_hetero.csv'), index=False)

# =====================================================================
# T8 - Falsification on non-tariff big-market-move days.
#   Concern: does exposure just proxy for residual beta / high volatility, so
#   that it would load negatively on ANY down day and positively on ANY up day?
#   We control for beta throughout, but test it directly: recompute abnormal
#   returns on the largest GENERIC market-move days of 2024 (well outside the
#   tariff window) using the SAME market model (stored alpha,beta estimated over
#   [-252,-46] before the Apr-3 event, a window that spans these days), and re-run
#   the full-control exposure regression. Tariff-specific pricing => ~zero,
#   inconsistent loadings on generic big-move days.
# =====================================================================
log('T8 non-tariff big-move-day falsification ...')
dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date']); dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
mkt = pd.read_csv(os.path.join(RAW, 'market_ff.csv'))
mkt['date'] = pd.to_datetime(mkt['date']); mkt['mktret'] = pd.to_numeric(mkt['mktret'], errors='coerce')
mktmap = mkt.dropna(subset=['mktret']).set_index('date')['mktret']

# placebo days: largest |market move| days in 2024 inside the market-model
# estimation window (so stored alpha,beta are valid), 4 down + 4 up.
PLACEBO = [
    ('2024-08-05', 'down'), ('2024-12-18', 'down'), ('2024-07-24', 'down'), ('2024-09-03', 'down'),
    ('2024-11-06', 'up'),   ('2024-08-08', 'up'),   ('2025-01-15', 'up'),   ('2024-08-15', 'up'),
]
base = df[['permno', 'alpha', 'beta', 'z_imp_intensity', 'naics3'] + CTRL].dropna(subset=['alpha', 'beta']).copy()
t8 = []
for daystr, sign in PLACEBO:
    d0 = pd.Timestamp(daystr)
    if d0 not in mktmap.index:
        log(f'  {daystr} not a trading day, skip'); continue
    mret = float(mktmap.loc[d0])
    day = dsf[dsf.date == d0][['permno', 'ret']].merge(base, on='permno', how='inner')
    day['ar'] = day['ret'] - (day['alpha'] + day['beta'] * mret)   # single-day abnormal return
    try:
        m = run('ar', ['z_imp_intensity'] + CTRL, day)
        t8.append({'date': daystr, 'sign': sign, 'mktret': mret,
                   'coef_imp': m.params['z_imp_intensity'], 't_imp': m.tvalues['z_imp_intensity'],
                   'N': int(m.nobs)})
        log(f'  {daystr} ({sign}, mkt={mret:+.3f}) exposure coef={m.params["z_imp_intensity"]:+.4f}'
            f' (t={m.tvalues["z_imp_intensity"]:+.2f})')
    except Exception as e:
        log(f'  {daystr} ERR {str(e)[:80]}')
t8d = pd.DataFrame(t8); t8d.to_csv(os.path.join(OUT, 't8_placebo.csv'), index=False)
# share of placebo days on which exposure is significant at 5%
sig = float((t8d['t_imp'].abs() >= 1.96).mean())
log(f'  placebo days with |t|>=1.96: {sig:.0%}; mean |coef|={t8d.coef_imp.abs().mean():.4f}')

# =====================================================================
# T9 - Randomization inference at the level treatment varies (73 NAICS-3).
#   Permute the 73 industry-level intensity values across industries, remap to
#   firms, RE-STANDARDIZE, re-run the full spec. Tests the sharp null that
#   industry exposure is unrelated to CARs conditional on controls, honoring the
#   clustered structure (Young 2019). Report RI p-values for the shock loading,
#   the pause loading, and the opposite-signed spread D = pause - shock (H3).
# =====================================================================
log('T9 randomization inference (1000 permutations of industry exposure) ...')
NPERM = 1000
FULL = ['z_imp_intensity'] + CTRL
# industry-level intensity table (one value per NAICS-3)
ind = df.dropna(subset=['imp_intensity', 'naics3'])[['naics3', 'imp_intensity']].drop_duplicates('naics3').reset_index(drop=True)
ind_codes = ind['naics3'].values
ind_vals  = ind['imp_intensity'].values
n_ind = len(ind_codes)

def loadings(data):
    ms = run('car_s01', FULL, data); mp = run('car_p0', FULL, data)
    return ms.params['z_imp_intensity'], mp.params['z_imp_intensity']

real_s, real_p = loadings(df)
real_D = real_p - real_s
log(f'  actual: shock={real_s:+.4f} pause={real_p:+.4f} D(pause-shock)={real_D:+.4f}')

perm_s, perm_p, perm_D = [], [], []
for _ in range(NPERM):
    perm = np.random.permutation(ind_vals)
    m = dict(zip(ind_codes, perm))
    d = df.copy()
    d['imp_perm'] = d['naics3'].map(m)
    d = d.dropna(subset=['imp_perm'])
    d['z_imp_intensity'] = z(wins(d['imp_perm']))   # re-standardize the permuted exposure
    try:
        s, p = loadings(d)
        perm_s.append(s); perm_p.append(p); perm_D.append(p - s)
    except Exception:
        pass
perm_s = np.array(perm_s); perm_p = np.array(perm_p); perm_D = np.array(perm_D)
def ri_p(perm, real): return float(np.mean(np.abs(perm) >= abs(real)))
ri = {
    'shock': {'real': real_s, 'p': ri_p(perm_s, real_s), 'q025': np.percentile(perm_s, 2.5), 'q975': np.percentile(perm_s, 97.5)},
    'pause': {'real': real_p, 'p': ri_p(perm_p, real_p), 'q025': np.percentile(perm_p, 2.5), 'q975': np.percentile(perm_p, 97.5)},
    'spread (pause - shock)': {'real': real_D, 'p': ri_p(perm_D, real_D), 'q025': np.percentile(perm_D, 2.5), 'q975': np.percentile(perm_D, 97.5)},
}
t9 = pd.DataFrame([{'statistic': k, 'actual': v['real'], 'perm_q025': v['q025'],
                    'perm_q975': v['q975'], 'p_ri': v['p'], 'nperm': len(perm_s)}
                   for k, v in ri.items()])
t9.to_csv(os.path.join(OUT, 't9_ri.csv'), index=False)
for k, v in ri.items():
    log(f'  {k:24s} real={v["real"]:+.4f} RI p={v["p"]:.3f} perm95%[{v["q025"]:+.4f},{v["q975"]:+.4f}]')

# fig3: RI distribution of the opposite-signed spread D
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(perm_D, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(real_D, color='crimson', lw=2,
           label=f"Actual spread = {real_D:+.4f}\n(RI $p$ = {ri['spread (pause - shock)']['p']:.3f})")
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo opposite-signed spread  $D=\\hat\\beta_{pause}-\\hat\\beta_{shock}$  under permuted industry exposure')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 1000 permutations of industry exposure', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_randinf.pdf')); plt.close(fig)

# =====================================================================
# T10 - Minimum detectable effects (80% power).
#   MDE = (z_.975 + z_.80)*SE ~= 2.80*SE(exposure loading), in CAR points (pp).
#   Expressed against the cross-firm SD of the outcome CAR. A small MDE on the
#   near-zero round-trip means the full-reversal (H3) zero is an informative zero,
#   not an underpowered one.
# =====================================================================
log('T10 minimum detectable effects ...')
Z = 1.959964 + 0.841621
POW = [('car_s01', 'Shock [Apr3,4]'), ('car_p0', 'Pause [Apr9]'),
       ('car_round', 'Round-trip (pause+shock)'), ('car_pre', 'Pre-window [Mar27,Apr2]')]
t10 = []
for dv, lab in POW:
    m = run(dv, FULL, df)
    coef = m.params['z_imp_intensity']; se = m.bse['z_imp_intensity']
    tval = m.tvalues['z_imp_intensity']
    sd = df[dv].std()
    mde = Z * se
    t10.append({'dv': dv, 'label': lab, 'coef': coef, 'se': se, 't': tval, 'mde': mde,
                'mde_pct_sd': 100 * mde / sd, 'car_sd': sd})
    log(f'  {lab:26s} coef={coef:+.4f} SE={se:.4f} |t|={abs(tval):.2f} MDE={mde:.4f} '
        f'= {100*mde/sd:.1f}% of CAR SD')
t10d = pd.DataFrame(t10); t10d.to_csv(os.path.join(OUT, 't10_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the four new tables (numbers read from the CSVs above)
# =====================================================================
# --- T7 heterogeneity
body = ''
for name, _ in MODS:
    sub = t7[t7.moderator == name]
    sh = sub[sub.outcome == 'shock']; pa = sub[sub.outcome == 'pause']
    if sh.empty or pa.empty: continue
    sh = sh.iloc[0]; pa = pa.iloc[0]
    body += (f"{name} & {sh['base']:+.4f}{stars(sh['t_base'])} & {sh['inter']:+.4f}{stars(sh['t_inter'])} "
             f"& {pa['base']:+.4f}{stars(pa['t_base'])} & {pa['inter']:+.4f}{stars(pa['t_inter'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lcccc}
\toprule
& \multicolumn{2}{c}{Shock CAR[Apr3,4]} & \multicolumn{2}{c}{Pause CAR[Apr9]} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Moderator $M$ (pre-event) & Base & Exp.$\times M$ & Base & Exp.$\times M$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 placebo
body = ''
for _, r in t8d.iterrows():
    body += (f"{r['date']} & {r['sign']} & {100*r['mktret']:+.2f}\\% & "
             f"{r['coef_imp']:+.4f}{stars(r['t_imp'])} & ({r['t_imp']:+.2f}) & {int(r['N'])} \\\\\n")
w('tab_placebo.tex', r"""\begin{tabular}{llccccc}
\toprule
Placebo day & Direction & Market ret. & Exposure coef. & ($t$) & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 randomization inference
body = ''
for _, r in t9.iterrows():
    body += (f"{r['statistic']} & {r['actual']:+.4f} & [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] "
             f"& {r['p_ri']:.3f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lccc}
\toprule
Statistic & Actual & Perm.\ 95\% interval & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 power
body = ''
for _, r in t10d.iterrows():
    body += (f"{r['label']} & {r['coef']:+.4f} & {r['se']:.4f} & {abs(r['t']):.2f} & {r['mde']:.4f} "
             f"& {r['mde_pct_sd']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lccccc}
\toprule
Outcome (DV) & Coef. & SE & $|t|$ & MDE(80\%) & \% of CAR SD \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{
    'ri_p_shock': ri['shock']['p'], 'ri_p_pause': ri['pause']['p'],
    'ri_p_spread': ri['spread (pause - shock)']['p'], 'real_spread': real_D,
    'placebo_sig_share': sig, 'placebo_mean_abscoef': float(t8d.coef_imp.abs().mean()),
    'mde_shock': float(t10d[t10d.dv=='car_s01']['mde'].iloc[0]),
    'mde_round': float(t10d[t10d.dv=='car_round']['mde'].iloc[0]),
    'nperm': int(len(perm_s)), 'n_ind': int(n_ind),
}]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE - extension tables (t7-t10) + fig3 written.')
logf.close()
print('Extension tables written to', TEX)
