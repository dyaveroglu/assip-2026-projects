#!/usr/bin/env python3
"""
Project 10 (SVB) — Step 40: journal-track extensions.

Adds four NEW real tables (plus two supporting tables and a figure) that deepen
the cross-sectional event study without touching the student's reserved
hand-collection (STUDENT_TASKS.md): the hand-corrected multi-bank uninsured
aggregation (Task 2), the news/confound flags (Task 4), and the actual
deposit-run outcome (Task 5). Everything here uses OBSERVABLE 2022Q4
balance-sheet data and the market-model CARs only.

  t6_hetero.csv    Heterogeneity of the uninsured (run) and securities (MTM)
                   channels by observable moderators (size, securities loss,
                   HTM loss, thrift charter).
  t7_matched.csv   Matching estimator: high- vs low-uninsured banks matched on
                   size + securities loss; a design that does not impose the
                   linear functional form. + balance table t7_balance.csv.
  t8_ri.csv        Randomization inference: permute uninsured (and securities)
                   exposure across banks 2000x; design-based p-values for the
                   two channel coefficients. Writes fig3_randinf.pdf.
  t8_placebo.csv   Pre-event-window falsification: the same horse race with the
                   [-6,-2] placebo CAR as the dependent variable.
  t9_power.csv     Minimum detectable effects (80% power) per predictor: shows
                   the securities-loss null is informative, not underpowered.

Also renders tab_corr.tex and tab_robust.tex from the existing t2/t5 CSVs so the
Data and Robustness sections have dedicated tables. Every number is written to
output/tables/*.csv and rendered to paper/tables/*.tex; the paper cannot drift.
Reads the same processed panel as 20_regressions.py.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))
df['thrift'] = df.inst_type.astype(str).str.contains('Thrift').astype(int)
log(f'panel: {len(df)} banks; uninsured nonnull={df.uninsured_ratio.notna().sum()}; '
    f'thrifts={int(df.thrift.sum())}')

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)
def ols(formula, data):
    return smf.ols(formula, data=data).fit(cov_type='HC1')

CTRL = 'z_size'
LAB = {'z_uninsured_ratio':'Uninsured deposits / Assets',
       'z_sec_loss_eq':'Securities unreal.\\ loss / Equity',
       'z_htm_loss_eq':'HTM unreal.\\ loss / Equity',
       'z_size':'ln(Assets)'}

# =====================================================================
# T6 — Heterogeneity by OBSERVABLE moderators.
#   For each moderator M (indicator, fixed at observable 2022Q4 values), fit
#     car_0_3 ~ unins + unins:M + sec + sec:M + size
#   and report the run-channel (uninsured) and MTM-channel (securities) base
#   coefficient (low-M group) and interaction (extra effect for high-M group).
#   Moderators are chosen to be observable and orthogonal to the reserved
#   hand-collected variables.
# =====================================================================
log('T6 heterogeneity by observable moderators ...')
MODS = [
    ('Large bank (above-median assets)', 'z_size'),
    ('High securities loss (above-median)', 'z_sec_loss_eq'),
    ('High HTM loss (above-median)', 'z_htm_loss_eq'),
    ('Thrift holding company', 'thrift'),
]
h6 = []
base = df.dropna(subset=['car_0_3', 'z_uninsured_ratio', 'z_sec_loss_eq', 'z_size']).copy()
for name, col in MODS:
    d = base.copy()
    if col == 'thrift':
        d['M'] = d['thrift']
    else:
        d['M'] = (d[col] > d[col].median()).astype(int)
    d['unins_M'] = d['z_uninsured_ratio'] * d['M']
    d['sec_M']   = d['z_sec_loss_eq'] * d['M']
    m = ols('car_0_3 ~ z_uninsured_ratio + unins_M + z_sec_loss_eq + sec_M + z_size + M', d)
    h6.append({'moderator': name,
               'unins_base': m.params['z_uninsured_ratio'], 'unins_base_t': m.tvalues['z_uninsured_ratio'],
               'unins_int':  m.params['unins_M'],          'unins_int_t':  m.tvalues['unins_M'],
               'sec_base':   m.params['z_sec_loss_eq'],    'sec_base_t':   m.tvalues['z_sec_loss_eq'],
               'sec_int':    m.params['sec_M'],            'sec_int_t':    m.tvalues['sec_M'],
               'N': int(m.nobs)})
    log(f'  {name:36s} unins={m.params["z_uninsured_ratio"]:+.4f}(t={m.tvalues["z_uninsured_ratio"]:+.2f}) '
        f'x={m.params["unins_M"]:+.4f}(t={m.tvalues["unins_M"]:+.2f})')
t6 = pd.DataFrame(h6); t6.to_csv(os.path.join(OUT, 't6_hetero.csv'), index=False)

# =====================================================================
# T7 — Matching estimator (alternative identification).
#   Treatment = above-median uninsured ratio. Nearest-neighbor 1:1 match each
#   high-uninsured bank to a low-uninsured bank on standardized (size, sec_loss)
#   Euclidean distance, no replacement, caliper 0.5 SD. Compare mean CAR[0,+3];
#   this ATT does not impose the linear form. Placebo window as a check.
# =====================================================================
log('T7 matching estimator ...')
mm = df.dropna(subset=['car_0_3', 'z_uninsured_ratio', 'z_sec_loss_eq', 'z_size', 'car_pre']).copy()
med = mm['z_uninsured_ratio'].median()
mm['hi'] = (mm['z_uninsured_ratio'] > med).astype(int)
hi = mm[mm.hi == 1].copy(); lo = mm[mm.hi == 0].copy()
caliper = 0.5
used = set(); pairs = []
for _, r in hi.sort_values('z_uninsured_ratio', ascending=False).iterrows():
    pool = lo[~lo.permno.isin(used)]
    if pool.empty: break
    dist = np.sqrt((pool['z_size'] - r['z_size'])**2 + (pool['z_sec_loss_eq'] - r['z_sec_loss_eq'])**2)
    j = dist.idxmin()
    if dist.loc[j] <= caliper:
        used.add(lo.loc[j, 'permno'])
        pairs.append((r['permno'], lo.loc[j, 'permno']))
hi_ids = [a for a, _ in pairs]; lo_ids = [b for _, b in pairs]
mh = mm[mm.permno.isin(hi_ids)]; ml = mm[mm.permno.isin(lo_ids)]
log(f'  matched pairs: {len(pairs)}')

def diff_se(a, b):
    # two-sample difference in means with unequal-variance (Welch) SE
    da, db = a.dropna(), b.dropna()
    d = da.mean() - db.mean()
    se = np.sqrt(da.var(ddof=1)/len(da) + db.var(ddof=1)/len(db))
    return d, se, d/se

rows7 = []
# raw (unmatched) high-vs-low difference
d, se, t = diff_se(hi['car_0_3'], lo['car_0_3'])
rows7.append({'row':'Raw difference (all banks)', 'window':'[0,+3]', 'diff':d, 'se':se, 't':t,
              'n_hi':len(hi), 'n_lo':len(lo)})
# matched difference, event window
d, se, t = diff_se(mh['car_0_3'], ml['car_0_3'])
rows7.append({'row':'Matched difference', 'window':'[0,+3]', 'diff':d, 'se':se, 't':t,
              'n_hi':len(mh), 'n_lo':len(ml)})
# matched difference, placebo window
d, se, t = diff_se(mh['car_pre'], ml['car_pre'])
rows7.append({'row':'Matched difference (placebo)', 'window':'[-6,-2]', 'diff':d, 'se':se, 't':t,
              'n_hi':len(mh), 'n_lo':len(ml)})
t7 = pd.DataFrame(rows7); t7.to_csv(os.path.join(OUT, 't7_matched.csv'), index=False)
for _, r in t7.iterrows():
    log(f'  {r["row"]:30s} {r["window"]:8s} diff={r["diff"]:+.4f} se={r["se"]:.4f} t={r["t"]:+.2f}')

# balance: standardized mean differences on matching covariates, pre vs post
bal = []
for col, lab in [('z_size', 'ln(Assets)'), ('z_sec_loss_eq', 'Securities loss/Equity'),
                 ('z_htm_loss_eq', 'HTM loss/Equity')]:
    pre = hi[col].mean() - lo[col].mean()
    post = mh[col].mean() - ml[col].mean()
    bal.append({'covariate': lab, 'gap_pre': pre, 'gap_post': post})
t7b = pd.DataFrame(bal); t7b.to_csv(os.path.join(OUT, 't7_balance.csv'), index=False)
log('  balance (std. mean diff hi-lo):\n' + t7b.round(3).to_string(index=False))

# =====================================================================
# T8 — Randomization inference. Permute the (predetermined) exposure across
#   banks; refit the horse race; compare the actual coefficient to the
#   permutation distribution. Design-based p = share |perm| >= |real|.
# =====================================================================
log('T8 randomization inference (2000 perms) ...')
ri_df = df.dropna(subset=['car_0_3', 'z_uninsured_ratio', 'z_sec_loss_eq', 'z_size']).copy()
NPERM = 2000
def coef(dat, key):
    return ols('car_0_3 ~ z_uninsured_ratio + z_sec_loss_eq + z_size', dat).params[key]
ri = {}
for key in ['z_uninsured_ratio', 'z_sec_loss_eq']:
    real = coef(ri_df, key)
    perms = np.empty(NPERM)
    vals = ri_df[key].values.copy()
    for i in range(NPERM):
        d = ri_df.copy()
        d[key] = np.random.permutation(vals)
        perms[i] = ols('car_0_3 ~ z_uninsured_ratio + z_sec_loss_eq + z_size', d).params[key]
    p = float(np.mean(np.abs(perms) >= abs(real)))
    ri[key] = {'real': real, 'p': p, 'perms': perms,
               'q025': np.percentile(perms, 2.5), 'q975': np.percentile(perms, 97.5)}
    log(f'  {key:20s} real={real:+.4f} RI p={p:.4f} perm95%[{ri[key]["q025"]:+.4f},{ri[key]["q975"]:+.4f}]')
t8 = pd.DataFrame([{'predictor': LAB[k], 'real': v['real'], 'p_ri': v['p'],
                    'perm_q025': v['q025'], 'perm_q975': v['q975'], 'nperm': NPERM}
                   for k, v in ri.items()])
t8.to_csv(os.path.join(OUT, 't8_ri.csv'), index=False)

# fig3: RI permutation distribution for the uninsured (run) channel
fig, ax = plt.subplots(figsize=(7, 4.2))
pp = ri['z_uninsured_ratio']['perms']
ax.hist(pp, bins=45, color='0.78', edgecolor='0.4', linewidth=0.4)
ax.axvline(ri['z_uninsured_ratio']['real'], color='crimson', lw=2,
           label=f"Actual coef.\\ = {ri['z_uninsured_ratio']['real']:+.3f}\n(RI $p$ = {ri['z_uninsured_ratio']['p']:.3f})")
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo uninsured coefficient under permuted exposure (CAR[0,+3])')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 2000 permutations of uninsured exposure', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_randinf.pdf')); plt.close(fig)

# =====================================================================
# T8b — Pre-event placebo-window falsification. The uninsured gradient should
#   be absent BEFORE the run week even though the pre-window mean CAR is
#   negative (Silvergate). Same horse race with car_pre as the DV.
# =====================================================================
log('T8b placebo-window falsification ...')
pw = df.dropna(subset=['car_pre', 'z_uninsured_ratio', 'z_sec_loss_eq', 'z_size']).copy()
mpl = ols('car_pre ~ z_uninsured_ratio + z_sec_loss_eq + z_size', pw)
pl_rows = []
for k in ['z_uninsured_ratio', 'z_sec_loss_eq', 'z_size']:
    pl_rows.append({'predictor': LAB[k], 'coef': mpl.params[k], 't': mpl.tvalues[k]})
t8b = pd.DataFrame(pl_rows); t8b.to_csv(os.path.join(OUT, 't8_placebo.csv'), index=False)
log('  placebo-window coefs:\n' + t8b.round(4).to_string(index=False) +
    f'\n  (N={int(mpl.nobs)}, R2={mpl.rsquared:.3f})')
pl_meta = {'N': int(mpl.nobs), 'R2': mpl.rsquared}

# =====================================================================
# T9 — Minimum detectable effect (MDE) at 80% power per predictor from the
#   preferred horse race (col 4). MDE = (z_.975 + z_.80) * SE ~= 2.80 * SE.
#   Expressed in CAR points, as % of the CAR[0,+3] SD, and relative to the
#   estimated uninsured (run-channel) effect. Shows the securities-loss null
#   is informative: an effect the size of the run channel would be detected.
# =====================================================================
log('T9 minimum detectable effects ...')
m4 = ols('car_0_3 ~ z_uninsured_ratio + z_sec_loss_eq + z_size', ri_df)
Z = 1.959964 + 0.841621
car_sd = ri_df['car_0_3'].std()
unins_eff = abs(m4.params['z_uninsured_ratio'])
t9 = []
for k in ['z_uninsured_ratio', 'z_sec_loss_eq', 'z_size']:
    se = m4.bse[k]; c = m4.params[k]; mde = Z * se
    t9.append({'predictor': LAB[k], 'coef': c, 'se': se, 'mde': mde,
               'mde_pct_carsd': 100 * mde / car_sd,
               'mde_vs_unins': mde / unins_eff})
    log(f'  {k:20s} coef={c:+.4f} SE={se:.4f} MDE={mde:.4f} '
        f'({100*mde/car_sd:.1f}% of CAR SD; {mde/unins_eff:.2f}x the run effect)')
t9d = pd.DataFrame(t9); t9d.to_csv(os.path.join(OUT, 't9_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the new tables
# =====================================================================
# --- T6 hetero
body = ''
for _, r in t6.iterrows():
    body += (f"{r['moderator']} & {r['unins_base']:+.4f}{stars(r['unins_base_t'])} "
             f"& {r['unins_int']:+.4f}{stars(r['unins_int_t'])} "
             f"& {r['sec_base']:+.4f}{stars(r['sec_base_t'])} "
             f"& {r['sec_int']:+.4f}{stars(r['sec_int_t'])} & {r['N']:.0f} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lccccc}
\toprule
& \multicolumn{2}{c}{Run channel (uninsured)} & \multicolumn{2}{c}{MTM channel (securities)} & \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Moderator $M$ (2022Q4) & Base & $\times\,M$ & Base & $\times\,M$ & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T7 matched + balance
body = ''
for _, r in t7.iterrows():
    body += (f"{r['row']} & {r['window']} & {r['diff']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) "
             f"& {r['n_hi']:.0f}/{r['n_lo']:.0f} \\\\\n")
balbody = ''
for _, r in t7b.iterrows():
    balbody += f"\\quad {r['covariate']} & {r['gap_pre']:+.3f} & {r['gap_post']:+.3f} \\\\\n"
w('tab_matched.tex', r"""\begin{tabular}{llccc}
\toprule
Comparison & Window & Diff.\ in CAR & $t$-stat & $N_{hi}/N_{lo}$ \\
\midrule
""" + body + r"""\midrule
\multicolumn{5}{l}{\textit{Covariate balance (std.\ mean diff., high$-$low uninsured):}} \\
& & Pre-match & Post-match & \\
""" + ''.join(f"\\quad {r['covariate']} & & {r['gap_pre']:+.3f} & {r['gap_post']:+.3f} & \\\\\n"
              for _, r in t7b.iterrows()) + r"""\bottomrule
