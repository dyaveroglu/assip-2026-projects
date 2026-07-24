#!/usr/bin/env python3
"""
Project 06 (Disaster housing & beliefs) — Step 40: journal-track extensions.

Adds four real tables that deepen the honest null WITHOUT touching the student's
reserved contribution (hand-collected graded landfall geography: distance-to-track,
peak wind, surge depth — STUDENT_TASKS.md Tasks 1-2). Everything here uses only
OBSERVABLE, pre-existing county data (pre-storm home-value level, pre-storm price
momentum, FEMA National Risk Index flood/overall scores, the coarse IHP treatment
already in the panel) and design-based inference. We never construct a graded
distance/intensity exposure or a corrected treatment set — those are the student's.

  t7_hetero.csv    Heterogeneity of the exposure DiD by observable pre-storm
                   moderators (pre-storm home-value level, price momentum, FEMA
                   flood risk, FEMA overall risk). Are hard-hit effects larger for
                   wealthier / higher-baseline-risk counties?
  t8_matched.csv   Matched DiD: nearest-neighbor match (within event, no replacement)
                   of each treated county to a control on pre-storm ln-ZHVI level and
                   pre-storm price momentum. Removes the wealth/momentum confound that
                   drives the raw Ian result; re-estimates baseline, detrended, and the
                   belief-split interaction on the balanced sample.
  t9_ri.csv        Randomization inference: 1,000 within-event permutations of the
                   treatment label (fixing #treated per storm). Design-based p-values
                   for the average DiD and the belief-split interaction. Writes
                   fig4_randinf.pdf.
  t10_power.csv    Minimum detectable effects (80% power) for the average, detrended,
                   and belief-conditional coefficients: shows the null is informative.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reads the same processed panel as 20_did.py.
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
OUT  = os.path.join(HERE, 'output', 'tables')
TEX  = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
LOG  = os.path.join(HERE, 'logs')
for d in (OUT, TEX, FIG): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)  # deterministic RI

p = pd.read_csv(os.path.join(PROC, 'panel.csv'),
                dtype={'fips': str, 'ce_id': str, 'em_id': str})
log(f'panel loaded: {len(p):,} rows, {p.ce_id.nunique()} county-events, {p.fips.nunique()} counties')

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

def twfe(df, xcols, month_fe=True, cluster='fips'):
    """County-event entity FE (+ event x calendar-month FE), SE clustered by county."""
    d = df.copy()
    d['emcode'] = pd.factorize(d['em_id'])[0]
    d = d.set_index(['ce_id', 'rel_month'])
    y = d['ln_zhvi']; X = d[xcols]
    other = d[['emcode']] if month_fe else None
    m = PanelOLS(y, X, entity_effects=True, other_effects=other, drop_absorbed=True)
    return m.fit(cov_type='clustered', clusters=d[cluster])

# ---------------------------------------------------------------------------
# County-event level pre-storm characteristics (observable, time-invariant).
# pre-storm level  = mean ln ZHVI over the 6 months before landfall
# pre-storm momentum = avg monthly ln change over the full pre window
# ---------------------------------------------------------------------------
pre = p[p.rel_month < 0].sort_values(['ce_id', 'rel_month'])
lvl = pre[pre.rel_month >= -6].groupby('ce_id')['ln_zhvi'].mean().rename('pre_level')
mom = pre.groupby('ce_id')['ln_zhvi'].agg(
        lambda s: (s.iloc[-1] - s.iloc[0]) / (len(s) - 1)).rename('pre_mom')
cec = p.drop_duplicates('ce_id')[['ce_id', 'event', 'treat', 'high_belief',
                                  'CFLD_RISKS', 'RISK_SCORE', 'per_gop']].copy()
cec = cec.merge(lvl, on='ce_id', how='left').merge(mom, on='ce_id', how='left')

# =====================================================================
# T7 — Heterogeneity by OBSERVABLE pre-storm moderators.
#   modhi = 1[moderator above within-event median]; did_m = treatpost*modhi.
#   Reported: base DiD (low-moderator group) and did_m (extra effect for the
#   high-moderator group) for ln ZHVI. All moderators are pre-existing county
#   characteristics — none is the student's graded exposure.
# =====================================================================
log('T7 heterogeneity by observable moderators ...')
MODS = [
    ('High pre-storm home value', 'pre_level'),
    ('High pre-storm price momentum', 'pre_mom'),
    ('High FEMA flood risk (NRI)', 'CFLD_RISKS'),
    ('High FEMA overall risk (NRI)', 'RISK_SCORE'),
]
# within-event median split, so the moderator is orthogonal to the storm dummy
cec2 = cec.copy()
for _, col in MODS:
    med = cec2.groupby('event')[col].transform('median')
    cec2[col + '_hi'] = (cec2[col] > med).astype('Int64')
h = p.merge(cec2[['ce_id'] + [c + '_hi' for _, c in MODS]], on='ce_id', how='left')
h7 = []
for name, col in MODS:
    hc = col + '_hi'
    d = h.dropna(subset=[hc]).copy()
    d[hc] = d[hc].astype(int)
    d['did_m'] = d['treatpost'] * d[hc]
    d['po_m']  = d['post'] * d[hc]
    r = twfe(d, ['treatpost', 'did_m', 'po_m'])
    h7.append({'moderator': name, 'base': r.params['treatpost'], 'base_t': r.tstats['treatpost'],
               'inter': r.params['did_m'], 'inter_t': r.tstats['did_m'],
               'inter_se': r.std_errors['did_m'], 'N': int(r.nobs)})
    log(f'  {name:32s} base={r.params["treatpost"]:+.4f}(t={r.tstats["treatpost"]:+.2f}) '
        f'x={r.params["did_m"]:+.4f}(t={r.tstats["did_m"]:+.2f})')
t7 = pd.DataFrame(h7); t7.to_csv(os.path.join(OUT, 't7_hetero.csv'), index=False)

# =====================================================================
# T8 — Matched DiD. NN 1:1 match treated->control WITHIN event (no replacement)
#   on standardized pre-storm level and pre-storm momentum, caliper 0.5 on the
#   Euclidean distance. If the raw Ian "effect" is a wealth/momentum confound it
#   should attenuate on the balanced sample; the belief interaction should not
#   survive either.
# =====================================================================
log('T8 matched DiD ...')
m = cec.dropna(subset=['pre_level', 'pre_mom']).copy()
# standardize the matching covariates within event
for col in ['pre_level', 'pre_mom']:
    m[col + '_z'] = m.groupby('event')[col].transform(lambda s: (s - s.mean()) / s.std())
CAL = 0.5
matched_ce = []
for ev in ['Ian', 'Helene']:
    me = m[m.event == ev]
    tr = me[me.treat == 1]; co = me[me.treat == 0].copy()
    used = set()
    for _, row in tr.iterrows():
        pool = co[~co.ce_id.isin(used)]
        if pool.empty: break
        dist = np.sqrt((pool.pre_level_z - row.pre_level_z) ** 2 +
                       (pool.pre_mom_z - row.pre_mom_z) ** 2)
        j = dist.idxmin()
        if dist.loc[j] <= CAL:
            used.add(co.loc[j, 'ce_id'])
            matched_ce += [row.ce_id, co.loc[j, 'ce_id']]
mp = p[p.ce_id.isin(matched_ce)].copy()
npair = len(matched_ce) // 2
log(f'  matched county-events: {len(matched_ce)} ({npair} pairs), rows={len(mp):,}')
# balance before / after (pre-storm level, in ln points)
def gap(frame, col):
    return frame[frame.treat == 1][col].mean() - frame[frame.treat == 0][col].mean()
gap_pre_lvl  = gap(m, 'pre_level'); gap_pre_mom = gap(m, 'pre_mom')
mm = m[m.ce_id.isin(matched_ce)]
gap_pst_lvl  = gap(mm, 'pre_level'); gap_pst_mom = gap(mm, 'pre_mom')
log(f'  level gap {gap_pre_lvl:+.3f} -> {gap_pst_lvl:+.3f}; '
    f'momentum gap {gap_pre_mom:+.5f} -> {gap_pst_mom:+.5f}')

t8 = []
# (a) baseline two-way FE DiD on matched sample
r = twfe(mp, ['treatpost'])
t8.append({'spec': 'Average DiD (matched)', 'coef': r.params['treatpost'],
           't': r.tstats['treatpost'], 'se': r.std_errors['treatpost'], 'N': int(r.nobs)})
# (b) detrended: + treated-specific linear trend
mp['treat_rel'] = mp.treat * mp.rel_month
r = twfe(mp, ['treatpost', 'treat_rel'])
t8.append({'spec': 'Detrended DiD (matched)', 'coef': r.params['treatpost'],
           't': r.tstats['treatpost'], 'se': r.std_errors['treatpost'], 'N': int(r.nobs)})
# (c) belief-split interaction on matched sample
mp['tp_high'] = mp.treatpost * mp.high_belief
mp['po_high'] = mp.post * mp.high_belief
r = twfe(mp, ['treatpost', 'tp_high', 'po_high'])
t8.append({'spec': 'Belief-split interaction (matched)', 'coef': r.params['tp_high'],
           't': r.tstats['tp_high'], 'se': r.std_errors['tp_high'], 'N': int(r.nobs)})
t8d = pd.DataFrame(t8); t8d.to_csv(os.path.join(OUT, 't8_matched.csv'), index=False)
pd.DataFrame([{'npairs': npair, 'gap_pre_lvl': gap_pre_lvl, 'gap_post_lvl': gap_pst_lvl,
               'gap_pre_mom': gap_pre_mom, 'gap_post_mom': gap_pst_mom}]
             ).to_csv(os.path.join(OUT, 't8_balance.csv'), index=False)

# =====================================================================
# T9 — Randomization inference (within-event permutation).
#   Permute the time-invariant treatment label WITHIN each event, holding the
#   number treated per storm fixed (Ian=29, Helene=187), rebuild treatpost, refit
#   the two-way FE panel. Design-based p = share |perm| >= |actual|.
#   Two estimands: the average DiD and the high-belief-split interaction (the
#   central test). Because the permutation preserves the Ian/Helene structure,
#   a CENTRAL actual value for the belief interaction means it is mechanical
#   storm geography, not a treatment response.
# =====================================================================
log('T9 randomization inference (1,000 within-event permutations) ...')
NP = 1000
ce_tab = p.drop_duplicates('ce_id')[['ce_id', 'event', 'treat', 'high_belief']].reset_index(drop=True)
ntr = {ev: int(ce_tab[(ce_tab.event == ev)].treat.sum()) for ev in ['Ian', 'Helene']}
log(f'  #treated per event held fixed: {ntr}')

# actual coefficients
p['tp_high'] = p.treatpost * p.high_belief
p['po_high'] = p.post * p.high_belief
act_avg = twfe(p, ['treatpost']).params['treatpost']
act_int = twfe(p, ['treatpost', 'tp_high', 'po_high']).params['tp_high']

perm_avg, perm_int = [], []
idx_by_ev = {ev: ce_tab.index[ce_tab.event == ev].to_numpy() for ev in ['Ian', 'Helene']}
for i in range(NP):
    lab = pd.Series(0, index=ce_tab.index)
    for ev in ['Ian', 'Helene']:
        idx = idx_by_ev[ev]
        chosen = np.random.choice(idx, ntr[ev], replace=False)
        lab.loc[chosen] = 1
    cmap = dict(zip(ce_tab.ce_id, lab.values))
    d = p.copy()
    d['tperm'] = d.ce_id.map(cmap)
    d['treatpost'] = d.tperm * d.post
    try:
        perm_avg.append(twfe(d, ['treatpost']).params['treatpost'])
        d['tp_high'] = d.treatpost * d.high_belief
        d['po_high'] = d.post * d.high_belief
        perm_int.append(twfe(d, ['treatpost', 'tp_high', 'po_high']).params['tp_high'])
    except Exception as e:
        log(f'   perm {i} skipped: {str(e)[:60]}')
    if (i + 1) % 200 == 0:
        log(f'   {i+1}/{NP} permutations done')
# restore actual treatpost on p (mutated in loop copies only, but be safe)
p['treatpost'] = p.treat * p.post

perm_avg = np.array(perm_avg); perm_int = np.array(perm_int)
def ri_row(name, actual, perms):
    p_ri = float(np.mean(np.abs(perms) >= abs(actual)))
    pct  = float(np.mean(perms <= actual)) * 100
    return {'estimand': name, 'actual': actual, 'p_ri': p_ri,
            'perm_q025': np.percentile(perms, 2.5), 'perm_q975': np.percentile(perms, 97.5),
            'pctile': pct, 'nperm': len(perms)}
ri = [ri_row('Average DiD (Treat$\\times$Post)', act_avg, perm_avg),
      ri_row('Belief-split interaction', act_int, perm_int)]
t9 = pd.DataFrame(ri); t9.to_csv(os.path.join(OUT, 't9_ri.csv'), index=False)
for r in ri:
    log(f'  {r["estimand"]:34s} actual={r["actual"]:+.4f} RI p={r["p_ri"]:.3f} '
        f'pctile={r["pctile"]:.1f} 95%[{r["perm_q025"]:+.4f},{r["perm_q975"]:+.4f}]')

# fig4: two-panel RI distributions
fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.2))
for ax, perms, actual, lab, ptitle in [
        (axes[0], perm_avg, act_avg, 'Average DiD', 'Average exposure effect'),
        (axes[1], perm_int, act_int, 'Belief interaction', 'Belief-split interaction')]:
    ax.hist(perms, bins=40, color='0.78', edgecolor='0.45', linewidth=0.4)
    prow = [x for x in ri if (x['estimand'].startswith('Average') and lab == 'Average DiD')
            or (x['estimand'].startswith('Belief') and lab == 'Belief interaction')][0]
    ax.axvline(actual, color='crimson', lw=2,
               label=f'Actual = {actual:+.3f}\n(RI $p$ = {prow["p_ri"]:.3f})')
    ax.axvline(0, color='0.3', lw=0.8, ls=':')
    ax.set_xlabel(f'Placebo coefficient under random treatment\n({ptitle.lower()})', fontsize=9)
    ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=8.5)
    ax.set_title(ptitle, fontsize=10)
fig.suptitle('Randomization inference: 1,000 within-event permutations of treatment', fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(os.path.join(FIG, 'fig4_randinf.pdf')); plt.close(fig)

# =====================================================================
# T10 — Minimum detectable effect (MDE) at 80% power.
#   MDE = (z_.975 + z_.80) * SE ~= 2.80 * SE. For a ln outcome, MDE*100 is the
#   detectable effect in PERCENT of home value. We benchmark it against (i) the
#   cross-county SD of the pre-to-post ln-ZHVI change, and (ii) the storm-level
#   effects we DO estimate (Ian +7.3%, Helene -1.1%).
# =====================================================================
log('T10 minimum detectable effects ...')
Z = 1.959964 + 0.841621
# cross-county SD of the post-minus-pre mean ln change (an economic yardstick)
prem = p[p.rel_month < 0].groupby('ce_id')['ln_zhvi'].mean()
pom  = p[p.rel_month >= 1].groupby('ce_id')['ln_zhvi'].mean()
chg  = (pom - prem).dropna()
sd_chg = chg.std()
t2 = pd.read_csv(os.path.join(OUT, 't2_did.csv'))
# SE for average (preferred, row 3) and detrended (row 7)
se_avg = float(t2.iloc[2]['se']); se_det = float(t2.iloc[6]['se'])
t3 = pd.read_csv(os.path.join(OUT, 't3_belief.csv'))
se_int = float(t3[t3.spec.str.contains('High-belief split') &
                  ~t3.spec.str.contains('detrended')]['inter_se'].iloc[0])
rows10 = [
    ('Average DiD (Treat$\\times$Post)', float(t2.iloc[2]['coef']), se_avg),
    ('Detrended DiD',                     float(t2.iloc[6]['coef']), se_det),
    ('Belief-split interaction',          float(t3[t3.spec.str.contains("High-belief split") &
                                                  ~t3.spec.str.contains("detrended")]['inter'].iloc[0]),
                                          se_int),
]
t10 = []
for name, coef, se in rows10:
    mde = Z * se
    t10.append({'estimand': name, 'coef': coef, 'se': se, 'mde': mde,
                'mde_pct_price': 100 * mde, 'mde_pct_sdchg': 100 * mde / sd_chg})
    log(f'  {name:34s} SE={se:.4f} MDE={mde:.4f} = {100*mde:.2f}% price, '
        f'{100*mde/sd_chg:.1f}% of SD(change)')
t10d = pd.DataFrame(t10); t10d.to_csv(os.path.join(OUT, 't10_power.csv'), index=False)
pd.DataFrame([{'sd_chg': sd_chg}]).to_csv(os.path.join(OUT, 't10_meta.csv'), index=False)

# =====================================================================
# Render LaTeX for the four new tables
# =====================================================================
# --- T7 hetero
body = ''
for _, r in t7.iterrows():
    body += (f"{r['moderator']} & {r['base']:+.4f}{stars(r['base_t'])} & ({r['base_t']:+.2f}) "
             f"& {r['inter']:+.4f}{stars(r['inter_t'])} & ({r['inter_t']:+.2f}) & {int(r['N'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lccccc}
\toprule
Moderator $M$ (pre-storm, within-event median split) & DiD & ($t$) & DiD$\times M$ & ($t$) & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 matched
bal = pd.read_csv(os.path.join(OUT, 't8_balance.csv')).iloc[0]
body = ''
for _, r in t8d.iterrows():
    body += f"{r['spec']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {r['se']:.4f} & {int(r['N'])} \\\\\n"
w('tab_matched.tex', r"""\begin{tabular}{lcccc}
\toprule
Specification (matched sample) & Coef. & ($t$) & SE & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 RI
body = ''
for _, r in t9.iterrows():
    body += (f"{r['estimand']} & {r['actual']:+.4f} & [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] "
             f"& {r['pctile']:.1f} & {r['p_ri']:.3f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lcccc}
\toprule
Estimand & Actual & Perm.\ 95\% interval & Pctile & RI $p$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 power
body = ''
for _, r in t10d.iterrows():
    body += (f"{r['estimand']} & {r['coef']:+.4f} & {r['se']:.4f} & {r['mde']:.4f} "
             f"& {r['mde_pct_price']:.2f}\\% & {r['mde_pct_sdchg']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lccccc}
\toprule
Estimand & Coef. & SE & MDE(80\%) & \% of price & \% of SD($\Delta$) \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{'npairs': int(bal['npairs']),
               'gap_pre_lvl': bal['gap_pre_lvl'], 'gap_post_lvl': bal['gap_post_lvl'],
               'ri_p_avg': ri[0]['p_ri'], 'ri_pct_avg': ri[0]['pctile'],
               'ri_p_int': ri[1]['p_ri'], 'ri_pct_int': ri[1]['pctile'],
               'matched_avg': float(t8d.iloc[0]['coef']), 'matched_avg_t': float(t8d.iloc[0]['t']),
               'matched_int': float(t8d.iloc[2]['coef']), 'matched_int_t': float(t8d.iloc[2]['t']),
               'mde_avg_pct': 100 * Z * se_avg, 'mde_int_pct': 100 * Z * se_int,
               'sd_chg': sd_chg}]
             ).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE — extension tables (t7-t10) + fig4 written.')
logf.close()
print('Extension tables written to', TEX)
