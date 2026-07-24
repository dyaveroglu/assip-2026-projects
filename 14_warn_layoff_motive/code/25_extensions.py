#!/usr/bin/env python3
"""
Project 14 (WARN) - Step 25: journal-track extensions.

Adds four NEW real tables (+ one figure) that deepen the cross-sectional
event study without touching the student's reserved contribution (the
hand-coded layoff MOTIVE / `strategic` variable, and the verified/rescued
ticker matches -- see STUDENT_TASKS.md). Everything here uses ONLY observable
data (the machine `is_closure` proxy and firm characteristics) and design-based
inference; the hand-coded motive is never constructed or used.

  t7_hetero_ext.csv  Cross-sectional heterogeneity of the materiality effect by
                     NEW observable moderators (valuation, asset turnover, early
                     2022 sample, goods-producing), distinct from t5's
                     size/closure/tech interactions.
  t8_randinf.csv     Randomization inference: permute the materiality regressor
                     (and, separately, the motive/closure indicator) across
                     events 2,000x; a design-based p-value that does not rely on
                     clustered-SE asymptotics. Writes fig3_randinf.pdf.
  t9_altbench.csv    Alternative abnormal-return benchmarks (alt identification):
                     re-derive CAR[0,+5] under market-adjusted (beta=1),
                     S&P-500-adjusted, and mean-adjusted models straight from the
                     raw CRSP daily returns, and re-run H1 (mean CAR) and H2
                     (materiality slope) under each. A reconciliation gate first
                     rebuilds the market-model CAR from stored alpha/beta and
                     confirms it matches cars.csv row-for-row.
  t10_power.csv      Minimum detectable effects (80% power) for the materiality
                     slope and -- critically -- the machine motive (closure)
                     coefficient: quantifies how large a motive effect the crude
                     proxy could actually detect, motivating the hand-coding.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reads the same processed panel as
20_regressions.py plus the raw CRSP daily returns for the alt-benchmark table.
"""
import os, sys, bisect, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw')
INT  = os.path.join(HERE, 'data', 'interim')
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

np.random.seed(20260724)  # deterministic randomization inference

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)
def z(s): return (s - s.mean()) / s.std()
def wins(s, p=0.01):
    s = pd.to_numeric(s, errors='coerce'); lo, hi = s.quantile(p), s.quantile(1-p)
    return s.clip(lo, hi)

df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'), parse_dates=['event_date'])
log(f'panel {len(df)} firm-events, {df.permno.nunique()} firms')

# =====================================================================
# T7 -- Heterogeneity of the materiality effect by NEW observable
#   moderators (distinct from t5's size/closure/tech). Each row interacts the
#   standardized relative-layoff ratio with a pre-event, observable moderator;
#   size is always controlled. None is the reserved hand-coded motive.
# =====================================================================
log('T7 heterogeneity by new observable moderators ...')
df['mkt2at'] = df.mktcap / df['at']            # market-to-assets (glamour/growth)
df['turn']   = df.sale / df['at']              # asset turnover (labor-light vs -heavy)
df['is_2022'] = (df.year == 2022).astype(int)  # rate-shock / early-sample year
df['is_goods'] = (((df.sich >= 2000) & (df.sich < 4000)) & (df.is_tech == 0)).astype(int)
df['hi_val']  = (df.mkt2at > df.mkt2at.median()).astype(int)
df['hi_turn'] = (df.turn   > df.turn.median()).astype(int)

def run(formula, data, cluster='permno'):
    yv = formula.split('~')[0].strip()
    rhs = ['z_rel_layoff', 'z_ln_at']
    d = data.dropna(subset=[yv] + [c for c in rhs if c in formula])
    return smf.ols(formula, data=d).fit(cov_type='cluster', cov_kwds={'groups': d[cluster]})

