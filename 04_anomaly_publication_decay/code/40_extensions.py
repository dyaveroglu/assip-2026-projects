#!/usr/bin/env python3
"""
Project 04 (Anomaly publication decay) -- Step 40: journal-track extensions.

Adds four real tables that deepen the H1/H2/H3 story WITHOUT touching the
student's reserved contribution (hand-read exact monthly timing, Task 1, and
hand-coded risk-vs-mispricing FRAMING, Task 2). Every moderator and every design
here uses OBSERVABLE Open Source Asset Pricing metadata only (in-sample strength,
journal, publication era, sample-end / publication YEAR) -- never the authors'
stated economic interpretation, which stays the student's hand-collected variable.

  t7_hetero.csv    Decay heterogeneity by observable moderators (in-sample return
                   strength, in-sample t-stat, top-3 journal, modern-era). Tests
                   the McLean-Pontiff cross-sectional prediction that stronger /
                   more-publicized anomalies decay more -- with the regression-to-
                   the-mean caveat stated in the paper.
  t8_stacked.csv   Not-yet-published-control STACKED difference-in-differences.
                   Because every anomaly is eventually "treated" (published), a
                   two-way FE panel uses already-published anomalies as implicit
                   controls (Callaway-Sant'Anna / Goodman-Bacon problem). Here each
                   publication cohort is compared only to anomalies not yet
                   published within the window -- a clean design-based read on H2.
  t9_ri.csv        Randomization / timing-specificity inference (500 permutations
                   of the publication date within each anomaly's own out-of-sample
                   life). Design-based p-values for the level decay (H1) and the
                   incremental-at-publication effect (H2). Writes fig3_randinf.pdf.
  t10_power.csv    Minimum detectable effects (80% power) for the post-publication
                   decay, the incremental publication effect, and the risk x
                   post-publication interaction -- showing the H2/H3 nulls are
                   informative bounds, not merely underpowered.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reads the same processed panel as
20_regressions.py plus data/interim/anomaly_meta.csv.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels.panel import PanelOLS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed')
INT  = os.path.join(HERE, 'data', 'interim')
OUT  = os.path.join(HERE, 'output', 'tables')
TEX  = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
for dd in (OUT, TEX, FIG): os.makedirs(dd, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)  # deterministic RI

d = pd.read_csv(os.path.join(PROC, 'anomaly_panel.csv'))
d['date'] = pd.to_datetime(d['date'])
meta = pd.read_csv(os.path.join(INT, 'anomaly_meta.csv'))
INS = float(d.loc[d.insample == 1, 'ret'].mean())          # pooled in-sample mean (%)
log(f'panel: {len(d):,} anomaly-months, {d.signal.nunique()} anomalies; pooled in-samp mean={INS:.4f}%')

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '$^{***}$' if a >= 2.58 else '$^{**}$' if a >= 1.96 else '$^{*}$' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

def fe_panel(df, y, xvars, entity='sid', time=None, cluster_col='sid'):
    """Within-transform FE panel with SE clustered by cluster_col.
       entity FE always; time FE if `time` given. Fast (no dummy OLS)."""
    dd = df.dropna(subset=[y] + xvars + [entity] + ([time] if time else [])).copy()
    dd['_ent'] = dd[entity].astype('category').cat.codes
    dd['_tim'] = (dd[time].astype('category').cat.codes if time
                  else dd['date'].astype('category').cat.codes)
    dd = dd.set_index(['_ent', '_tim'])
    clusters = dd[cluster_col].astype('category').cat.codes.to_frame('cl')
    mod = PanelOLS(dd[y], dd[xvars], entity_effects=True,
                   time_effects=bool(time), drop_absorbed=True, check_rank=False)
    return mod.fit(cov_type='clustered', clusters=clusters)

# ======================================================================
# T7 -- Heterogeneity of the decay by OBSERVABLE moderators.
#   ret ~ postsample + postpub + postpub:HI + postsample:HI + HI  (anomaly FE)
#   Report base post-pub decay (LO group) and the extra decay for the HI group.
#   Moderators fixed at study level (observable OSAP metadata), median split.
# ======================================================================
log('T7 heterogeneity by observable moderators ...')
mm = meta.rename(columns={'T-Stat': 'tstat_is', 'Return': 'ret_is'})[
        ['signal', 'tstat_is', 'ret_is', 'journal']].copy()
mm['top3'] = mm['journal'].isin(['JF', 'JFE', 'RFS']).astype(float)
# in-sample mean return (from data, full coverage) and pub-era from panel
lvl = d.groupby('signal').agg(insmean=('insample_mean', 'first')).reset_index()
mm = mm.merge(lvl, on='signal', how='left')
h = d.merge(mm, on='signal', how='left')   # pubyear already present in d

MODS = [
    ('High in-sample return',      'insmean',  'median'),   # MP cross-sectional test
    ('High in-sample $t$-stat',    'tstat_is', 'median'),
    ('Top-3 journal (JF/JFE/RFS)', 'top3',     0.5),
    ('Modern era (pub.\\ $\\ge$ 2006)', 'pubyear', 2005.5),
]
h7 = []
for name, col, thr in MODS:
    g = h.dropna(subset=[col]).copy()
    if thr == 'median':
        cut = g[col].median(); g['HI'] = (g[col] > cut).astype(int)
    else:
        g['HI'] = (g[col] > thr).astype(int)
    g['pp_HI'] = g['postpub'] * g['HI']
    g['ps_HI'] = g['postsample'] * g['HI']
    try:
        r = fe_panel(g, 'ret', ['postsample', 'postpub', 'pp_HI', 'ps_HI', 'HI'])
        n_hi = g.loc[g.HI == 1, 'signal'].nunique(); n_lo = g.loc[g.HI == 0, 'signal'].nunique()
        h7.append({'moderator': name,
                   'pp_lo': r.params['postpub'],   't_lo': r.tstats['postpub'],
                   'pp_int': r.params['pp_HI'],    't_int': r.tstats['pp_HI'],
                   'decay_hi': r.params['postpub'] + r.params['pp_HI'],
                   'n_hi': n_hi, 'n_lo': n_lo, 'N': int(r.nobs)})
        log(f'  {name:34s} pp(lo)={r.params["postpub"]:+.3f}(t={r.tstats["postpub"]:+.2f}) '
            f'x_HI={r.params["pp_HI"]:+.3f}(t={r.tstats["pp_HI"]:+.2f})')
    except Exception as e:
        log(f'  {name} ERR {str(e)[:90]}')
t7 = pd.DataFrame(h7); t7.to_csv(os.path.join(OUT, 't7_hetero.csv'), index=False)

# ======================================================================
# T8 -- Not-yet-published-control STACKED difference-in-differences.
#   Collapse to anomaly-YEAR. For each 3-year publication cohort (center Yc):
#     treated  = anomalies published in [Yc-1, Yc+1]
#     controls = anomalies NOT yet published within the window (pubyear >= Yc+W)
#     window   = [Yc-W, Yc+W];  Post = 1{year >= Yc};  did = Post * Treated
#   Stack all cohorts; entity = (cohort,anomaly), time = (cohort,year).
#   (1) entity FE + Post main effect; (2) entity FE + cohort x year FE.
#   Cluster by anomaly. This compares each cohort only to still-unpublished
#   anomalies -- a clean design-based read on the H2 publication effect.
# ======================================================================
log('T8 not-yet-published-control stacked DiD ...')
ann = (d.groupby(['signal', 'sid', 'year'])
         .agg(ret=('ret', 'mean'), pubyear=('pubyear', 'first')).reset_index())
W = 8
py = ann.groupby('signal').pubyear.first()
centers = range(int(np.floor(py.min())) + 1, int(np.ceil(py.max())), 3)
stacks = []
n_cohorts = 0
for Yc in centers:
    treated = set(py[(py >= Yc - 1) & (py <= Yc + 1)].index)
    controls = set(py[py >= Yc + W].index)
    if len(treated) < 3 or len(controls) < 3:
        continue
    units = treated | controls
    sub = ann[(ann.signal.isin(units)) & (ann.year >= Yc - W) & (ann.year <= Yc + W)].copy()
    if sub.empty:
        continue
    sub['cohort'] = Yc
    sub['treated'] = sub.signal.isin(treated).astype(int)
    sub['post'] = (sub.year >= Yc).astype(int)
    sub['did'] = sub['post'] * sub['treated']
    sub['ent'] = sub['cohort'].astype(str) + '_' + sub['sid'].astype(str)
    sub['tim'] = sub['cohort'].astype(str) + '_' + sub['year'].astype(str)
    stacks.append(sub); n_cohorts += 1
st = pd.concat(stacks, ignore_index=True)
log(f'  {n_cohorts} cohorts, {len(st):,} stacked anomaly-year obs, '
    f'{st.treated.sum():,} treated-obs')

def stacked_fit(time_fe):
    dd = st.copy()
    dd['_e'] = dd['ent'].astype('category').cat.codes
    dd['_t'] = dd['tim'].astype('category').cat.codes if time_fe else dd['year'].astype('category').cat.codes
    dd = dd.set_index(['_e', '_t'])
    xvars = ['did'] if time_fe else ['did', 'post']
    cl = dd['sid'].astype('category').cat.codes.to_frame('cl')
    return PanelOLS(dd['ret'], dd[xvars], entity_effects=True, time_effects=bool(time_fe),
                    drop_absorbed=True, check_rank=False).fit(cov_type='clustered', clusters=cl)

t8 = []
for lbl, tfe in [('(1) Cohort-anomaly FE + Post', False),
                 ('(2) Cohort-anomaly FE + cohort$\\times$year FE', True)]:
    r = stacked_fit(tfe)
    t8.append({'spec': lbl, 'did': r.params['did'], 't': r.tstats['did'],
               'N': int(r.nobs), 'ncohorts': n_cohorts})
    log(f'  {lbl:44s} did={r.params["did"]:+.4f} (t={r.tstats["did"]:+.2f}) N={int(r.nobs):,}')
t8d = pd.DataFrame(t8); t8d.to_csv(os.path.join(OUT, 't8_stacked.csv'), index=False)

# ======================================================================
# T9 -- Randomization / timing-specificity inference (500 permutations).
#   For each anomaly draw a FAKE publication year uniformly within its own
#   out-of-sample life (sampend+1 .. last observed year), keeping the real
#   sample-end. Rebuild fake post-pub / post-sample and refit anomaly-FE panels.
#     (a) level decay (H1): ret ~ ppub_fake            -> compare to real postpub
#     (b) incremental (H2): ret ~ oos + pub_fake       -> compare to real g2
#   Design-based p = share of |placebo| >= |real|. Because returns drift down
#   over each anomaly's life, random later dates ALSO produce negative
#   coefficients: this is a TIMING-SPECIFICITY test, not a mere significance test.
# ======================================================================
log('T9 randomization / timing-specificity inference (500 perms) ...')
info = d.groupby('sid').agg(sampend=('sampend', 'first'),
                            lastyear=('year', 'max')).reset_index()
info = info[info.lastyear > info.sampend + 1]        # need room to place a fake date
placeable = set(info.sid)
base = d[d.sid.isin(placeable)].copy()

# real estimands on the same sample / same estimator
r_real_pp = fe_panel(base, 'ret', ['postpub'])
real_pp = float(r_real_pp.params['postpub'])
r_real_g2 = fe_panel(base, 'ret', ['oos', 'pub'])
real_g2 = float(r_real_g2.params['pub'])
log(f'  real level postpub={real_pp:+.4f}  real incremental g2={real_g2:+.4f}')

rng = np.random
lo = dict(zip(info.sid, info.sampend + 1))
hi = dict(zip(info.sid, info.lastyear))
sids = base['sid'].values
years = base['year'].values
oos_arr = (years > base['sampend'].values).astype(float)
perm_pp, perm_g2 = [], []
uniq = info.sid.values
for _ in range(500):
    fake = {s: rng.randint(lo[s], hi[s] + 1) for s in uniq}   # inclusive upper
    fk = np.array([fake[s] for s in sids])
    ppub_f = (years >= fk).astype(float)
    tmp = base.copy()
    tmp['ppub_f'] = ppub_f
    tmp['pub_f'] = ppub_f            # nested: oos real, pub fake
    try:
        rp = fe_panel(tmp, 'ret', ['ppub_f'])
        perm_pp.append(float(rp.params['ppub_f']))
        rg = fe_panel(tmp, 'ret', ['oos', 'pub_f'])
        perm_g2.append(float(rg.params['pub_f']))
    except Exception:
        pass
perm_pp = np.array(perm_pp); perm_g2 = np.array(perm_g2)
def ri_row(label, real, perms):
    p = float(np.mean(np.abs(perms) >= abs(real)))
    return {'estimand': label, 'real': real, 'p_ri': p,
            'perm_q025': float(np.percentile(perms, 2.5)),
            'perm_q975': float(np.percentile(perms, 97.5)),
            'perm_mean': float(perms.mean()), 'nperm': len(perms)}
t9 = pd.DataFrame([
    ri_row('Level post-publication decay (H1)', real_pp, perm_pp),
    ri_row('Incremental effect at publication (H2)', real_g2, perm_g2)])
t9.to_csv(os.path.join(OUT, 't9_ri.csv'), index=False)
log('  ' + t9.round(4).to_string(index=False).replace('\n', '\n  '))

# fig3: placebo distribution for the INCREMENTAL (H2) effect -- the paper's question
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(perm_g2, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(real_g2, color='crimson', lw=2,
           label=f"Actual incremental effect = {real_g2:+.3f}\n(RI $p$ = "
                 f"{float(np.mean(np.abs(perm_g2) >= abs(real_g2))):.3f})")
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Incremental-at-publication coefficient under a random within-life date')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Timing-specificity test: is the drop tied to the TRUE publication date?',
             fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_randinf.pdf')); plt.close(fig)

# ======================================================================
# T10 -- Minimum detectable effects (80% power). MDE = (z_.975+z_.80)*SE
#   ~= 2.80*SE. SE recovered as coef/t from the estimated regressions (so no
#   drift). Expressed in %/month and as a share of the pooled in-sample mean.
#   Small MDE => the H2/H3 nulls are informative bounds, not low power.
# ======================================================================
log('T10 minimum detectable effects ...')
Z = 1.959964 + 0.841621
t3 = pd.read_csv(os.path.join(OUT, 't3_panel.csv'))
t4 = pd.read_csv(os.path.join(OUT, 't4_hetero.csv'))
sp2 = t3[t3.spec == '(2) Anomaly FE'].iloc[0]
brd = t4[t4.split.str.startswith('Broad')].iloc[0]
items = [
    ('Post-publication decay (H1)',              sp2['postpub'],   sp2['postpub_t']),
    ('Incremental effect at publication (H2)',   sp2['pub_extra'], sp2['pub_extra_t']),
    ('Risk $\\times$ post-pub.\\ interaction (H3)', brd['postpub_x_risk'], brd['postpub_x_risk_t']),
]
t10 = []
for lab, coef, tval in items:
    se = abs(coef / tval)
    mde = Z * se
    t10.append({'estimand': lab, 'coef': coef, 'se': se, 'mde': mde,
                'mde_pct_ins': 100 * mde / abs(INS)})
    log(f'  {lab:42s} coef={coef:+.3f} SE={se:.3f} MDE={mde:.3f} = {100*mde/abs(INS):.1f}% of in-samp mean')
t10d = pd.DataFrame(t10); t10d.to_csv(os.path.join(OUT, 't10_power.csv'), index=False)

# ======================================================================
# Render LaTeX for the four new tables (bodies straight from the CSVs)
# ======================================================================
# --- T7 hetero
body = ''
for _, r in t7.iterrows():
    body += (f"{r['moderator']} & {r['pp_lo']:+.3f}{stars(r['t_lo'])} & "
             f"{r['pp_int']:+.3f}{stars(r['t_int'])} & {r['decay_hi']:+.3f} & "
             f"{int(r['n_lo'])}/{int(r['n_hi'])} \\\\\n"
             f" & ({r['t_lo']:+.2f}) & ({r['t_int']:+.2f}) & & \\\\\n")
w('tab_hetero_ext.tex', r"""\begin{tabular}{lcccc}
\toprule
 & Post-pub. & Post-pub. & Post-pub. & Anom.\ \\