\end{tabular}""")

# --- T8 RI
body = ''
for _, r in t8.iterrows():
    body += (f"{r['predictor']} & {r['real']:+.4f} & [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] "
             f"& {r['p_ri']:.4f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lccc}
\toprule
Predictor (DV $=$ CAR[0,+3]) & Actual coef. & Perm.\ 95\% interval & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8b placebo
body = ''
for _, r in t8b.iterrows():
    body += f"{r['predictor']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) \\\\\n"
w('tab_placebo.tex', r"""\begin{tabular}{lcc}
\toprule
Predictor (DV $=$ placebo CAR[$-6,-2$]) & Coef. & $t$-stat \\
\midrule
""" + body + r"""\midrule
Observations & \multicolumn{2}{c}{""" + f"{pl_meta['N']}" + r"""} \\
$R^2$ & \multicolumn{2}{c}{""" + f"{pl_meta['R2']:.3f}" + r"""} \\
\bottomrule
\end{tabular}""")

# --- T9 power
body = ''
for _, r in t9d.iterrows():
    body += (f"{r['predictor']} & {r['coef']:+.4f} & {r['se']:.4f} & {r['mde']:.4f} "
             f"& {r['mde_pct_carsd']:.1f}\\% & {r['mde_vs_unins']:.2f}$\\times$ \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lccccc}
\toprule
Predictor & Coef. & SE & MDE(80\%) & \% of CAR SD & vs.\ run effect \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- also render correlations (t2) and robustness (t5) for Data/Robustness sections
t2c = pd.read_csv(os.path.join(OUT, 't2_corr.csv'), index_col=0)
clab = {'car_0_3':'CAR[0,+3]', 'uninsured_ratio':'Uninsured/Assets',
        'sec_loss_eq':'Sec.\\ loss/Eq.', 'htm_loss_eq':'HTM loss/Eq.', 'size':'ln(Assets)'}
cols = list(t2c.columns)
head = ' & '.join(f'({i+1})' for i in range(len(cols)))
body = ''
for i, (idx, row) in enumerate(t2c.iterrows()):
    cells = ' & '.join(f"{row[c]:.3f}" if j <= i else '' for j, c in enumerate(cols))
    body += f"({i+1}) {clab.get(idx, idx)} & {cells} \\\\\n"
w('tab_corr.tex', r"""\begin{tabular}{l""" + 'c'*len(cols) + r"""}
\toprule
& """ + head + r""" \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

