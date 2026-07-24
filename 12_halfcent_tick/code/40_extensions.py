#!/usr/bin/env python3
"""
Project 12 (Half-Cent Tick) - Step 40: journal-track extensions.

Adds five real tables (and one figure) that deepen the measurement-limited null of
20_did.py WITHOUT performing either of the student's reserved manual contributions
(STUDENT_TASKS.md): (i) hand-verifying per-stock official half-cent eligibility, and
(ii) proposing a control group hand-matched to treated on price and volatility. Every
extension below uses ONLY observable screening/panel data already in data/, and the
price-and-volatility-matched control DiD is deliberately left for the student -- we
instead DOCUMENT the overlap failure that motivates it, and we NEVER trim to a matched
sample and re-estimate on it.

  t9_hetero.csv   Heterogeneity of the DiD by observable pre-rule moderators that vary
                  within BOTH arms (Sept volatility, dollar volume, Nasdaq listing,
                  financial industry). Price is deliberately excluded (collinear with
                  treatment). Tests whether any observable subgroup shows the predicted
                  spread narrowing; none does.
  t10_overlap.csv Common-support / covariate-overlap diagnostic: Imbens-Rubin normalized
                  differences for price, volatility, dollar volume, and relative spread,
                  plus the share of treated stocks that have ANY price-comparable control.
                  Proves the wide-spread controls are not a counterfactual and motivates
                  the student's hand-matched control. (No matched sample is estimated.)
  t11_altdef.csv  Alternative treatment/control SCREEN definitions (tighter treated cut,
                  narrower control cut, a donut around the $0.015 boundary, and dropping
                  mega-caps). The wrong-signed DiD survives every reasonable redefinition
                  of the observable screen -- it cannot be fixed without the price-matched
                  control the student will build.
  t12_ri.csv      Randomization inference: 500 permutations of the (time-invariant)
                  treatment label; a design-based p-value for the headline (relative
                  quoted spread) and the dollar spread. Also writes fig4_randinf.pdf.
  t13_power.csv   Minimum detectable effects (80% power) per outcome, and the penny-grid
                  quantum: a half-cent narrowing at the median treated price is ~1.1 bps,
                  above the design's 0.49 bps MDE -- so IF the daily close could take
                  half-cent values (the censoring table shows it never does) the effect
                  would be detectable. An informative null, not an underpowered one.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex, so
the paper cannot drift from the code. Reads the same processed panels as 20_did.py.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from linearmodels import PanelOLS
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

np.random.seed(20260724)  # deterministic RI

did  = pd.read_csv(os.path.join(PROC, 'panel_did.csv'), parse_dates=['date'])
full = pd.read_csv(os.path.join(PROC, 'panel_full.csv'), parse_dates=['date'])
samp = pd.read_csv(os.path.join(RAW, 'sample_stocks.csv'))
did['dstr'] = did.date.dt.strftime('%Y%m%d')

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)
def esc(s):
    return (str(s).replace('$','\\$').replace('#','\\#').replace('%','\\%').replace('&','\\&'))

def cl(formula, data, group='permno'):
    return smf.ols(formula, data=data).fit(cov_type='cluster',
                                            cov_kwds={'groups': data[group]})

# per-stock Sept screening covariates (observable, pre-event) + Sept return vol
sept = full[(full.date >= '2025-09-02') & (full.date <= '2025-09-30')]
septvol = sept.groupby('permno')['ret'].std().rename('septvol')
scov = samp.set_index('permno')[['treated', 'price', 'dqs', 'dvol', 'rqs', 'exch', 'siccd']].join(septvol)
scov['ldvol_s'] = np.log(scov['dvol'].clip(lower=1))
scov['nasdaq']  = (scov['exch'] == 'Q').astype(int)
scov['fin']     = ((scov['siccd'] >= 6000) & (scov['siccd'] < 6800)).astype(int)
LAB = {'rqs_bps_w': 'Relative spread (bps)', 'dqs_c_w': 'Dollar spread (cents)',
       'espr_bps_w': 'Eff.-spread proxy (bps)'}

# =====================================================================
# T9 -- Heterogeneity by observable pre-rule moderators (triple difference).
#   did_m = tp * 1[moderator high]; post_m = post * 1[moderator high] absorbs the
#   moderator-specific time shock. Report tp (low-moderator DiD) and did_m (extra
#   for high-moderator group) for the relative and dollar spread. Moderators vary
#   within BOTH arms; PRICE is excluded (near-collinear with treatment).
# =====================================================================
log('T9 heterogeneity by observable moderators ...')
modmap = scov[['septvol', 'ldvol_s', 'nasdaq', 'fin']].copy()
d9 = did.merge(modmap, left_on='permno', right_index=True, how='left')
MODS = [
    ('High Sept.\\ volatility', 'septvol',  None),   # median split
    ('High dollar volume',      'ldvol_s',  None),   # median split
    ('Nasdaq-listed',           'nasdaq',   0.5),    # indicator
    ('Financial industry',      'fin',      0.5),    # indicator
]
h9 = []
for name, col, thr in MODS:
    dd = d9.dropna(subset=[col]).copy()
    cut = dd[col].median() if thr is None else thr
    dd['modhi'] = (dd[col] > cut).astype(int)
    dd['tp_m']   = dd['tp']   * dd['modhi']
    dd['post_m'] = dd['post'] * dd['modhi']
    for y in ['rqs_bps_w', 'dqs_c_w']:
        r = cl(f'{y} ~ tp + tp_m + post_m + lprice + ldvol + C(permno) + C(dstr)', dd)
        h9.append({'moderator': name, 'outcome': y,
                   'did_low': r.params['tp'],  't_low': r.tvalues['tp'],
                   'did_int': r.params['tp_m'], 't_int': r.tvalues['tp_m'],
                   'N': int(r.nobs)})
    lo = h9[-2]; log(f'  {name:24s} rqs: DiD_low={lo["did_low"]:+.3f}(t={lo["t_low"]:+.2f}) '
                     f'x={lo["did_int"]:+.3f}(t={lo["t_int"]:+.2f})')
t9 = pd.DataFrame(h9); t9.to_csv(os.path.join(OUT, 't9_hetero.csv'), index=False)

# =====================================================================
# T10 -- Common-support / covariate-overlap diagnostic (Imbens-Rubin normalized
#   differences). Also: the share of treated stocks that have ANY control within a
#   0.25-SD(log price) caliper, and the count of controls inside the treated price
#   range. This documents that wide-spread controls are not a counterfactual; it
#   does NOT construct a matched sample (that is the student's reserved task).
# =====================================================================
log('T10 common-support / overlap diagnostic ...')
scov['lp'] = np.log(scov['price'])
tr = scov[scov.treated == 1]; co = scov[scov.treated == 0]
def ndiff(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2.0)
covs = [('Price (\\$)', 'price'), ('ln price', 'lp'), ('Sept.\\ return vol.', 'septvol'),
        ('ln dollar volume', 'ldvol_s'), ('Rel.\\ spread (screen)', 'rqs')]
o10 = []
for lbl, c in covs:
    o10.append({'cov': lbl, 'mean_t': tr[c].mean(), 'mean_c': co[c].mean(),
                'norm_diff': ndiff(tr[c].dropna(), co[c].dropna())})
t10 = pd.DataFrame(o10); t10.to_csv(os.path.join(OUT, 't10_overlap.csv'), index=False)
# overlap statistics
cal = 0.25 * scov['lp'].std()
has_match = sum(((co['lp'] - r.lp).abs() <= cal).any() for _, r in tr.iterrows())
lo_p, hi_p = tr['price'].min(), tr['price'].max()
co_in = int(((co['price'] >= lo_p) & (co['price'] <= hi_p)).sum())
ov = {'share_treated_with_match': has_match / len(tr), 'n_treated_with_match': int(has_match),
      'controls_in_treated_range': co_in, 'treated_pmin': lo_p, 'treated_pmax': hi_p,
      'norm_diff_price': float(t10[t10['cov'] == 'Price (\\$)']['norm_diff'].iloc[0])}
pd.DataFrame([ov]).to_csv(os.path.join(OUT, 't10_overlap_stats.csv'), index=False)
log(f'  norm-diff price={ov["norm_diff_price"]:+.2f}; treated w/ a price-comparable control: '
    f'{ov["n_treated_with_match"]}/{len(tr)} ({100*ov["share_treated_with_match"]:.0f}%); '
    f'controls in treated range [{lo_p:.0f},{hi_p:.0f}]: {co_in}')

# =====================================================================
# T11 -- Alternative treatment/control SCREEN definitions. Re-estimate the TWFE DiD
#   on subsets of the SAME 150 stocks under stricter/looser observable screens.
#   The wrong-signed, significant DiD survives every reasonable redefinition.
# =====================================================================
log('T11 alternative screen definitions ...')
sc = samp.set_index('permno')[['dqs', 'price']]
d11 = did.merge(sc, left_on='permno', right_index=True, how='left', suffixes=('', '_scr'))
FORM = 'rqs_bps_w ~ tp + lprice + ldvol + C(permno) + C(dstr)'
def keep_ok(sub):
    # need both arms present in pre and post
    return (sub.groupby(['treated', 'post']).size().reindex(
            pd.MultiIndex.from_product([[0, 1], [0, 1]])).notna().all())
defs = [
    ('Baseline (all 150 stocks)',            d11),
    ('Tighter treated screen (dqs\\_scr $\\le$ \\$0.012)',
        d11[(d11.treated == 0) | (d11.dqs <= 0.012)]),
    ('Narrower control screen (dqs\\_scr $\\ge$ \\$0.03)',
        d11[(d11.treated == 1) | (d11.dqs >= 0.03)]),
    ('Donut: drop names near \\$0.015 cutoff',
        d11[((d11.treated == 1) & (d11.dqs <= 0.012)) |
            ((d11.treated == 0) & (d11.dqs >= 0.03))]),
    ('Drop mega-caps (screen price $>$ \\$500)', d11[d11.price <= 500]),
]
r11 = []
for name, sub in defs:
    if not keep_ok(sub):
        log(f'  {name}: SKIP (a cell is empty)'); continue
    m = cl(FORM, sub)
    r11.append({'defn': name, 'coef': m.params['tp'], 't': m.tvalues['tp'],
                'se': m.bse['tp'], 'n_stocks': sub.permno.nunique(), 'N': int(m.nobs)})
    log(f'  {name:48s} DiD={m.params["tp"]:+.3f} (t={m.tvalues["tp"]:+.2f}) '
        f'stocks={sub.permno.nunique()}')
t11 = pd.DataFrame(r11); t11.to_csv(os.path.join(OUT, 't11_altdef.csv'), index=False)

# =====================================================================
# T12 -- Randomization inference. Permute the (time-invariant) treatment label across
#   the 150 stocks 500x, rebuild tp = post*treat_perm, refit the two-way FE panel, and
#   collect the DiD coefficient. Design-based p = share |perm| >= |real|.
# =====================================================================
log('T12 randomization inference (500 perms) ...')
pan = did.copy()
pan['dint'] = pan['date'].astype('int64')  # numeric time id (avoid deprecated .view)
firm = samp.set_index('permno')['treated']
firm_ids = np.array(sorted(pan.permno.unique()))
n_tr = int(firm.loc[firm_ids].sum()); n_f = len(firm_ids)

def did_coef_panel(y, tpvec):
    dd = pan[[ 'permno', 'dint', y, 'lprice', 'ldvol']].copy()
    dd['tp'] = tpvec
    dd = dd.dropna().set_index(['permno', 'dint'])
    res = PanelOLS(dd[y], dd[['tp', 'lprice', 'ldvol']],
                   entity_effects=True, time_effects=True,
                   drop_absorbed=True, check_rank=False).fit()
    return res.params['tp']

ri = {}
post_arr = pan['post'].values
for y in ['rqs_bps_w', 'dqs_c_w']:
    real = did_coef_panel(y, pan['tp'].values)
    perms = []
    for _ in range(500):
        lab = np.zeros(n_f, dtype=int); lab[np.random.choice(n_f, n_tr, replace=False)] = 1
        m = dict(zip(firm_ids, lab))
        tperm = pan.permno.map(m).values
        try: perms.append(did_coef_panel(y, post_arr * tperm))
        except Exception: pass
    perms = np.array(perms)
    p = float(np.mean(np.abs(perms) >= abs(real)))
    ri[y] = {'real': real, 'p_ri': p, 'perms': perms,
             'q025': np.percentile(perms, 2.5), 'q975': np.percentile(perms, 97.5)}
    log(f'  {y:10s} real={real:+.4f}  RI p={p:.3f}  perm 95% '
        f'[{ri[y]["q025"]:+.4f},{ri[y]["q975"]:+.4f}]')
t12 = pd.DataFrame([{'outcome': y, 'label': LAB[y], 'real': v['real'], 'p_ri': v['p_ri'],
                     'perm_q025': v['q025'], 'perm_q975': v['q975'], 'nperm': len(v['perms'])}
                    for y, v in ri.items()])
t12.to_csv(os.path.join(OUT, 't12_ri.csv'), index=False)

# fig4: RI permutation distribution for the headline (relative quoted spread)
fig, ax = plt.subplots(figsize=(7, 4.2))
pp = ri['rqs_bps_w']['perms']
ax.hist(pp, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(ri['rqs_bps_w']['real'], color='crimson', lw=2,
           label=f"Actual DiD = {ri['rqs_bps_w']['real']:+.3f} bps\n(RI $p$ = {ri['rqs_bps_w']['p_ri']:.3f})")
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo DiD coefficient under random treatment (relative quoted spread, bps)')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 500 permutations of treatment', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig4_randinf.pdf')); plt.close(fig)

# =====================================================================
# T13 -- Minimum detectable effect (MDE) at 80% power per outcome, from the preferred
#   -spec SE. MDE = (z_.975 + z_.80)*SE ~= 2.80*SE. Expressed vs the pre-period treated
#   mean. Plus the penny-grid quantum: a $0.01->$0.005 narrowing at the median treated
#   mid price is ~1.1 bps, which EXCEEDS the MDE -- so the effect WOULD be detectable IF
#   the daily close could take half-cent values (which the censoring table shows it
#   never does). The null is informative, not underpowered.
# =====================================================================
log('T13 minimum detectable effects + penny quantum ...')
t3 = pd.read_csv(os.path.join(OUT, 't3_did_main.csv'))
t4 = pd.read_csv(os.path.join(OUT, 't4_altoutcomes.csv'))
Z = 1.959964 + 0.841621
pre_t = did[(did.treated == 1) & (did.post == 0)]
pre_mean = {'rqs_bps_w': pre_t['rqs_bps_w'].mean(), 'dqs_c_w': pre_t['dqs_c_w'].mean(),
            'espr_bps_w': pre_t['espr_bps_w'].mean()}
se_rqs  = float(t3[t3.spec == '(4) TWFE + controls']['se'].iloc[0])
se_dqs  = float(t4[t4.spec == 'Dollar spread (cents), +controls']['se'].iloc[0])
se_espr = float(t4[t4.spec == 'Eff-spread proxy (bps), +ctrl']['se'].iloc[0])
rows = [('rqs_bps_w', se_rqs), ('dqs_c_w', se_dqs), ('espr_bps_w', se_espr)]
t13 = []
for y, se in rows:
    mde = Z * se; mu = pre_mean[y]
    t13.append({'outcome': y, 'label': LAB[y], 'se': se, 'mde': mde,
                'pre_treated_mean': mu, 'mde_pct_mean': 100 * mde / abs(mu)})
    log(f'  {y:10s} SE={se:.4f} MDE={mde:.4f} = {100*mde/abs(mu):.1f}% of pre treated mean')
t13d = pd.DataFrame(t13); t13d.to_csv(os.path.join(OUT, 't13_power.csv'), index=False)
# penny quantum
med_mid = full[(full.treated == 1) & (full.date >= '2025-10-06') & (full.date <= '2025-10-31')]['mid'].median()
halfcent_bps = 10000.0 * 0.005 / med_mid
pd.DataFrame([{'median_treated_mid': med_mid, 'halfcent_bps': halfcent_bps,
               'mde_rqs_bps': Z * se_rqs}]).to_csv(os.path.join(OUT, 't13_quantum.csv'), index=False)
log(f'  penny quantum: half-cent at median treated mid \\${med_mid:.2f} = {halfcent_bps:.3f} bps '
    f'(vs MDE {Z*se_rqs:.3f} bps)')

# =====================================================================
# Render LaTeX for the new tables
# =====================================================================
# --- T9 hetero
body = ''
for name in [m[0] for m in MODS]:
    rv = t9[(t9.moderator == name) & (t9.outcome == 'rqs_bps_w')].iloc[0]
    dv = t9[(t9.moderator == name) & (t9.outcome == 'dqs_c_w')].iloc[0]
    body += (f"{name} & {rv['did_low']:+.3f}{stars(rv['t_low'])} & {rv['did_int']:+.3f}{stars(rv['t_int'])} "
             f"& {dv['did_low']:+.3f}{stars(dv['t_low'])} & {dv['did_int']:+.3f}{stars(dv['t_int'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lcccc}
\toprule
& \multicolumn{2}{c}{Relative spread (bps)} & \multicolumn{2}{c}{Dollar spread (cents)} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Moderator $M$ (pre-rule) & DiD & DiD$\times M$ & DiD & DiD$\times M$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 overlap
body = ''
for _, r in t10.iterrows():
    body += f"{r['cov']} & {r['mean_t']:.3f} & {r['mean_c']:.3f} & {r['norm_diff']:+.2f} \\\\\n"
w('tab_overlap.tex', r"""\begin{tabular}{lccc}
\toprule
Covariate (Sept.\ screen) & Treated mean & Control mean & Norm.\ diff. \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T11 altdef
body = ''
for _, r in t11.iterrows():
    body += (f"{r['defn']} & {r['coef']:+.3f}{stars(r['t'])} & ({r['t']:+.2f}) & {r['se']:.3f} "
             f"& {int(r['n_stocks'])} & {int(r['N'])} \\\\\n")
