#!/usr/bin/env python3
"""
Project 02 (AI in Medicine) — Step 30: journal-track extensions.

The base paper is a SIGNIFICANT result (medical-AI patent stock predicts higher
Tobin's Q and market cap). These extensions therefore stress the result with
robustness, an alternative-identification design, and design-based inference —
and power the ONE insignificant sub-claim (the incumbent-vs-entrant gap) rather
than the headline. All moderators are OBSERVABLE firm characteristics (size,
R&D intensity, SIC sector, incumbency). We do NOT build any clinical-application
(imaging / drug-discovery / genomics) or AI-modality breakdown — that is the
student's reserved hand-coding crux (STUDENT_TASKS, Task 2) and is left for them.

  t4_sumstats.csv  Summary statistics, analytical sample, holders vs non-holders.
  t5_hetero.csv    Heterogeneity of the value premium by observable moderators
                   (firm size, R&D intensity, incumbent sector, prior AI stock).
  t6_altid.csv     Alternative-identification / robustness ladder for the Q
                   premium: industry x year FE, lagged (predetermined) stock,
                   adopter-matched sample, drop mega-caps, two-way clustering,
                   and a LEAD falsification test (future medical-AI *flow* must
                   not predict current Q if the relation is not reverse-caused).
  t7_ri.csv        Randomization inference: 500 permutations of the firm-level
                   medical-AI-holder label under a common AI-era post window;
                   design-based p-value. Also writes fig2_randinf.pdf.
  t8_power.csv     Minimum detectable effects for the INSIGNIFICANT interactions
                   (entrant gap in Q and in market cap): shows what incumbent-vs-
                   entrant difference the design could and could not detect.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reads the same shared panel as 10_analysis.py.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels import PanelOLS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(HERE, 'output', 'tables')
TEX  = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
for d in (OUT, TEX, FIG): os.makedirs(d, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line, flush=True); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)  # deterministic randomization inference

SH = '/mnt/d/ccli/assip26/data'
p = pd.read_csv(f'{SH}/patent_analytical_panel.csv')

def sector(s):
    try: s = int(s)
    except: return 'Other'
    if (2833 <= s <= 2836) or s in (3826, 3827, 3841, 3842, 3843, 3845) or (8000 <= s <= 8099):
        return 'Incumbent (health)'
    if (7370 <= s <= 7379) or (3570 <= s <= 3579) or s in (3674, 3661, 3663, 3669, 3670, 3672):
        return 'Entrant (tech)'
    return 'Other'
p['sector']   = p['sich'].map(sector)
p['entrant']  = (p.sector == 'Entrant (tech)').astype(int)
p['incumbent']= (p.sector == 'Incumbent (health)').astype(int)
p['mktcap_ln']= np.log(p.mktcap.replace(0, np.nan))
p['ind2']     = (p.sich // 100)                 # 2-digit SIC for industry x year FE
p['ln_aimed_x_ent'] = p.ln_aimed * p.entrant

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

def fe(y, xs, data, entity=True, time=True, cluster_time=False):
    d = data.dropna(subset=[y] + xs).copy().set_index(['permno', 'year'])
    mod = PanelOLS(d[y], d[xs], entity_effects=entity, time_effects=time,
                   drop_absorbed=True, check_rank=False)
    if cluster_time:
        return mod.fit(cov_type='clustered', cluster_entity=True, cluster_time=True)
    return mod.fit(cov_type='clustered', cluster_entity=True)

CTRL = ['ln_ai', 'ln_med', 'size']
HEAD = 'tobinq'

# =====================================================================
# T4 — Summary statistics (analytical sample): holders vs non-holders
# =====================================================================
log('T4 summary statistics ...')
p['holder'] = (p.groupby('permno').aimed_stk.transform('max') > 0).astype(int)
svars = [('aimed_stk', 'Medical-AI patent stock'), ('ln_aimed', 'ln(1+med-AI stock)'),
         ('tobinq', "Tobin's Q"), ('mktcap', 'Market cap (\\$M)'),
         ('size', 'Firm size = ln(assets)'), ('rd_at', 'R\\&D/assets'),
         ('ai_stk', 'AI patent stock'), ('med_stk', 'Medical patent stock')]
rows = []
for col, lab in svars:
    a = p[col].dropna()
    h = p.loc[p.holder == 1, col].dropna()
    n = p.loc[p.holder == 0, col].dropna()
    rows.append({'var': lab, 'mean': a.mean(), 'sd': a.std(), 'p50': a.median(),
                 'mean_hold': h.mean(), 'mean_non': n.mean()})
t4 = pd.DataFrame(rows); t4.to_csv(os.path.join(OUT, 't4_sumstats.csv'), index=False)
n_firm = p.permno.nunique(); n_fy = len(p)
n_hold = int(p.loc[p.holder == 1, 'permno'].nunique())
log(f'  firms={n_firm} firm-years={n_fy} holder-firms={n_hold}')

# =====================================================================
# T5 — Heterogeneity of the value premium by OBSERVABLE moderators
#   Q ~ ln_aimed + ln_aimed*M + M + controls.  Report base (low-M) slope
#   and the extra slope for high-M firms.  Moderators are observable firm
#   characteristics only (NOT clinical application — that is the student's).
# =====================================================================
log('T5 heterogeneity of the value premium ...')
p['large']   = (p['size'] > p['size'].median()).astype(int)
p['rdhi']    = (p.rd_at > p.groupby('year').rd_at.transform('median')).astype(int)
p['aihi']    = (p.ai_share > p.groupby('year').ai_share.transform('median')).astype(int)  # AI-specialized
MODS = [('Large firm (above-median assets)', 'large'),
        ('R\\&D-intensive (above-median R\\&D/assets)', 'rdhi'),
        ('Incumbent health firm', 'incumbent'),
        ('AI-specialized (above-median AI patent share)', 'aihi')]
h5 = []
for name, m in MODS:
    d = p.copy()
    d['ln_aimed_x_m'] = d.ln_aimed * d[m]
    r = fe(HEAD, ['ln_aimed', 'ln_aimed_x_m', m] + CTRL, d)
    h5.append({'moderator': name, 'base': r.params['ln_aimed'], 't_base': r.tstats['ln_aimed'],
               'inter': r.params['ln_aimed_x_m'], 't_inter': r.tstats['ln_aimed_x_m'],
               'N': int(r.nobs)})
    log(f'  {name:42s} base={r.params["ln_aimed"]:+.3f}(t={r.tstats["ln_aimed"]:+.2f}) '
        f'x={r.params["ln_aimed_x_m"]:+.3f}(t={r.tstats["ln_aimed_x_m"]:+.2f})')
t5 = pd.DataFrame(h5); t5.to_csv(os.path.join(OUT, 't5_hetero.csv'), index=False)

# =====================================================================
# T6 — Alternative-identification / robustness ladder for Q ~ med-AI stock.
#   Central threat: valuable firms patent more (reverse causality). We add
#   industry x year FE, a predetermined (lagged) stock, an adopter-matched
#   sample, a mega-cap drop, two-way clustering, and a LEAD falsification.
# =====================================================================
log('T6 alternative-identification / robustness ...')
t6 = []
def add(spec, r, key='ln_aimed'):
    t6.append({'spec': spec, 'coef': r.params[key], 't': r.tstats[key], 'N': int(r.nobs)})
    log(f'  {spec:34s} coef={r.params[key]:+.4f} (t={r.tstats[key]:+.2f}) N={int(r.nobs)}')

# (1) Baseline (firm + year FE) — reproduces 10_analysis
add('(1) Baseline: firm + year FE', fe(HEAD, ['ln_aimed'] + CTRL, p))

# (2) Firm FE + industry(2-digit SIC) x year FE  (time-varying industry shocks)
d2 = p.dropna(subset=[HEAD, 'ln_aimed', 'ind2'] + CTRL).copy()
d2['iy'] = (d2.ind2.astype('Int64').astype(str) + '_' + d2.year.astype(str)).astype('category').cat.codes
dd = d2.set_index(['permno', 'year'])
r2 = PanelOLS(dd[HEAD], dd[['ln_aimed'] + CTRL], entity_effects=True,
              other_effects=d2.set_index(['permno', 'year'])['iy'],
              drop_absorbed=True, check_rank=False).fit(cov_type='clustered', cluster_entity=True)
add('(2) + industry$\\times$year FE', r2)

# (3) Predetermined stock: 1-year lag of ln_aimed
p = p.sort_values(['permno', 'year'])
p['ln_aimed_l1'] = p.groupby('permno')['ln_aimed'].shift(1)
add('(3) Lagged (predetermined) stock', fe(HEAD, ['ln_aimed_l1'] + CTRL, p), key='ln_aimed_l1')

# (4) Adopter-matched sample: match ever-holders to observably similar never-
#     holders on pre-period (2012) size, R&D, and sector; NN 1:1, caliper.
b = p[p.year == 2012][['permno', 'holder', 'size', 'rd_at', 'incumbent', 'entrant']].dropna(subset=['size'])
tr = b[b.holder == 1].copy(); co = b[b.holder == 0].copy()
cal = 0.25 * b['size'].std(); used = set(); keep = []
for _, row in tr.sort_values('size').iterrows():
    pool = co[(~co.permno.isin(used)) & (co.incumbent == row.incumbent) & (co.entrant == row.entrant)]
    if pool.empty:
        pool = co[~co.permno.isin(used)]
    if pool.empty: break
    j = (pool['size'] - row['size']).abs().idxmin()
    cand = co.loc[j]
    if abs(cand['size'] - row['size']) <= cal:
        used.add(cand.permno); keep += [row.permno, cand.permno]
msample = p[p.permno.isin(keep)].copy()
add(f'(4) Adopter-matched sample', fe(HEAD, ['ln_aimed'] + CTRL, msample))
n_pairs = len(keep) // 2
log(f'    matched {n_pairs} adopter/non-adopter pairs, firm-years={len(msample)}')

# (5) Drop mega-caps (top 1% market cap) — result not driven by a few giants
cut = p.mktcap.quantile(0.99)
add('(5) Drop top-1\\% mega-caps', fe(HEAD, ['ln_aimed'] + CTRL, p[p.mktcap <= cut]))

# (6) Two-way clustered SE (firm and year)
add('(6) Two-way clustered SE', fe(HEAD, ['ln_aimed'] + CTRL, p, cluster_time=True))

# (7) LEAD FALSIFICATION: future medical-AI FLOW predicting current Q.
#     Flow (not the mechanically-rising stock) avoids collinearity with the level.
#     If the relation were reverse-caused (high Q -> more future patenting), the
#     lead loads positively even controlling for the current stock.
p['flow']      = np.log1p(p['aimed'])
p['flow_lead1']= p.groupby('permno')['flow'].shift(-1)
rlead = fe(HEAD, ['flow_lead1', 'ln_aimed'] + CTRL, p)
t6.append({'spec': '(7) Lead falsification: future flow', 'coef': rlead.params['flow_lead1'],
           't': rlead.tstats['flow_lead1'], 'N': int(rlead.nobs)})
log(f'  (7) lead falsification            future-flow coef={rlead.params["flow_lead1"]:+.4f} '
    f'(t={rlead.tstats["flow_lead1"]:+.2f})  [current stock coef={rlead.params["ln_aimed"]:+.4f}]')
t6d = pd.DataFrame(t6); t6d.to_csv(os.path.join(OUT, 't6_altid.csv'), index=False)

# =====================================================================
# T7 — Randomization inference. Firm-level medical-AI-holder label D_i under a
#   common AI-era post window (year >= 2013).  did = post * D.  Regress Q on did
#   (+ controls) with firm + year FE.  Permute D across firms 500x for a
#   design-based p.  Mirrors the golden template; no staggered-timing bias.
# =====================================================================
log('T7 randomization inference (500 perms) ...')
p['post13'] = (p.year >= 2013).astype(int)
firm_h = p.groupby('permno').holder.max()
D = firm_h.to_dict()
p['D'] = p.permno.map(D)
p['did'] = p.post13 * p.D
def did_coef(dat):
    r = fe(HEAD, ['did'] + CTRL, dat); return r.params['did'], r.tstats['did']
real_c, real_t = did_coef(p)
firm_ids = np.array(list(firm_h.index)); n_f = len(firm_ids); n_tr = int(firm_h.sum())
log(f'  real AI-era holder DiD on Q: coef={real_c:+.4f} (t={real_t:+.2f}); '
    f'holders={n_tr}/{n_f}')
perms = []
for i in range(500):
    lab = np.zeros(n_f, dtype=int); lab[np.random.choice(n_f, n_tr, replace=False)] = 1
    m = dict(zip(firm_ids, lab))
    d = p.copy(); d['Dp'] = d.permno.map(m); d['did'] = d.post13 * d['Dp']
    try:
        r = fe(HEAD, ['did'] + CTRL, d); perms.append(r.params['did'])
    except Exception:
        pass
perms = np.array(perms)
p_ri = float(np.mean(np.abs(perms) >= abs(real_c)))
q025, q975 = np.percentile(perms, 2.5), np.percentile(perms, 97.5)
t7 = pd.DataFrame([{'outcome': "Tobin's Q", 'real': real_c, 'real_t': real_t,
                    'p_ri': p_ri, 'perm_q025': q025, 'perm_q975': q975, 'nperm': len(perms)}])
t7.to_csv(os.path.join(OUT, 't7_ri.csv'), index=False)
log(f'  RI p={p_ri:.3f}  perm 95% [{q025:+.4f},{q975:+.4f}]  (nperm={len(perms)})')

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(perms, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(real_c, color='crimson', lw=2,
           label=f"Actual DiD = {real_c:+.3f}\n(RI $p$ = {p_ri:.3f})")
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel("Placebo DiD coefficient under random holder assignment (Tobin's Q)")
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 500 permutations of the medical-AI holder label', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig2_randinf.pdf')); plt.close(fig)

# =====================================================================
# T8 — Power / MDE for the INSIGNIFICANT sub-results (the incumbent-vs-entrant
#   gap).  The headline premium (t=5) needs no powering; the claim that the
#   premium is "concentrated in incumbents" rests on an insignificant entrant
#   interaction, so we report what gap the design could detect at 80% power.
# =====================================================================
log('T8 power / MDE for the entrant interaction ...')
Z = 1.959964 + 0.841621
t8 = []
for y, ylab in [('tobinq', "Tobin's Q"), ('mktcap_ln', 'ln(market cap)')]:
    r = fe(y, ['ln_aimed', 'ln_aimed_x_ent', 'entrant'] + ['ln_ai', 'ln_med', 'size'], p)
    coef = r.params['ln_aimed_x_ent']; se = r.std_errors['ln_aimed_x_ent']
    base = r.params['ln_aimed']
    mde = Z * se
    t8.append({'outcome': ylab, 'base': base, 'inter': coef, 't_inter': r.tstats['ln_aimed_x_ent'],
               'se': se, 'mde': mde, 'mde_pct_base': 100 * mde / abs(base)})
    log(f'  {ylab:14s} base={base:+.3f} entrant-gap={coef:+.3f}(t={r.tstats["ln_aimed_x_ent"]:+.2f}) '
        f'SE={se:.3f} MDE(80%)={mde:.3f} = {100*mde/abs(base):.0f}% of base premium')
t8d = pd.DataFrame(t8); t8d.to_csv(os.path.join(OUT, 't8_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the five new tables
# =====================================================================
# --- T4 summary statistics
body = ''
for _, r in t4.iterrows():
    body += (f"{r['var']} & {r['mean']:.3f} & {r['sd']:.3f} & {r['p50']:.3f} "
             f"& {r['mean_hold']:.3f} & {r['mean_non']:.3f} \\\\\n")
w('tab_sumstats.tex', r"""\begin{tabular}{lccccc}
\toprule
& \multicolumn{3}{c}{Full sample} & \multicolumn{2}{c}{Mean by group} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-6}
Variable & Mean & SD & Median & Holder & Non-holder \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T5 heterogeneity
body = ''
for _, r in t5.iterrows():
    body += (f"{r['moderator']} & {r['base']:+.3f}{stars(r['t_base'])} & ({r['t_base']:+.2f}) "
             f"& {r['inter']:+.3f}{stars(r['t_inter'])} & ({r['t_inter']:+.2f}) & {r['N']:,} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lccccc}
\toprule
Moderator $M$ & Base slope & $t$ & $\times\,M$ & $t$ & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T6 alternative identification / robustness
body = ''
for _, r in t6d.iterrows():
    body += f"{r['spec']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {r['N']:,} \\\\\n"
w('tab_altid.tex', r"""\begin{tabular}{lccc}
\toprule
Specification & Med-AI stock coef. & $t$-stat & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T7 randomization inference
body = ''
for _, r in t7.iterrows():
    body += (f"{r['outcome']} & {r['real']:+.4f}{stars(r['real_t'])} "
             f"& [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] & {r['p_ri']:.3f} & {int(r['nperm'])} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lcccc}
\toprule
Outcome (DV) & Actual DiD & Perm.\ 95\% interval & RI $p$ & \# perms \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 power / MDE
body = ''
for _, r in t8d.iterrows():
    body += (f"{r['outcome']} & {r['base']:+.3f} & {r['inter']:+.3f} & ({r['t_inter']:+.2f}) "
             f"& {r['se']:.3f} & {r['mde']:.3f} & {r['mde_pct_base']:.0f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lcccccc}
\toprule
DV & Base premium & Entrant gap & $t$ & SE & MDE(80\%) & \% of base \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{'n_firms': n_firm, 'n_fy': n_fy, 'n_holders': n_hold, 'n_pairs': n_pairs,
               'ri_real': real_c, 'ri_t': real_t, 'ri_p': p_ri,
               'ri_q025': q025, 'ri_q975': q975,
               'lead_coef': float(rlead.params['flow_lead1']),
               'lead_t': float(rlead.tstats['flow_lead1']),
               'mde_q': float(t8d.iloc[0]['mde']), 'mde_q_pct': float(t8d.iloc[0]['mde_pct_base']),
               'matched_coef': float(t6d[t6d.spec.str.startswith('(4)')]['coef'].iloc[0]),
               'matched_t': float(t6d[t6d.spec.str.startswith('(4)')]['t'].iloc[0]),
               'iy_coef': float(t6d[t6d.spec.str.startswith('(2)')]['coef'].iloc[0]),
               'iy_t': float(t6d[t6d.spec.str.startswith('(2)')]['t'].iloc[0])}
             ]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE — extension tables + fig2 written.')
logf.close()
print('Extension tables written to', TEX)