Moderator $M$ (obs., pre-set) & (low $M$) & $\times$ high $M$ & (high $M$) & lo/hi \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 stacked DiD
body = ''
for _, r in t8d.iterrows():
    body += (f"{r['spec']} & {r['did']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & "
             f"{int(r['ncohorts'])} & {int(r['N']):,} \\\\\n")
w('tab_stacked.tex', r"""\begin{tabular}{lcccc}
\toprule
Specification & Post$\times$Treated & $t$-stat & Cohorts & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 RI
body = ''
for _, r in t9.iterrows():
    body += (f"{r['estimand']} & {r['real']:+.4f} & {r['perm_mean']:+.4f} & "
             f"[{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] & {r['p_ri']:.3f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lcccc}
\toprule
Estimand & Actual & Placebo mean & Placebo 95\% interval & RI $p$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 power
body = ''
for _, r in t10d.iterrows():
    body += (f"{r['estimand']} & {r['coef']:+.3f} & {r['se']:.3f} & {r['mde']:.3f} & "
             f"{r['mde_pct_ins']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lcccc}
\toprule
Estimand & Coef. & SE & MDE(80\%) & \% of in-samp.\ mean \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose (so numbers in text also trace to code)
pd.DataFrame([{
    'ri_p_level': float(t9.iloc[0]['p_ri']), 'ri_p_incr': float(t9.iloc[1]['p_ri']),
    'ri_real_pp': real_pp, 'ri_real_g2': real_g2,
    'ri_placebo_g2_mean': float(perm_g2.mean()),
    'stack_did1': float(t8d.iloc[0]['did']), 'stack_t1': float(t8d.iloc[0]['t']),
    'stack_did2': float(t8d.iloc[1]['did']), 'stack_t2': float(t8d.iloc[1]['t']),
    'stack_ncohorts': n_cohorts,
    'mde_incr_pct': float(t10d.iloc[1]['mde_pct_ins']),
    'mde_h3_pct': float(t10d.iloc[2]['mde_pct_ins']),
}]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE -- extension tables t7-t10 + fig3 written.')
logf.close()
print('Extension tables written to', TEX)