MODS = [
    ('High market-to-assets (glamour)', 'hi_val'),
    ('High asset turnover',             'hi_turn'),
    ('Early sample (2022 event)',       'is_2022'),
    ('Goods-producing (non-tech mfg.)', 'is_goods'),
]
h7 = []
for name, col in MODS:
    f = f'car_0_5 ~ z_rel_layoff*{col} + z_ln_at'
    m = run(f, df)
    inter = f'z_rel_layoff:{col}'
    h7.append({'moderator': name, 'col': col,
               'b_rel': m.params.get('z_rel_layoff', np.nan), 't_rel': m.tvalues.get('z_rel_layoff', np.nan),
               'b_int': m.params.get(inter, np.nan),         't_int': m.tvalues.get(inter, np.nan),
               'b_mod': m.params.get(col, np.nan),           't_mod': m.tvalues.get(col, np.nan),
               'N': int(m.nobs), 'R2': m.rsquared})
    log(f'  {name:34s} rel={h7[-1]["b_rel"]:+.4f}(t={h7[-1]["t_rel"]:+.2f}) '
        f'x={h7[-1]["b_int"]:+.4f}(t={h7[-1]["t_int"]:+.2f})')
t7 = pd.DataFrame(h7); t7.to_csv(os.path.join(OUT, 't7_hetero_ext.csv'), index=False)

# =====================================================================
# T8 -- Randomization inference. Under the sharp null of no cross-sectional
#   relation, the mapping of firm characteristics to events is exchangeable.
#   We permute (i) the materiality regressor z_rel_layoff and (ii) the machine
#   motive indicator is_closure across events 2,000x, refit the same
#   cross-section, and compare the actual slope to the permutation
#   distribution. Design-based p = share of |perm| >= |actual|.
# =====================================================================
log('T8 randomization inference (2000 perms) ...')
NPERM = 2000
d0 = df.dropna(subset=['car_0_5', 'z_rel_layoff', 'z_ln_at']).copy()
# actual slopes (materiality; and closure/motive in the full spec)
m_rel = smf.ols('car_0_5 ~ z_rel_layoff + z_ln_at', data=d0).fit(
    cov_type='cluster', cov_kwds={'groups': d0.permno})
real_rel = m_rel.params['z_rel_layoff']
dcl = df.dropna(subset=['car_0_5', 'z_rel_layoff', 'z_ln_headcount', 'z_ln_at']).copy()
m_cl = smf.ols('car_0_5 ~ z_rel_layoff + z_ln_headcount + z_ln_at + is_closure + is_tech',
               data=dcl).fit(cov_type='cluster', cov_kwds={'groups': dcl.permno})
real_cl = m_cl.params['is_closure']

def perm_slopes(data, yv, permcol, othercols, term, n):
    y = data[yv].values
    base = {c: data[c].values for c in othercols}
    pv = data[permcol].values.copy()
    out = np.empty(n)
    for i in range(n):
        pp = np.random.permutation(pv)
        X = np.column_stack([np.ones(len(y))] + [base[c] for c in othercols] + [pp])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        out[i] = beta[-1]  # coefficient on the permuted column (last)
    return out

perm_rel = perm_slopes(d0, 'car_0_5', 'z_rel_layoff', ['z_ln_at'], 'z_rel_layoff', NPERM)
perm_cl  = perm_slopes(dcl, 'car_0_5', 'is_closure',
                       ['z_rel_layoff', 'z_ln_headcount', 'z_ln_at', 'is_tech'], 'is_closure', NPERM)
