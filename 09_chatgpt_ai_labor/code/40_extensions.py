#!/usr/bin/env python3
"""
Project 09 (ChatGPT / AI-exposed labor) — Step 40: journal-track extensions.

Adds four real tables that deepen and stress-test the headline cross-sectional
event-study result WITHOUT touching the student's reserved contributions (the
hand-verified event calendar, Task 1, and the hand-coded firm-level task exposure,
Task 2). All identification here uses OBSERVABLE data already in the analytical
panel (AIIE, market-model CARs, predetermined controls, the machine NAICS buckets),
never a new event date and never a hand-coded exposure score.

  t7_hetero.csv    Heterogeneity of the priced-AIIE effect by observable moderators
                   (size, book/market, momentum, financial) via interaction terms.
  t8_matched.csv   Characteristic-matched design: nearest-neighbor match high-AIIE
                   firms to low-AIIE firms on standardized size/BM/mom/emp. Tests
                   whether the priced-AIIE gap survives balancing on the growth/size
                   characteristics a factor-loading story would exploit.
  t9_ri.csv        Randomization inference: permute the INDUSTRY-level AIIE label
                   across the 182 industries 1,000x, broadcast to firms, refit the
                   clustered cross-section, collect the coefficient. Design-based
                   p-value for the headline CAR[0,+10] and the tight CAR[0,+1].
                   Also writes fig4_randinf.pdf.
  t10_power.csv    Minimum detectable effects (80% power) per window and per bucket
                   contrast, denominated in pp and in cross-firm CAR SD: shows which
                   nulls are informative bounds and which windows are well powered.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex.
Reads the SAME data/processed/analytical_panel.csv and the SAME z_aiie / control
construction as 20_regressions.py, so the new tables cannot drift from the main ones.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
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

np.random.seed(20260724)  # deterministic randomization inference

df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))
df['financial'] = df.siccd.between(6000, 6999).astype(int)
CTRL = ['z_lnme', 'z_mom', 'z_bm', 'z_lnemp']
HEAD = 'car_0_10_cg_w'      # headline diffuse-adoption window (matches 20_regressions)
TIGHT = 'car_0_1_cg_w'      # tight window
LAB = {'car_0_1_cg_w':'CAR[0,+1] ChatGPT','car_0_5_cg_w':'CAR[0,+5] ChatGPT',
       'car_0_10_cg_w':'CAR[0,+10] ChatGPT','car_m1_1_cg_w':'CAR[-1,+1] ChatGPT',
       'car_pre_cg_w':'CAR[-10,-2] placebo','car_0_5_g4_w':'CAR[0,+5] GPT-4',
       'car_0_10_g4_w':'CAR[0,+10] GPT-4'}

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

def clus(formula, data):
    dv = formula.split('~')[0].strip()
    rhs = [t for t in ['z_aiie','z_lnme','z_mom','z_bm','z_lnemp'] if t in formula]
    d = data.dropna(subset=[dv] + rhs).copy()
    m = smf.ols(formula, d).fit(cov_type='cluster', cov_kwds={'groups': d['naics4']})
    return m, d

# =====================================================================
# T7 — Heterogeneity by OBSERVABLE moderators (interaction / triple diff).
#   CAR = a + b*z_aiie + c*z_aiie*modhi + d*modhi + controls.
#   b = priced-AIIE effect in the low-moderator group; c = extra effect for
#   the high group. Moderators are predetermined firm characteristics chosen
#   BECAUSE they are orthogonal to the student's reserved hand-coded task
#   exposure. Reported for the headline [0,+10] and tight [0,+1] windows.
# =====================================================================
log('T7 heterogeneity by observable moderators ...')
MODS = [
    ('Large firm (high ln ME)',      'z_lnme', None),
    ('High book/market',             'z_bm',   None),
    ('High momentum',                'z_mom',  None),
    ('Financial firm (SIC 6000-6999)','financial', 0.5),
]
h7 = []
for name, col, thr in MODS:
    d = df.dropna(subset=[col]).copy()
    if thr is None:
        d['modhi'] = (d[col] > d[col].median()).astype(int)
    else:
        d['modhi'] = (d[col] > thr).astype(int)
    d['z_aiie_x'] = d['z_aiie'] * d['modhi']
    for y in [HEAD, TIGHT]:
        f = f'{y} ~ z_aiie + z_aiie_x + modhi + z_lnme + z_mom + z_bm + z_lnemp'
        try:
            m, dd = clus(f, d)
            h7.append({'moderator': name, 'outcome': y,
                       'b_low': m.params['z_aiie'], 't_low': m.tvalues['z_aiie'],
                       'c_int': m.params['z_aiie_x'], 't_int': m.tvalues['z_aiie_x'],
                       'N': int(m.nobs)})
            log(f'  {name:34s} {y:14s} b={m.params["z_aiie"]:+.4f}(t={m.tvalues["z_aiie"]:+.2f}) '
                f'x={m.params["z_aiie_x"]:+.4f}(t={m.tvalues["z_aiie_x"]:+.2f})')
        except Exception as e:
            log(f'  {name} {y} ERR {str(e)[:80]}')
t7 = pd.DataFrame(h7); t7.to_csv(os.path.join(OUT, 't7_hetero.csv'), index=False)

# =====================================================================
# T8 — Characteristic-matched design. Treated = top-AIIE tercile,
#   control = bottom-AIIE tercile. Greedy 1:1 nearest-neighbor match without
#   replacement on the standardized predetermined controls (size, B/M, mom,
#   emp), Euclidean distance, caliper 0.5. If the priced-AIIE effect is really
#   a growth/size factor-loading artifact it should vanish once high- and
#   low-AIIE firms are balanced on those characteristics.
# =====================================================================
log('T8 characteristic-matched high-vs-low AIIE ...')
base = df.dropna(subset=['z_aiie'] + CTRL + [HEAD]).copy()
q = base['z_aiie'].quantile([1/3, 2/3])
hi = base[base['z_aiie'] >= q.iloc[1]].copy()      # top AIIE tercile (treated)
lo = base[base['z_aiie'] <= q.iloc[0]].copy()      # bottom AIIE tercile (control)
Xc = CTRL
lo_arr = lo[Xc].values; lo_idx = lo.index.to_numpy()
used = np.zeros(len(lo), dtype=bool); pairs = []
CALIPER = 0.5
for _, r in hi.iterrows():
    x = r[Xc].values.astype(float)
    dist = np.sqrt(((lo_arr - x) ** 2).sum(axis=1))
    dist[used] = np.inf
    j = int(np.argmin(dist))
    if dist[j] <= CALIPER:
        used[j] = True
        pairs.append((r.name, lo_idx[j]))
tr_ix = [p[0] for p in pairs]; co_ix = [p[1] for p in pairs]
msample = base.loc[tr_ix + co_ix].copy()
log(f'  matched pairs={len(pairs)}  matched firms={len(msample)}')

# balance: standardized mean differences before vs after match
def smd(a, b, col):
    return (a[col].mean() - b[col].mean())
bal = []
for c in Xc:
    pre = smd(hi, lo, c)
    post = smd(base.loc[tr_ix], base.loc[co_ix], c)
    bal.append({'char': c, 'gap_pre': pre, 'gap_post': post})
baldf = pd.DataFrame(bal); baldf.to_csv(os.path.join(OUT, 't8_balance.csv'), index=False)
log('  balance (hi-lo mean gap, pre vs post match):\n' + baldf.round(3).to_string(index=False))

# matched high-minus-low CAR gap + matched-sample regression coefficient
t8 = []
for y in [HEAD, TIGHT, 'car_0_5_cg_w']:
    a = base.loc[tr_ix][y].dropna(); b = base.loc[co_ix][y].dropna()
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var()/len(a) + b.var()/len(b)); tt = diff/se
    # regression on matched sample using the fixed (full-sample) z_aiie
    m, dd = clus(f'{y} ~ z_aiie + z_lnme + z_mom + z_bm + z_lnemp', msample)
    t8.append({'outcome': y, 'label': LAB[y], 'hi_minus_lo': diff, 't_diff': tt,
               'reg_coef': m.params['z_aiie'], 'reg_t': m.tvalues['z_aiie'], 'N': int(m.nobs)})
    log(f'  {y:14s} hi-lo={diff*100:+.2f}pp (t={tt:+.2f})  reg z_aiie={m.params["z_aiie"]*100:+.2f}pp (t={m.tvalues["z_aiie"]:+.2f})')
t8d = pd.DataFrame(t8); t8d.to_csv(os.path.join(OUT, 't8_matched.csv'), index=False)

# =====================================================================
# T9 — Randomization inference at the INDUSTRY level. AIIE is assigned at the
#   4-digit NAICS level, so the design-based null permutes the 182 industry
#   AIIE values AMONG the industries (firms-per-industry counts held fixed),
#   broadcasts back to firms, and refits the clustered cross-section. p =
#   share of |permuted coef| >= |actual coef|. This respects the exact
#   clustering the reported SE respects; permuting across firms would break it.
# =====================================================================
log('T9 randomization inference (industry-level, 1,000 perms) ...')
NPERM = 1000
# unique industry -> z_aiie map (z_aiie is industry-constant by construction)
ind = df.dropna(subset=['z_aiie']).groupby('naics4')['z_aiie'].first().reset_index()
ind_codes = ind['naics4'].values; ind_aiie = ind['z_aiie'].values
ri = {}
for y in [HEAD, TIGHT]:
    m0, d0 = clus(f'{y} ~ z_aiie + z_lnme + z_mom + z_bm + z_lnemp', df)
    real = m0.params['z_aiie']
    perms = []
    for _ in range(NPERM):
        perm_map = dict(zip(ind_codes, np.random.permutation(ind_aiie)))
        d = df.copy()
        d['z_aiie'] = d['naics4'].map(perm_map)
        try:
            mp, _ = clus(f'{y} ~ z_aiie + z_lnme + z_mom + z_bm + z_lnemp', d)
            perms.append(mp.params['z_aiie'])
        except Exception:
            pass
    perms = np.array(perms)
    p = float(np.mean(np.abs(perms) >= abs(real)))
    ri[y] = {'real': real, 'p': p, 'perms': perms,
             'q025': np.percentile(perms, 2.5), 'q975': np.percentile(perms, 97.5)}
    log(f'  {y:14s} real={real*100:+.3f}pp  RI p={p:.3f}  perm 95% [{ri[y]["q025"]*100:+.3f},{ri[y]["q975"]*100:+.3f}]pp')
t9 = pd.DataFrame([{'outcome': y, 'label': LAB[y], 'real': v['real'], 'p_ri': v['p'],
                    'perm_q025': v['q025'], 'perm_q975': v['q975'], 'nperm': len(v['perms'])}
                   for y, v in ri.items()])
t9.to_csv(os.path.join(OUT, 't9_ri.csv'), index=False)

# fig4: RI permutation distribution for the headline window
fig, ax = plt.subplots(figsize=(7, 4.2))
pp = ri[HEAD]['perms'] * 100
ax.hist(pp, bins=40, color='0.78', edgecolor='0.4', linewidth=0.4)
ax.axvline(ri[HEAD]['real'] * 100, color='crimson', lw=2,
           label=f"Actual AIIE coef. = {ri[HEAD]['real']*100:+.2f}pp\n(RI $p$ = {ri[HEAD]['p']:.3f})")
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo AIIE coefficient under random industry exposure (pp, CAR[0,+10])')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 1,000 industry-level permutations of AIIE', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig4_randinf.pdf')); plt.close(fig)

# =====================================================================
# T10 — Minimum detectable effect (MDE) at 80% power. MDE = 2.80 * SE, in pp
#   and as a share of the CAR's cross-firm SD. Applied to the imprecise/null
#   pieces (5-day window, substitution bucket, GPT-4, placebo) and the well-
#   powered headline windows, benchmarked against the estimated headline
#   effects (long-short +1.3-2.7pp; cross-section +0.71pp). CAR means are ~0,
#   so we deliberately do NOT denominate in "% of mean."
# =====================================================================
log('T10 minimum detectable effects ...')
Z = 1.959964 + 0.841621   # 2.80
t10 = []
# (a) cross-sectional AIIE coefficient, several windows
for y in ['car_0_1_cg_w', 'car_0_5_cg_w', HEAD, 'car_pre_cg_w', 'car_0_5_g4_w']:
    m, d = clus(f'{y} ~ z_aiie + z_lnme + z_mom + z_bm + z_lnemp', df)
    se = m.bse['z_aiie']; coef = m.params['z_aiie']
    sd = df[y].std()
    t10.append({'row': f'AIIE coef., {LAB[y]}', 'coef': coef, 'se': se,
                'mde': Z*se, 'mde_pp': 100*Z*se, 'mde_pct_sd': 100*Z*se/sd,
                't': m.tvalues['z_aiie']})
    log(f'  {LAB[y]:22s} coef={coef*100:+.3f}pp SE={se*100:.3f}pp MDE={100*Z*se:.3f}pp = {100*Z*se/sd:.1f}% of CAR SD')
# (b) substitution-bucket mean CAR (individually imprecise in [0,+10])
for y in ['car_0_5_cg_w', HEAD]:
    s = df[df.bucket == 'substitution'][y].dropna()
    se = s.std()/np.sqrt(len(s)); mu = s.mean(); sd = df[y].std()
    t10.append({'row': f'Substitution bucket mean, {LAB[y]}', 'coef': mu, 'se': se,
                'mde': Z*se, 'mde_pp': 100*Z*se, 'mde_pct_sd': 100*Z*se/sd,
                't': mu/se})
    log(f'  Substitution {LAB[y]:14s} mean={mu*100:+.3f}pp SE={se*100:.3f}pp MDE={100*Z*se:.3f}pp')
t10d = pd.DataFrame(t10); t10d.to_csv(os.path.join(OUT, 't10_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the four new tables
# =====================================================================
# --- T7 hetero
body = ''
for name in [m[0] for m in MODS]:
    hh = t7[(t7.moderator == name) & (t7.outcome == HEAD)]
    tt = t7[(t7.moderator == name) & (t7.outcome == TIGHT)]
    if hh.empty or tt.empty: continue
    hh = hh.iloc[0]; tt = tt.iloc[0]
    body += (f"{name} & {hh['b_low']*100:+.2f}{stars(hh['t_low'])} & {hh['c_int']*100:+.2f}{stars(hh['t_int'])} "
             f"& {tt['b_low']*100:+.2f}{stars(tt['t_low'])} & {tt['c_int']*100:+.2f}{stars(tt['t_int'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lcccc}
\toprule
& \multicolumn{2}{c}{CAR[0,+10] (\%)} & \multicolumn{2}{c}{CAR[0,+1] (\%)} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Moderator $M$ (pre-event) & AIIE & AIIE$\times M$ & AIIE & AIIE$\times M$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 matched
balb = ''
CLAB = {'z_lnme':'ln(ME)','z_mom':'6-mo momentum','z_bm':'Book/Market','z_lnemp':'ln(employees)'}
for _, r in baldf.iterrows():
    balb += f"\\quad {CLAB[r['char']]} & {r['gap_pre']:+.3f} & {r['gap_post']:+.3f} \\\\\n"
body = ''
for _, r in t8d.iterrows():
    body += (f"{r['label']} & {r['hi_minus_lo']*100:+.2f}{stars(r['t_diff'])} & ({r['t_diff']:+.2f}) "
             f"& {r['reg_coef']*100:+.2f}{stars(r['reg_t'])} & ({r['reg_t']:+.2f}) & {int(r['N'])} \\\\\n")
w('tab_matched.tex', r"""\begin{tabular}{lccccc}
\toprule
& \multicolumn{2}{c}{High$-$low AIIE gap} & \multicolumn{2}{c}{Matched regression} & \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Outcome (DV) & Diff.\ (\%) & $t$ & AIIE (\%) & $t$ & N \\
\midrule
""" + body + r"""\midrule
\multicolumn{6}{l}{\emph{Covariate balance (high$-$low mean gap, standardized):}} \\
 & Pre-match & Post-match & & & \\
