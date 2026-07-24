#!/usr/bin/env python3
"""
Project 08 (LLM 10-K look-ahead) — Step 50: journal-track extensions.

Adds four real tables that deepen the placebo null without touching the student's
reserved contribution (the hand-built anonymization GOLD STANDARD and the human
blind-identification / leakage measurement, STUDENT_TASKS.md). Everything here uses
only OBSERVABLE filing characteristics already produced by the automated pipeline
(the machine-redactor's identifier count, the model's own risk score, whether the
firm names itself in the raw text) and design-based inference. It never constructs
a hand-anonymized text, a leakage rate, or an identifiability judgment — those are
the student's gold-standard deliverable and are cited here as the next step.

  t7_hetero.csv  Heterogeneity of the raw-vs-anon predictive gap by OBSERVABLE
                 moderators (pre-cutoff window, where look-ahead is possible).
  t8_matched.csv Composition-matched placebo: nearest-neighbor match pre-cutoff to
                 post-cutoff filings on observable score level + redaction count,
                 then re-estimate the four cells and the triple interaction on the
                 balanced sample (removes window-composition as a confound).
  t9_ri.csv      Randomization inference: 2000 within-filing swaps of the raw/anon
                 label (the actual randomizable manipulation). Design-based p-values
                 for the triple z*raw*post and the within-pre extra-raw slope. Also
                 writes fig4_randinf.pdf.
  t10_power.csv  Minimum detectable effects (80% power) for the key placebo slopes:
                 shows the null is informative, not merely underpowered.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reads the same panel as 30_regressions.py.
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

np.random.seed(20260724)  # deterministic RI (Date.now-free environment)

df = pd.read_csv(os.path.join(PROC, 'panel.csv'), dtype={'id': str})
df = df.dropna(subset=['bhar_12_w', 'z_raw', 'z_anon']).reset_index(drop=True)
log(f'panel: {len(df)} filings (pre={(df.post==0).sum()}, post={(df.post==1).sum()})')

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

def ols(formula, data):
    return smf.ols(formula, data=data).fit(cov_type='HC1')
def cl(formula, data):
    return smf.ols(formula, data=data).fit(cov_type='cluster',
                   cov_kwds={'groups': data['id']})

def make_long(d):
    """Stacked long form: two rows per filing (raw row raw=1, anon row raw=0)."""
    rows = []
    for _, r in d.iterrows():
        rows.append(dict(id=r.id, post=int(r.post), raw=1, z=r.z_raw, bhar=r.bhar_12_w))
        rows.append(dict(id=r.id, post=int(r.post), raw=0, z=r.z_anon, bhar=r.bhar_12_w))
    return pd.DataFrame(rows).dropna(subset=['bhar', 'z'])

# =====================================================================
# T7 — Heterogeneity of the raw-vs-anon predictive gap by OBSERVABLE
#   moderators, in the pre-cutoff window (the only window where look-ahead
#   is possible). For each moderator M we estimate two things:
#     (a) extra-raw slope:  bhar ~ z*raw*Mhi   -> z:raw (M-low) and z:raw:Mhi
#     (b) gap slope:        bhar ~ z_gap*Mhi   -> z_gap (M-low) and z_gap:Mhi
#   Look-ahead (H2) predicts the extra-raw / gap predictive power concentrates
#   where identity signal is denser; a flat interaction reinforces the null.
#   Moderators are OBSERVABLE (machine-redactor count, the model's own score,
#   firm-self-naming) — NOT the student's hand-built leakage/gold standard.
# =====================================================================
log('T7 heterogeneity (pre-cutoff) ...')
pre = df[df.post == 0].copy()
MODS = [
    ('High automated-redaction count', 'n_redactions', 'median'),
    ('Elevated model risk score',      'score_raw',    1.0),   # >1 vs modal baseline 1
    ('Firm names itself in raw text',  'name_leak_raw', 0.0),  # >0 vs 0
]
h7 = []
for name, col, thr in MODS:
    d = pre.dropna(subset=[col]).copy()
    if thr == 'median':
        cut = d[col].median(); d['Mhi'] = (d[col] > cut).astype(int)
    else:
        d['Mhi'] = (d[col] > thr).astype(int)
    share_hi = d['Mhi'].mean()
    rec = {'moderator': name, 'col': col, 'share_hi': share_hi, 'N': int(len(d))}
    # (a) extra-raw slope, moderated
    L = make_long(d)
    try:
        m = cl('bhar ~ z * raw * Mhi', L.merge(d[['id', 'Mhi']], on='id'))
        rec['exraw_low'] = m.params.get('z:raw', np.nan);      rec['t_exraw_low'] = m.tvalues.get('z:raw', np.nan)
        rec['exraw_int'] = m.params.get('z:raw:Mhi', np.nan);  rec['t_exraw_int'] = m.tvalues.get('z:raw:Mhi', np.nan)
    except Exception as e:
        log(f'  {name} exraw ERR {str(e)[:70]}')
        rec['exraw_low'] = rec['t_exraw_low'] = rec['exraw_int'] = rec['t_exraw_int'] = np.nan
    # (b) gap slope, moderated
    try:
        mg = ols('bhar_12_w ~ z_gap * Mhi', d)
        rec['gap_low'] = mg.params.get('z_gap', np.nan);      rec['t_gap_low'] = mg.tvalues.get('z_gap', np.nan)
        rec['gap_int'] = mg.params.get('z_gap:Mhi', np.nan);  rec['t_gap_int'] = mg.tvalues.get('z_gap:Mhi', np.nan)
    except Exception as e:
        log(f'  {name} gap ERR {str(e)[:70]}')
        rec['gap_low'] = rec['t_gap_low'] = rec['gap_int'] = rec['t_gap_int'] = np.nan
    h7.append(rec)
    log(f'  {name:32s} share_hi={share_hi:.2f}  exraw_low={rec["exraw_low"]:+.4f}(t={rec["t_exraw_low"]:+.2f}) '
        f'exraw_int={rec["exraw_int"]:+.4f}(t={rec["t_exraw_int"]:+.2f})')
t7 = pd.DataFrame(h7); t7.to_csv(os.path.join(OUT, 't7_hetero.csv'), index=False)

# =====================================================================
# T8 — Composition-matched placebo. The pre- and post-cutoff windows are
#   different firms filed in different years; the null triple interaction
#   could in principle reflect that composition gap. We nearest-neighbor
#   match each post-cutoff filing to a not-yet-used pre-cutoff filing on
#   OBSERVABLE score level (z_raw) and machine-redaction count (standardized),
#   without replacement, caliper 0.5 SD on the score. On the balanced sample
#   we re-estimate the four cells and the triple interaction. Firm fixed
#   effects across windows are infeasible (only 1 gvkey appears in both).
# =====================================================================
log('T8 composition-matched placebo ...')
mm = df[['id', 'post', 'z_raw', 'z_anon', 'z_gap', 'bhar_12_w', 'n_redactions']].copy()
mm['zr'] = (mm['n_redactions'] - mm['n_redactions'].mean()) / mm['n_redactions'].std()
po = mm[mm.post == 1].copy(); prem = mm[mm.post == 0].copy()
cal = 0.5 * mm['z_raw'].std()
used = set(); keep_ids = []
for _, row in po.iterrows():
    pool = prem[~prem.id.isin(used)]
    if pool.empty: break
    dist = np.sqrt((pool['z_raw'] - row['z_raw'])**2 + (pool['zr'] - row['zr'])**2)
    j = dist.idxmin(); cand = prem.loc[j]
    if abs(cand['z_raw'] - row['z_raw']) <= cal:
        used.add(cand.id); keep_ids += [row.id, cand.id]
msample = df[df.id.isin(keep_ids)].copy()
npairs = len(keep_ids) // 2
log(f'  matched pairs={npairs}  matched filings={len(msample)} '
    f'(pre={(msample.post==0).sum()}, post={(msample.post==1).sum()})')
# balance: mean score-level gap pre-vs-post, before vs after matching
gap_pre_all = df[df.post==0]['z_raw'].mean() - df[df.post==1]['z_raw'].mean()
gap_pre_m   = msample[msample.post==0]['z_raw'].mean() - msample[msample.post==1]['z_raw'].mean()
# four cells + triple on matched sample
cells = [('(1) RAW / pre',  'z_raw',  msample[msample.post==0]),
         ('(2) ANON / pre', 'z_anon', msample[msample.post==0]),
         ('(3) RAW / post', 'z_raw',  msample[msample.post==1]),
         ('(4) ANON / post','z_anon', msample[msample.post==1])]
t8rows = []
for nm, key, data in cells:
    data = data.dropna(subset=['bhar_12_w', key])
    m = ols(f'bhar_12_w ~ {key}', data)
    t8rows.append(dict(spec=nm, coef=m.params[key], t=m.tvalues[key], N=int(m.nobs)))
Lm = make_long(msample)
mt = cl('bhar ~ z * raw * post', Lm)
tri_c = float(mt.params.get('z:raw:post', np.nan)); tri_t = float(mt.tvalues.get('z:raw:post', np.nan))
t8rows.append(dict(spec='Triple z x Raw x Post', coef=tri_c, t=tri_t, N=int(mt.nobs)))
t8 = pd.DataFrame(t8rows); t8.to_csv(os.path.join(OUT, 't8_matched.csv'), index=False)
pd.DataFrame([{'npairs': npairs, 'gap_pre_all': gap_pre_all, 'gap_pre_matched': gap_pre_m,
               'tri_c': tri_c, 'tri_t': tri_t}]).to_csv(os.path.join(OUT, 't8_balance.csv'), index=False)
log(f'  matched triple z:raw:post = {tri_c:+.4f} (t={tri_t:+.2f}); '
    f'score-level pre-post gap {gap_pre_all:+.3f} -> matched {gap_pre_m:+.3f}')

# =====================================================================
# T9 — Randomization inference on the raw-vs-anon manipulation. The actual
#   randomizable object is WHICH of a filing's two scores is called "raw."
#   Under H1 (the model reads risk; identity is irrelevant) the raw and anon
#   scores are exchangeable within a filing, so swapping the label at random
#   (prob 0.5, independently per filing) generates the null distribution of
#   the placebo statistics. We do 2000 swaps and recompute (i) the triple
#   z*raw*post and (ii) the within-pre extra-raw slope z*raw. Point estimates
#   suffice for RI, so we solve each OLS by least squares for speed.
# =====================================================================
log('T9 randomization inference (2000 within-filing swaps) ...')
zr = df['z_raw'].values; za = df['z_anon'].values
post = df['post'].values.astype(float); y = df['bhar_12_w'].values
n = len(df)

def triple_coef(z_raw_row, z_anon_row):
    """OLS coef on z:raw:post from stacked bhar ~ z*raw*post (point estimate)."""
    z = np.concatenate([z_raw_row, z_anon_row])
    raw = np.concatenate([np.ones(n), np.zeros(n)])
    pp = np.concatenate([post, post])
    yy = np.concatenate([y, y])
    X = np.column_stack([np.ones(2*n), z, raw, pp, z*raw, z*pp, raw*pp, z*raw*pp])
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    return beta[7]

def exraw_pre_coef(z_raw_row, z_anon_row):
    """OLS coef on z:raw from pre-cutoff bhar ~ z*raw (point estimate)."""
    idx = post == 0
    z = np.concatenate([z_raw_row[idx], z_anon_row[idx]])
    raw = np.concatenate([np.ones(idx.sum()), np.zeros(idx.sum())])
    yy = np.concatenate([y[idx], y[idx]])
    X = np.column_stack([np.ones(2*idx.sum()), z, raw, z*raw])
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    return beta[3]

real_tri = triple_coef(zr, za)
real_ex  = exraw_pre_coef(zr, za)
log(f'  actual triple z:raw:post = {real_tri:+.4f} ; actual within-pre extra-raw = {real_ex:+.4f}')

NPERM = 2000
perm_tri = np.empty(NPERM); perm_ex = np.empty(NPERM)
for b in range(NPERM):
    swap = np.random.rand(n) < 0.5
    zr_b = np.where(swap, za, zr); za_b = np.where(swap, zr, za)
    perm_tri[b] = triple_coef(zr_b, za_b)
    perm_ex[b]  = exraw_pre_coef(zr_b, za_b)
p_tri = float(np.mean(np.abs(perm_tri) >= abs(real_tri)))
p_ex  = float(np.mean(np.abs(perm_ex)  >= abs(real_ex)))
t9 = pd.DataFrame([
    {'statistic': 'Triple z x Raw x Post', 'actual': real_tri, 'p_ri': p_tri,
     'perm_q025': np.percentile(perm_tri, 2.5), 'perm_q975': np.percentile(perm_tri, 97.5), 'nperm': NPERM},
    {'statistic': 'Within-pre extra-RAW slope (z x Raw)', 'actual': real_ex, 'p_ri': p_ex,
     'perm_q025': np.percentile(perm_ex, 2.5), 'perm_q975': np.percentile(perm_ex, 97.5), 'nperm': NPERM},
])
t9.to_csv(os.path.join(OUT, 't9_ri.csv'), index=False)
log(f'  triple RI p={p_tri:.3f} 95%[{np.percentile(perm_tri,2.5):+.4f},{np.percentile(perm_tri,97.5):+.4f}]')
log(f'  extra-raw RI p={p_ex:.3f} 95%[{np.percentile(perm_ex,2.5):+.4f},{np.percentile(perm_ex,97.5):+.4f}]')

# fig4: RI permutation distribution for the triple interaction
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(perm_tri, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(real_tri, color='crimson', lw=2,
           label=f'Actual triple = {real_tri:+.3f}\n(RI $p$ = {p_tri:.3f})')
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo triple $z\\times$Raw$\\times$Post under random raw/anon labeling')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 2000 within-filing raw/anon label swaps', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig4_randinf.pdf')); plt.close(fig)

# =====================================================================
# T10 — Minimum detectable effect (MDE) at 80% power for the key placebo
#   slopes. MDE = (z_.975 + z_.80) * SE ~= 2.80 * SE. Expressed in return
#   points (x100) and as a share of the 12-month BHAR cross-sectional SD.
#   A null with a small MDE relative to the outcome's dispersion is
#   informative: a look-ahead effect of that size would have been detected.
# =====================================================================
log('T10 minimum detectable effects ...')
Z = 1.959964 + 0.841621
sd_bhar = df['bhar_12_w'].std()
# collect SEs of the key estimates
est = []
# raw/pre and anon/pre
for lbl, key in [('Raw-score slope (pre-cutoff)', 'z_raw'),
                 ('Anon-score slope (pre-cutoff)', 'z_anon')]:
    d = df[df.post == 0].dropna(subset=['bhar_12_w', key])
    m = ols(f'bhar_12_w ~ {key}', d)
    est.append((lbl, m.params[key], m.bse[key]))
# pre gap slope
dg = df[df.post == 0].dropna(subset=['bhar_12_w', 'z_gap'])
mg = ols('bhar_12_w ~ z_gap', dg)
est.append(('Score-gap slope (pre-cutoff)', mg.params['z_gap'], mg.bse['z_gap']))
# within-pre extra-raw slope (clustered)
Lpre = make_long(df[df.post == 0])
mex = cl('bhar ~ z * raw', Lpre)
est.append(('Extra-RAW slope, pre (z x Raw)', mex.params['z:raw'], mex.bse['z:raw']))
# triple interaction (clustered)
Lall = make_long(df)
mtr = cl('bhar ~ z * raw * post', Lall)
est.append(('Triple z x Raw x Post', mtr.params['z:raw:post'], mtr.bse['z:raw:post']))
t10rows = []
for lbl, coef, se in est:
    mde = Z * se
    t10rows.append({'estimate': lbl, 'coef': coef, 'se': se, 'mde': mde,
                    'mde_pp': 100 * mde, 'mde_pct_sd': 100 * mde / sd_bhar})
    log(f'  {lbl:34s} coef={coef:+.4f} SE={se:.4f} MDE={mde:.4f} '
        f'= {100*mde:.2f}pp = {100*mde/sd_bhar:.1f}% of BHAR SD')
t10 = pd.DataFrame(t10rows); t10.to_csv(os.path.join(OUT, 't10_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the four new tables
# =====================================================================
# --- T7 hetero
body = ''
for _, r in t7.iterrows():
    body += (f"{r['moderator']} & {r['exraw_low']:+.4f}{stars(r['t_exraw_low'])} "
             f"& {r['exraw_int']:+.4f}{stars(r['t_exraw_int'])} "
             f"& {r['gap_low']:+.4f}{stars(r['t_gap_low'])} "
             f"& {r['gap_int']:+.4f}{stars(r['t_gap_int'])} & {r['N']:.0f} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lccccc}
\toprule
& \multicolumn{2}{c}{Extra-RAW slope} & \multicolumn{2}{c}{Score-gap slope} & \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Observable moderator $M$ & $M$-low & $\times M$ & $M$-low & $\times M$ & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 matched
bal = pd.read_csv(os.path.join(OUT, 't8_balance.csv')).iloc[0]
body = ''
for _, r in t8.iterrows():
    body += f"{r['spec']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {r['N']:.0f} \\\\\n"
w('tab_matched.tex', r"""\begin{tabular}{lccc}
\toprule
Estimate (matched sample) & Coefficient & $t$-stat & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 RI
body = ''
for _, r in t9.iterrows():
    body += (f"{r['statistic']} & {r['actual']:+.4f} & [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] "
             f"& {r['p_ri']:.3f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lccc}
\toprule
Placebo statistic & Actual & Perm.\ 95\% interval & RI $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 power
body = ''
for _, r in t10.iterrows():
    body += (f"{r['estimate']} & {r['coef']:+.4f} & {r['se']:.4f} & {r['mde']:.4f} "
             f"& {r['mde_pp']:.2f} & {r['mde_pct_sd']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lccccc}
\toprule
Estimate & Coef. & SE & MDE(80\%) & MDE (pp) & \% of BHAR SD \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{'npairs': int(bal['npairs']), 'gap_pre_all': bal['gap_pre_all'],
               'gap_pre_matched': bal['gap_pre_matched'],
               'matched_tri_c': float(bal['tri_c']), 'matched_tri_t': float(bal['tri_t']),
               'ri_p_tri': p_tri, 'ri_p_ex': p_ex,
               'mde_tri_pp': float(t10[t10.estimate=='Triple z x Raw x Post']['mde_pp'].iloc[0]),
               'mde_tri_pctsd': float(t10[t10.estimate=='Triple z x Raw x Post']['mde_pct_sd'].iloc[0]),
               'sd_bhar': sd_bhar}
             ]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE — extension tables (t7-t10) + fig4 written.')
logf.close()
print('Extension tables written to', TEX)
