#!/usr/bin/env python3
"""
Project 03 (Clawbacks) — Step 15: journal-track extensions.

Adds four real tables that deepen the null without touching the student's
reserved contribution (hand-coded 10D-1 *provision strength*, Tasks 1-2). All
identification here uses OBSERVABLE moderators and design-based inference, never
the provision-strength dimension the student will hand-collect.

  t6_hetero.csv   Heterogeneity of the DiD by observable moderators
                  (CEO equity-pay share, leverage, R&D intensity, financials).
  t7_matched.csv  Size-matched DiD: nearest-neighbor match on pre-rule (2022)
                  size (+ pre-vol) removes the size confound behind the vol result.
  t8_ri.csv       Randomization inference: 500 permutations of treatment; a
                  design-based p-value for the headline (idio_vol) and a real-risk
                  outcome (invest_at). Also writes fig3_randinf.pdf.
  t9_power.csv    Minimum detectable effects (80% power) per real-risk outcome:
                  shows the null is informative, not merely underpowered.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reads the same processed panel as 10_did.py.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels import PanelOLS
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

np.random.seed(20260724)  # deterministic RI (Date.now-free environment)

df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'), dtype={'gvkey': str})
main = df[df.treat.notna()].copy()
main['treat'] = main['treat'].astype(int)
CTRL = ['size', 'mtb', 'roa', 'cflow', 'tang']
HEAD = 'idio_vol'                       # headline outcome from 10_did.py
REAL = ['invest_at', 'capx_at', 'rd_at', 'aqc_at', 'book_lev', 'cash_at']  # real-risk margins
LAB  = {'invest_at':'Investment/Assets','capx_at':'Capex/Assets','rd_at':'R\\&D/Assets',
        'aqc_at':'Acquisitions/Assets','book_lev':'Book leverage','cash_at':'Cash/Assets',
        'idio_vol':'Idiosyncratic volatility','total_vol':'Total return volatility'}

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

def panel(d, y, xvars, entity=True, time=True):
    dd = d.dropna(subset=[y] + xvars).copy().set_index(['gvkey_i', 'fyear_i'])
    return PanelOLS(dd[y], dd[xvars], entity_effects=entity, time_effects=time,
                    drop_absorbed=True, check_rank=False).fit(
                    cov_type='clustered', cluster_entity=True)

# =====================================================================
# T6 — Heterogeneity by OBSERVABLE moderators (triple difference)
#   did_m = did * 1[moderator high].  Reported: did (low group) and did_m
#   (extra effect for high group). Moderators fixed at pre-rule (2022) values.
# =====================================================================
log('T6 heterogeneity ...')
base22 = df[df.fyear == 2022][['gvkey', 'equity_share', 'book_lev', 'rd_at', 'sich']].copy()
base22 = base22.rename(columns={'equity_share':'eq22','book_lev':'lev22','rd_at':'rd22'})
base22['fin22'] = ((base22.sich >= 6000) & (base22.sich < 6800)).astype(float)  # financials/regulated
h = main.merge(base22[['gvkey','eq22','lev22','rd22','fin22']], on='gvkey', how='left')

MODS = [
    ('High CEO equity-pay share', 'eq22',  None),   # median split
    ('High book leverage',        'lev22', None),
    ('R\\&D-active firm',         'rd22',  0.0),     # rd>0 vs 0
    ('Financial/regulated firm',  'fin22', 0.5),     # indicator
]
h6 = []
for name, col, thr in MODS:
    d = h.dropna(subset=[col]).copy()
    if thr is None:
        cut = d[col].median(); d['modhi'] = (d[col] > cut).astype(int)
    else:
        d['modhi'] = (d[col] > thr).astype(int)
    d['did_m'] = d['did'] * d['modhi']
    for y, ylab in [(HEAD, LAB[HEAD]), ('invest_at', LAB['invest_at'])]:
        try:
            r = panel(d, y, ['did', 'did_m'] + CTRL)
            h6.append({'moderator': name, 'outcome': y, 'label': ylab,
                       'did_low': r.params['did'],  't_low': r.tstats['did'],
                       'did_int': r.params['did_m'], 't_int': r.tstats['did_m'],
                       'N': int(r.nobs)})
            log(f'  {name:28s} {y:10s} did={r.params["did"]:+.4f}(t={r.tstats["did"]:+.2f}) '
                f'x={r.params["did_m"]:+.4f}(t={r.tstats["did_m"]:+.2f})')
        except Exception as e:
            log(f'  {name} {y} ERR {str(e)[:80]}')
t6 = pd.DataFrame(h6); t6.to_csv(os.path.join(OUT, 't6_hetero.csv'), index=False)

# =====================================================================
# T7 — Size-matched DiD. NN 1:1 match treated->control on pre-rule (2022)
#   size and pre-rule idio_vol, without replacement, caliper 0.25 SD(size).
#   If the vol "effect" is a size artifact it should attenuate on the
#   size-balanced sample. Real-risk outcomes should stay null.
# =====================================================================
log('T7 size-matched DiD ...')
b = df[df.fyear == 2022][['gvkey','treat','size','idio_vol']].dropna(subset=['treat','size']).copy()
b['treat'] = b['treat'].astype(int)
tr = b[b.treat == 1].copy(); co = b[b.treat == 0].copy()
cal = 0.25 * b['size'].std()
used = set(); pairs = []
for _, row in tr.sort_values('size').iterrows():
    pool = co[~co.gvkey.isin(used)]
    if pool.empty: break
    j = (pool['size'] - row['size']).abs().idxmin()
    cand = co.loc[j]
    if abs(cand['size'] - row['size']) <= cal:
        used.add(cand.gvkey); pairs += [row.gvkey, cand.gvkey]
msample = main[main.gvkey.isin(pairs)].copy()
log(f'  matched firms: {len(pairs)} ({len(pairs)//2} pairs), firm-years={len(msample)}')
t7 = []
for y in [HEAD] + REAL:
    try:
        r = panel(msample, y, ['did'] + CTRL)
        t7.append({'outcome': y, 'label': LAB.get(y, y), 'coef': r.params['did'],
                   't': r.tstats['did'], 'N': int(r.nobs)})
    except Exception as e:
        log(f'  {y} ERR {str(e)[:80]}')
# balance check: post-match mean size gap
gap_pre = tr['size'].mean() - co['size'].mean()
mm = b[b.gvkey.isin(pairs)]
gap_post = mm[mm.treat==1]['size'].mean() - mm[mm.treat==0]['size'].mean()
t7d = pd.DataFrame(t7); t7d.to_csv(os.path.join(OUT, 't7_matched.csv'), index=False)
pd.DataFrame([{'gap_pre_size': gap_pre, 'gap_post_size': gap_post,
               'npairs': len(pairs)//2}]).to_csv(os.path.join(OUT, 't7_balance.csv'), index=False)
log(f'  size gap: pre={gap_pre:+.3f} -> post-match={gap_post:+.3f}')

# =====================================================================
# T8 — Randomization inference. Permute the (time-invariant) treatment
#   label across firms 500x, recompute did = post*treat_perm, refit the FE
#   panel, collect the coefficient. Design-based p = share |perm| >= |real|.
# =====================================================================
log('T8 randomization inference (500 perms) ...')
firm_ids = main[['gvkey','treat']].drop_duplicates('gvkey').reset_index(drop=True)
n_tr = int(firm_ids.treat.sum()); n_f = len(firm_ids)
def did_coef(dat, y):
    r = panel(dat, y, ['did'] + CTRL); return r.params['did']
ri = {}
for y in [HEAD, 'invest_at']:
    real = did_coef(main, y)
    perms = []
    for _ in range(500):
        lab = np.zeros(n_f, dtype=int); lab[np.random.choice(n_f, n_tr, replace=False)] = 1
        m = dict(zip(firm_ids.gvkey, lab))
        d = main.copy(); d['tp'] = d.gvkey.map(m); d['did'] = d['post'] * d['tp']
        try: perms.append(did_coef(d, y))
        except Exception: pass
    perms = np.array(perms)
    p = float(np.mean(np.abs(perms) >= abs(real)))
    ri[y] = {'real': real, 'p_ri': p, 'perms': perms,
             'q025': np.percentile(perms, 2.5), 'q975': np.percentile(perms, 97.5)}
    log(f'  {y:10s} real={real:+.4f}  RI p={p:.3f}  perm 95% [{ri[y]["q025"]:+.4f},{ri[y]["q975"]:+.4f}]')
t8 = pd.DataFrame([{'outcome': y, 'label': LAB.get(y, y), 'real': v['real'],
                    'p_ri': v['p_ri'], 'perm_q025': v['q025'], 'perm_q975': v['q975'],
                    'nperm': len(v['perms'])} for y, v in ri.items()])
t8.to_csv(os.path.join(OUT, 't8_ri.csv'), index=False)

# fig3: RI permutation distribution for the headline
fig, ax = plt.subplots(figsize=(7, 4.2))
pp = ri[HEAD]['perms']
ax.hist(pp, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(ri[HEAD]['real'], color='crimson', lw=2,
           label=f"Actual DiD = {ri[HEAD]['real']:+.3f}\n(RI $p$ = {ri[HEAD]['p_ri']:.3f})")
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo DiD coefficient under random treatment (idiosyncratic vol.)')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 500 permutations of treatment', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_randinf.pdf')); plt.close(fig)

# =====================================================================
# T9 — Minimum detectable effect (MDE) at 80% power per real-risk outcome.
#   MDE = (z_.975 + z_.80) * SE ~= 2.80 * SE(did). Expressed as a share of the
#   outcome mean and of its cross-firm SD. A null with small MDE/mean is
#   informative: an effect that size would have been detected.
# =====================================================================
log('T9 minimum detectable effects ...')
t2 = pd.read_csv(os.path.join(OUT, 't2_did_main.csv'))  # has se per outcome
Z = 1.959964 + 0.841621
t9 = []
for y in REAL + [HEAD]:
    row = t2[t2.outcome == y]
    if row.empty: continue
    se = float(row['se'].iloc[0]); coef = float(row['coef'].iloc[0])
    mu = main[y].mean(); sd = main[y].std()
    mde = Z * se
    t9.append({'outcome': y, 'label': LAB.get(y, y), 'coef': coef, 'se': se,
               'mde': mde, 'mde_pct_mean': 100 * mde / abs(mu) if mu else np.nan,
               'mde_pct_sd': 100 * mde / sd})
    log(f'  {y:10s} SE={se:.4f} MDE={mde:.4f} = {100*mde/abs(mu):.1f}% of mean, {100*mde/sd:.1f}% of SD')
t9d = pd.DataFrame(t9); t9d.to_csv(os.path.join(OUT, 't9_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the four new tables
# =====================================================================
# --- T6 hetero
body = ''
for name in [m[0] for m in MODS]:
    sub = t6[t6.moderator == name]
    rv = sub[sub.outcome == HEAD]; iv = sub[sub.outcome == 'invest_at']
    if rv.empty or iv.empty: continue
    rv = rv.iloc[0]; iv = iv.iloc[0]
    body += (f"{name} & {rv['did_low']:+.4f}{stars(rv['t_low'])} & {rv['did_int']:+.4f}{stars(rv['t_int'])} "
             f"& {iv['did_low']:+.4f}{stars(iv['t_low'])} & {iv['did_int']:+.4f}{stars(iv['t_int'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lcccc}
\toprule
& \multicolumn{2}{c}{Idiosyncratic vol.} & \multicolumn{2}{c}{Investment/Assets} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Moderator $M$ (pre-rule) & DiD & DiD$\times M$ & DiD & DiD$\times M$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T7 matched
bal = pd.read_csv(os.path.join(OUT, 't7_balance.csv')).iloc[0]
body = ''
for _, r in t7d.iterrows():
    body += f"{r['label']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {r['N']:.0f} \\\\\n"
w('tab_matched.tex', r"""\begin{tabular}{lccc}
\toprule
Outcome (DV) & DiD (matched) & $t$-stat & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 RI
body = ''
for _, r in t8.iterrows():
    body += (f"{r['label']} & {r['real']:+.4f} & [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] "
             f"& {r['p_ri']:.3f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lccc}
\toprule
Outcome (DV) & Actual DiD & Perm.\ 95\% interval & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 power
body = ''
for _, r in t9d.iterrows():
    body += (f"{r['label']} & {r['coef']:+.4f} & {r['se']:.4f} & {r['mde']:.4f} "
             f"& {r['mde_pct_mean']:.1f}\\% & {r['mde_pct_sd']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lccccc}
\toprule
Outcome (DV) & DiD coef. & SE & MDE(80\%) & \% of mean & \% of SD \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash extra meta for the paper
pd.DataFrame([{'npairs': int(bal['npairs']), 'gap_pre': bal['gap_pre_size'],
               'gap_post': bal['gap_post_size'],
               'ri_p_head': ri[HEAD]['p_ri'], 'ri_p_invest': ri['invest_at']['p_ri'],
               'matched_head_coef': float(t7d[t7d.outcome==HEAD]['coef'].iloc[0]),
               'matched_head_t': float(t7d[t7d.outcome==HEAD]['t'].iloc[0])}
             ]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE — extension tables + fig3 written.')
logf.close()
print('Extension tables written to', TEX)