""" + balb + r"""\bottomrule
\end{tabular}""")

# --- T9 RI
body = ''
for _, r in t9.iterrows():
    body += (f"{r['label']} & {r['real']*100:+.2f} & [{r['perm_q025']*100:+.2f}, {r['perm_q975']*100:+.2f}] "
             f"& {r['p_ri']:.3f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lccc}
\toprule
Outcome (DV) & Actual AIIE (\%) & Perm.\ 95\% interval (\%) & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 power
body = ''
for _, r in t10d.iterrows():
    body += (f"{r['row']} & {r['coef']*100:+.2f} & {r['se']*100:.3f} & {r['mde_pp']:.2f} "
             f"& {r['mde_pct_sd']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lcccc}
\toprule
Estimate & Coef.\ (pp) & SE (pp) & MDE(80\%) (pp) & \% of CAR SD \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash scalars for the paper prose
meta = {
    'ri_p_head': ri[HEAD]['p'], 'ri_p_tight': ri[TIGHT]['p'],
    'ri_lo_head': ri[HEAD]['q025']*100, 'ri_hi_head': ri[HEAD]['q975']*100,
    'match_npairs': len(pairs),
    'match_gap_head': float(t8d[t8d.outcome==HEAD]['hi_minus_lo'].iloc[0])*100,
    'match_t_head': float(t8d[t8d.outcome==HEAD]['t_diff'].iloc[0]),
    'match_reg_head': float(t8d[t8d.outcome==HEAD]['reg_coef'].iloc[0])*100,
    'match_reg_t_head': float(t8d[t8d.outcome==HEAD]['reg_t'].iloc[0]),
    'bal_pre_size': float(baldf[baldf.char=='z_lnme']['gap_pre'].iloc[0]),
    'bal_post_size': float(baldf[baldf.char=='z_lnme']['gap_post'].iloc[0]),
    'mde_10day': float(t10d[t10d.row.str.contains('0,\\+10')]['mde_pp'].iloc[0]),
}
pd.DataFrame([meta]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)
with open(os.path.join(TEX, 'ext_scalars.tex'), 'w') as f:
    f.write(f"\\newcommand{{\\ripHead}}{{{meta['ri_p_head']:.3f}}}\n")
    f.write(f"\\newcommand{{\\ripTight}}{{{meta['ri_p_tight']:.3f}}}\n")
    f.write(f"\\newcommand{{\\matchPairs}}{{{meta['match_npairs']}}}\n")
    f.write(f"\\newcommand{{\\matchGapHead}}{{{meta['match_gap_head']:+.2f}}}\n")
    f.write(f"\\newcommand{{\\matchTHead}}{{{meta['match_t_head']:.2f}}}\n")
    f.write(f"\\newcommand{{\\matchRegHead}}{{{meta['match_reg_head']:+.2f}}}\n")
    f.write(f"\\newcommand{{\\matchRegTHead}}{{{meta['match_reg_t_head']:.2f}}}\n")
    f.write(f"\\newcommand{{\\balPreSize}}{{{meta['bal_pre_size']:.2f}}}\n")
    f.write(f"\\newcommand{{\\balPostSize}}{{{meta['bal_post_size']:.2f}}}\n")
    f.write(f"\\newcommand{{\\mdeTenDay}}{{{meta['mde_10day']:.2f}}}\n")

log('DONE — extension tables (t7-t10) + fig4 + ext_scalars written.')
logf.close()
print('Extension tables written to', TEX)