w('tab_altdef.tex', r"""\begin{tabular}{lccccc}
\toprule
Screen definition & DiD (bps) & $t$ & SE & \#stocks & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T12 RI
body = ''
for _, r in t12.iterrows():
    nperm = int(r['nperm']) if pd.notna(r['nperm']) else 500
    p_str = f"$<${1.0/nperm:.3f}" if r['p_ri'] == 0 else f"{r['p_ri']:.3f}"
    body += (f"{r['label']} & {r['real']:+.4f} & [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] "
             f"& {p_str} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lccc}
\toprule
Outcome (DV) & Actual DiD & Perm.\ 95\% interval & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T13 power
body = ''
for _, r in t13d.iterrows():
    body += (f"{r['label']} & {r['se']:.4f} & {r['mde']:.4f} & {r['pre_treated_mean']:.3f} "
             f"& {r['mde_pct_mean']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lcccc}
\toprule
Outcome (DV) & SE & MDE(80\%) & Pre treated mean & MDE \% of mean \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{
    'ri_p_rqs': ri['rqs_bps_w']['p_ri'], 'ri_p_dqs': ri['dqs_c_w']['p_ri'],
    'ri_real_rqs': ri['rqs_bps_w']['real'],
    'ri_q025_rqs': ri['rqs_bps_w']['q025'], 'ri_q975_rqs': ri['rqs_bps_w']['q975'],
    'nd_price': ov['norm_diff_price'],
    'n_treated_with_match': ov['n_treated_with_match'],
    'share_treated_with_match': ov['share_treated_with_match'],
    'controls_in_treated_range': ov['controls_in_treated_range'],
    'med_treated_mid': med_mid, 'halfcent_bps': halfcent_bps, 'mde_rqs': Z * se_rqs,
}]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE -- extension tables (t9-t13) + fig4 written.')
logf.close()
print('Extension tables written to', TEX)