t5 = pd.read_csv(os.path.join(OUT, 't5_robust.csv'))
labels5 = [('z_uninsured_ratio','Uninsured / Assets'), ('z_sec_loss_eq','Securities loss / Equity'),
           ('z_htm_loss_eq','HTM loss / Equity'), ('z_size','ln(Assets)')]
head = ' & '.join('\\multicolumn{1}{c}{'+s+'}' for s in t5['spec'])
body = ''
for key, lab in labels5:
    coefs, ts = '', ''
    for _, r in t5.iterrows():
        if key in r and pd.notna(r[key]):
            coefs += f" & {r[key]:.4f}{stars(r[key+'_t'])}"; ts += f" & ({r[key+'_t']:.2f})"
        else:
            coefs += ' & '; ts += ' & '
    body += f"{lab}{coefs} \\\\\n{ts} \\\\[3pt]\n"
nrow = ' & '.join(f"{int(r['N'])}" for _, r in t5.iterrows())
r2row = ' & '.join(f"{r['R2']:.3f}" for _, r in t5.iterrows())
w('tab_robust.tex', r"""\begin{tabular}{l""" + 'c'*len(t5) + r"""}
\toprule
& """ + head + r""" \\
\cmidrule(lr){2-""" + str(len(t5)+1) + r"""}
""" + body + r"""\midrule
Observations & """ + nrow + r""" \\
$R^2$ & """ + r2row + r""" \\
\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{
    'npairs': len(pairs),
    'match_diff': float(t7[t7.row=='Matched difference']['diff'].iloc[0]),
    'match_t': float(t7[t7.row=='Matched difference']['t'].iloc[0]),
    'raw_diff': float(t7[t7.row=='Raw difference (all banks)']['diff'].iloc[0]),
    'ri_p_unins': ri['z_uninsured_ratio']['p'], 'ri_p_sec': ri['z_sec_loss_eq']['p'],
    'placebo_unins_t': float(t8b[t8b.predictor==LAB['z_uninsured_ratio']]['t'].iloc[0]),
    'mde_sec': float(t9d[t9d.predictor==LAB['z_sec_loss_eq']]['mde'].iloc[0]),
    'mde_sec_vs_unins': float(t9d[t9d.predictor==LAB['z_sec_loss_eq']]['mde_vs_unins'].iloc[0]),
}]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE — extension tables (t6-t9), placebo, corr/robust renders, fig3 written.')
logf.close()
print('Extension tables written to', TEX)