p_rel = float(np.mean(np.abs(perm_rel) >= abs(real_rel)))
p_cl  = float(np.mean(np.abs(perm_cl)  >= abs(real_cl)))
ri = pd.DataFrame([
    {'term': 'Rel. layoff (materiality), $z$', 'real': real_rel, 'p_ri': p_rel,
     'q025': np.percentile(perm_rel, 2.5), 'q975': np.percentile(perm_rel, 97.5), 'nperm': NPERM},
    {'term': 'Closure (machine motive proxy)', 'real': real_cl, 'p_ri': p_cl,
     'q025': np.percentile(perm_cl, 2.5), 'q975': np.percentile(perm_cl, 97.5), 'nperm': NPERM},
])
ri.to_csv(os.path.join(OUT, 't8_randinf.csv'), index=False)
log(f'  materiality real={real_rel:+.4f} RI p={p_rel:.4f} 95%[{ri.q025[0]:+.4f},{ri.q975[0]:+.4f}]')
log(f'  closure     real={real_cl:+.4f} RI p={p_cl:.4f} 95%[{ri.q025[1]:+.4f},{ri.q975[1]:+.4f}]')

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(perm_rel, bins=45, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(real_rel, color='crimson', lw=2,
           label=f'Actual slope = {real_rel:+.3f}\n(RI $p$ = {p_rel:.3f})')
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Materiality slope (rel. layoff, $z$) under 2,000 random permutations')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference for the materiality (relative-layoff) effect', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_randinf.pdf')); plt.close(fig)

# =====================================================================
# T9 -- Alternative abnormal-return benchmarks (alternative identification).
#   The base CARs use a firm-specific market model. We re-derive CAR[0,+5]
#   from the raw CRSP daily returns under three alternatives:
#     (a) market-adjusted    AR = ret - vwretd           (beta forced to 1)
#     (b) S&P-500-adjusted   AR = ret - sprtrn
#     (c) mean-adjusted      AR = ret - mean(est-window ret)
#   RECONCILIATION GATE: in the same alignment pass we rebuild the market-model
#   CAR from the stored alpha/beta and require it to match cars.csv car_0_5.
# =====================================================================
log('T9 alternative-benchmark CARs (with reconciliation gate) ...')
cars = pd.read_csv(os.path.join(INT, 'cars.csv'), parse_dates=['event_date'])
dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'), parse_dates=['date'])
dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce'); dsf = dsf.dropna(subset=['ret'])
mkt = pd.read_csv(os.path.join(RAW, 'crsp_market.csv'), parse_dates=['date'])
mkt['vwretd'] = pd.to_numeric(mkt['vwretd'], errors='coerce')
mkt['sprtrn'] = pd.to_numeric(mkt['sprtrn'], errors='coerce')
mkt = mkt.dropna(subset=['vwretd']).sort_values('date').reset_index(drop=True)
cal = list(mkt['date']); cal_pos = {d: i for i, d in enumerate(cal)}
vw = mkt.set_index('date')['vwretd']; sp = mkt.set_index('date')['sprtrn']
ret_by_permno = {p: g[['date', 'ret']] for p, g in dsf.groupby('permno')}

W0, W1 = 0, 5; EST0, EST1 = -252, -46
rows = []
for _, e in cars.iterrows():
    p = int(e.permno); ed = pd.Timestamp(e.event_date)
    if p not in ret_by_permno: continue
    pos = bisect.bisect_left(cal, ed)
    if pos >= len(cal): continue
    g = ret_by_permno[p]; g = g[g.date.isin(cal_pos)]
    if g.empty: continue
    rel = g.date.map(cal_pos).values - pos
    r = g.ret.values; dts = g.date.values
    ev_m = (rel >= W0) & (rel <= W1)
    est_m = (rel >= EST0) & (rel <= EST1)
    if ev_m.sum() == 0 or est_m.sum() < 60: continue
    ev_dts = dts[ev_m]; ev_r = r[ev_m]
    vwr = vw.loc[ev_dts].values.astype(float)
    spr = sp.loc[ev_dts].values.astype(float)
    car_mm  = float(np.sum(ev_r - (e.alpha + e.beta * vwr)))   # rebuilt market-model
    car_madj = float(np.sum(ev_r - vwr))                        # market-adjusted
    car_sp  = float(np.sum(ev_r - spr)) if not np.isnan(spr).any() else np.nan
    car_mean = float(np.sum(ev_r - np.mean(r[est_m])))          # mean-adjusted
    rows.append({'permno': p, 'event_date': ed, 'car_mm_rebuilt': car_mm,
                 'car_madj': car_madj, 'car_sp': car_sp, 'car_mean': car_mean,
                 'car_0_5_stored': e.car_0_5})
alt = pd.DataFrame(rows)
# reconciliation gate
rec = alt.dropna(subset=['car_mm_rebuilt', 'car_0_5_stored'])
maxdiff = float((rec.car_mm_rebuilt - rec.car_0_5_stored).abs().max())
corr = float(rec.car_mm_rebuilt.corr(rec.car_0_5_stored))
log(f'  reconciliation: n={len(rec)} max|diff|={maxdiff:.2e} corr={corr:.6f}')
assert maxdiff < 1e-6, f'market-model CAR did not reconcile (max|diff|={maxdiff}); alignment suspect'
log('  RECONCILED: rebuilt market-model CAR matches cars.csv to 1e-6.')

# merge alt CARs onto the analytical panel (predictors already z-scored)
alt2 = df.merge(alt[['permno', 'event_date', 'car_madj', 'car_sp', 'car_mean']],
                on=['permno', 'event_date'], how='inner')
BENCH = [('Market model (base)', 'car_0_5'),
         ('Market-adjusted ($\\beta{=}1$)', 'car_madj'),
         ('S\\&P 500-adjusted', 'car_sp'),
         ('Mean-adjusted', 'car_mean')]
t9 = []
for name, col in BENCH:
    s = alt2[col].dropna()
    tmean = s.mean() / (s.std() / np.sqrt(len(s)))
    dd = alt2.dropna(subset=[col, 'z_rel_layoff', 'z_ln_at'])
    mm = smf.ols(f'{col} ~ z_rel_layoff + z_ln_at', data=dd).fit(
        cov_type='cluster', cov_kwds={'groups': dd.permno})
    t9.append({'bench': name, 'mean_car': s.mean(), 't_mean': tmean, 'pct_pos': (s > 0).mean(),
               'b_rel': mm.params['z_rel_layoff'], 't_rel': mm.tvalues['z_rel_layoff'],
               'b_size': mm.params['z_ln_at'], 't_size': mm.tvalues['z_ln_at'], 'N': int(mm.nobs)})
    log(f'  {name:30s} meanCAR={s.mean()*100:+.2f}%(t={tmean:+.2f}) '
        f'rel={mm.params["z_rel_layoff"]:+.4f}(t={mm.tvalues["z_rel_layoff"]:+.2f})')
t9d = pd.DataFrame(t9); t9d.to_csv(os.path.join(OUT, 't9_altbench.csv'), index=False)

# =====================================================================
# T10 -- Minimum detectable effects (80% power) on the CAR cross-section.
#   MDE = (z_.975 + z_.80) * SE ~= 2.80 * SE. Reported for the materiality
#   slope (a real effect: small MDE) and for the machine motive (closure)
#   coefficient and the average CAR. Framed HONESTLY: whether the closure null
#   is an informative bound or merely imprecise is read off its MDE, which
#   directly quantifies the value of the student's hand-coded motive.
# =====================================================================
log('T10 minimum detectable effects ...')
Z = 1.959964 + 0.841621
t4 = pd.read_csv(os.path.join(OUT, 't4_crosssec.csv'))
row5 = t4[t4.spec.str.contains('FE')].iloc[0]  # full spec (5)
# SEs backed out from coef/t (robust, firm-clustered) in the full spec
def se_from(coef, tval):
    return abs(coef / tval) if (pd.notna(tval) and tval != 0) else np.nan
items = []
# materiality slope (full spec)
b_rel = float(row5['z_rel_layoff']); se_rel = se_from(b_rel, float(row5['z_rel_layoff_t']))
items.append(('Rel. layoff (materiality), $z$', b_rel, se_rel, 'coef in CAR pts'))
# firm size
b_sz = float(row5['z_ln_at']); se_sz = se_from(b_sz, float(row5['z_ln_at_t']))
items.append(('ln(Assets), $z$', b_sz, se_sz, 'coef in CAR pts'))
# machine motive (closure)
b_cl = float(row5['is_closure']); se_cl = se_from(b_cl, float(row5['is_closure_t']))
items.append(('Closure (machine motive proxy)', b_cl, se_cl, 'coef in CAR pts'))
# average CAR[0,+5] (one-sample)
s = df.car_0_5.dropna(); se_avg = s.std() / np.sqrt(len(s))
items.append(('Average CAR[0,+5]', s.mean(), se_avg, 'mean in CAR pts'))
t10 = []
for lab, coef, se, kind in items:
    mde = Z * se
    t10.append({'term': lab, 'coef': coef, 'se': se, 'mde': mde,
                'coef_pp': coef * 100, 'se_pp': se * 100, 'mde_pp': mde * 100, 'kind': kind})
    log(f'  {lab:34s} coef={coef*100:+.2f}pp SE={se*100:.2f}pp MDE(80%)={mde*100:.2f}pp')
t10d = pd.DataFrame(t10); t10d.to_csv(os.path.join(OUT, 't10_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the four new tables
# =====================================================================
# --- T7 hetero_ext
body = ''
for _, r in t7.iterrows():
    body += (f"{r['moderator']} & {r['b_rel']:+.4f}{stars(r['t_rel'])} ({r['t_rel']:+.2f}) "
             f"& {r['b_int']:+.4f}{stars(r['t_int'])} ({r['t_int']:+.2f}) "
             f"& {r['b_mod']:+.4f}{stars(r['t_mod'])} ({r['t_mod']:+.2f}) & {int(r['N'])} \\\\\n")
w('tab_hetero_ext.tex', r"""\begin{tabular}{lcccc}
\toprule
Moderator $M$ (observable, pre-event) & Rel. layoff ($z$) & Rel.$\times M$ & $M$ & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 randinf
body = ''
for _, r in ri.iterrows():
    body += (f"{r['term']} & {r['real']:+.4f} & [{r['q025']:+.4f}, {r['q975']:+.4f}] "
             f"& {r['p_ri']:.4f} \\\\\n")
w('tab_randinf.tex', r"""\begin{tabular}{lccc}
\toprule
Coefficient (DV $=$ CAR[0,+5]) & Actual & Perm.\ 95\% interval & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 altbench
body = ''
for _, r in t9d.iterrows():
    body += (f"{r['bench']} & {r['mean_car']*100:+.2f} & {r['t_mean']:+.2f}{stars(r['t_mean'])} "
             f"& {r['b_rel']:+.4f}{stars(r['t_rel'])} ({r['t_rel']:+.2f}) "
             f"& {r['b_size']:+.4f}{stars(r['t_size'])} ({r['t_size']:+.2f}) & {int(r['N'])} \\\\\n")
w('tab_altbench.tex', r"""\begin{tabular}{lccccc}
\toprule
Abnormal-return benchmark & Mean CAR (\%) & $t$ & Rel. layoff ($z$) & ln(Assets) ($z$) & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 power
body = ''
for _, r in t10d.iterrows():
    body += (f"{r['term']} & {r['coef_pp']:+.2f} & {r['se_pp']:.2f} & {r['mde_pp']:.2f} \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lccc}
\toprule
Coefficient & Estimate (pp) & SE (pp) & MDE 80\% (pp) \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{
    'ri_p_rel': p_rel, 'ri_p_closure': p_cl,
    'reconciled_maxdiff': maxdiff, 'reconciled_n': len(rec),
    'madj_mean': float(t9d[t9d.bench.str.contains('adjusted', case=False)].iloc[0]['mean_car']),
    'mde_closure_pp': float(t10d[t10d.term.str.contains('Closure')].iloc[0]['mde_pp']),
    'mde_rel_pp': float(t10d[t10d.term.str.contains('Rel')].iloc[0]['mde_pp']),
    'coef_closure_pp': float(t10d[t10d.term.str.contains('Closure')].iloc[0]['coef_pp']),
}]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE -- extension tables t7..t10 + fig3 written.')
logf.close()
print('Extension tables written to', TEX)
