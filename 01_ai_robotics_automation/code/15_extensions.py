#!/usr/bin/env python3
"""
Project 01 (AI vs Robotics automation) — Step 15: journal-track extensions.

Adds four real tables that deepen the two headline findings (cognitive/AI patents
travel with EMPLOYMENT growth; physical/robotics patents travel with firm VALUE)
without touching the student's reserved contribution. The reserved task is
hand-READING each robotics patent to code it labor-REPLACING vs labor-AUGMENTING
(STUDENT_TASKS Task 2). Everything here uses only OBSERVABLE firm characteristics
(industry, size, R&D activity) and design-based inference; none of it constructs
or proxies the replacing/augmenting label, which remains the student's next step.

  t5_hetero.csv   Heterogeneity of the two headline elasticities by observable
                  pre-sample moderators (manufacturing, high-tech, large firm,
                  R&D-active): does AI-employment complementarity / robotics-value
                  capitalization vary across firm types?
  t6_altfe.csv    Alternative identification: the AI->employment and robotics->Q
                  elasticities under industry x year FE, added accounting controls,
                  dropped size control, and a modern-era (>=2005) subsample.
  t7_ri.csv       Randomization inference: 500 permutations of the firm-level AI
                  trajectory (donor firm's ln_ai remapped by calendar year); a
                  design-based p-value for the headline ln_ai->ln_emp coefficient.
                  Also writes fig2_randinf.pdf. Perm-mean ~ 0 is the sanity check.
  t8_power.csv    Minimum detectable effects (80% power) per treatment x outcome:
                  shows the genuine nulls (robotics->employment, robotics->ROA,
                  AI->firm value question) are informative, not merely underpowered.

Also renders an event-study coefficient table (tab_eventstudy.tex) from the
existing t3_eventstudy.csv. Every number is written to output/tables/*.csv and
rendered to paper/tables/*.tex so the paper cannot drift from the code.
Reads the same shared analytical panel as 10_analysis.py.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels import PanelOLS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH   = '/mnt/d/ccli/assip26/data'
OUT  = os.path.join(HERE, 'output', 'tables')
TEX  = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
for d in (OUT, TEX, FIG): os.makedirs(d, exist_ok=True)
LOG  = os.path.join(HERE, 'logs'); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line, flush=True); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)  # deterministic randomization inference

p = pd.read_csv(os.path.join(SH, 'patent_analytical_panel.csv'))
log(f'panel: {len(p):,} firm-years, {p.permno.nunique():,} firms')

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

def fe(y, xs, data, entity='permno', time=True, other=None):
    """Two-way FE panel (firm + year) with firm-clustered SE; optional other_effects."""
    cols = [y] + xs + ([] if other is None else [other])
    d = data.dropna(subset=cols).copy().set_index([entity, 'year'])
    kw = dict(entity_effects=True, drop_absorbed=True, check_rank=False)
    if other is not None:
        kw['other_effects'] = d[other]
    else:
        kw['time_effects'] = time
    return PanelOLS(d[y], d[xs], **kw).fit(cov_type='clustered', cluster_entity=True)

# =====================================================================
# Firm-level OBSERVABLE moderators (time-invariant; absorbed by firm FE,
# so only their interaction with the patent stock is identified).
#   - Manufacturing (SIC 2000-3999)          - High-tech industry (SIC3 set)
#   - Large firm (above-median firm-mean size) - R&D-active (ever xrd>0)
# All are industry/size/accounting attributes, deliberately ORTHOGONAL to the
# reserved replacing-vs-augmenting patent coding.
# =====================================================================
firm_sic = p.dropna(subset=['sich']).sort_values('year').groupby('permno')['sich'].first()
HITECH3 = {357, 366, 367, 737, 384, 283, 873, 481, 372, 386}  # computers, comm, electronics, software, instruments, drugs, R&D svcs, telecom, aero, photo
attr = pd.DataFrame({'sich0': firm_sic})
attr['manuf']  = ((attr.sich0 >= 2000) & (attr.sich0 < 4000)).astype(int)
attr['hitech'] = (attr.sich0 // 10).isin(HITECH3).astype(int)
firm_size = p.groupby('permno')['size'].mean()
attr['large']  = (firm_size > firm_size.median()).astype(int)
firm_rd = p.assign(rdpos=(p.xrd.fillna(0) > 0)).groupby('permno')['rdpos'].max()
attr['rd_active'] = firm_rd.astype(int)
attr = attr.reset_index()
pm = p.merge(attr[['permno', 'manuf', 'hitech', 'large', 'rd_active']], on='permno', how='left')

# =====================================================================
# T5 — Heterogeneity of the two headline elasticities by observable moderator.
#   AI->employment:  ln_emp on ln_ai, ln_ai*M, ln_rob, size (+FE)
#   Robotics->value: tobinq on ln_rob, ln_rob*M, ln_ai, size (+FE)
# =====================================================================
log('T5 heterogeneity by observable moderators ...')
MODS = [('Manufacturing (SIC 2000-3999)', 'manuf'),
        ('High-tech industry',            'hitech'),
        ('Large firm (above-median size)','large'),
        ('R\\&D-active firm',             'rd_active')]
h5 = []
for name, m in MODS:
    d = pm.dropna(subset=[m]).copy()
    d['ai_m']  = d['ln_ai'] * d[m]
    d['rob_m'] = d['ln_rob'] * d[m]
    # AI -> employment
    ra = fe('ln_emp', ['ln_ai', 'ai_m', 'ln_rob', 'size'], d)
    # Robotics -> Tobin's Q
    rq = fe('tobinq', ['ln_rob', 'rob_m', 'ln_ai', 'size'], d)
    h5.append({'moderator': name,
               'ai_base': ra.params['ln_ai'],   'ai_base_t': ra.tstats['ln_ai'],
               'ai_int':  ra.params['ai_m'],    'ai_int_t':  ra.tstats['ai_m'],
               'rob_base': rq.params['ln_rob'], 'rob_base_t': rq.tstats['ln_rob'],
               'rob_int':  rq.params['rob_m'],  'rob_int_t':  rq.tstats['rob_m'],
               'N': int(ra.nobs)})
    log(f'  {name:32s} AI_emp base={ra.params["ln_ai"]:+.4f}(t={ra.tstats["ln_ai"]:+.2f}) '
        f'x={ra.params["ai_m"]:+.4f}(t={ra.tstats["ai_m"]:+.2f}) | '
        f'Rob_Q base={rq.params["ln_rob"]:+.3f}(t={rq.tstats["ln_rob"]:+.2f}) '
        f'x={rq.params["rob_m"]:+.3f}(t={rq.tstats["rob_m"]:+.2f})')
t5 = pd.DataFrame(h5); t5.to_csv(os.path.join(OUT, 't5_hetero.csv'), index=False)

# =====================================================================
# T6 — Alternative identification for the two headlines.
#   Columns: AI->employment elasticity and robotics->value elasticity under
#   progressively demanding specifications. (Firm linear trends are deliberately
#   NOT used: they are near-collinear with a monotonically accumulating patent
#   stock and would absorb the effect mechanically.)
# =====================================================================
log('T6 alternative fixed effects / identification ...')
p6 = pm.copy()
p6['sic2'] = (p6['sich'] // 100)
p6['iyr'] = p6['sic2'].astype('Int64').astype(str) + '_' + p6['year'].astype(str)
SPECS = [
    ('Baseline (firm + year FE)',        dict(xs=['ln_ai', 'ln_rob', 'size'])),
    ('+ Industry$\\times$year FE',       dict(xs=['ln_ai', 'ln_rob', 'size'], other='iyr')),
    ('+ Accounting controls (ROA, lev.)',dict(xs=['ln_ai', 'ln_rob', 'size', 'roa', 'lev'])),
    ('Drop size control',                dict(xs=['ln_ai', 'ln_rob'])),
    ('Modern era (year $\\geq$ 2005)',   dict(xs=['ln_ai', 'ln_rob', 'size'], sub=lambda x: x.year >= 2005)),
]
t6 = []
for name, cfg in SPECS:
    data = p6[cfg['sub'](p6)] if 'sub' in cfg else p6
    re_emp = fe('ln_emp', cfg['xs'], data, other=cfg.get('other'))
    re_q   = fe('tobinq', cfg['xs'], data, other=cfg.get('other'))
    t6.append({'spec': name,
               'ai_emp': re_emp.params['ln_ai'], 'ai_emp_t': re_emp.tstats['ln_ai'],
               'rob_q':  re_q.params['ln_rob'],  'rob_q_t':  re_q.tstats['ln_rob'],
               'N': int(re_emp.nobs)})
    log(f'  {name:34s} AI->emp={re_emp.params["ln_ai"]:+.4f}(t={re_emp.tstats["ln_ai"]:+.2f}) '
        f'Rob->Q={re_q.params["ln_rob"]:+.3f}(t={re_q.tstats["ln_rob"]:+.2f}) N={int(re_emp.nobs)}')
t6d = pd.DataFrame(t6); t6d.to_csv(os.path.join(OUT, 't6_altfe.csv'), index=False)

# =====================================================================
# T7 — Randomization inference for the headline ln_ai -> ln_emp coefficient.
#   Sharp null: a firm's AI-patent trajectory has no effect on its employment.
#   Each permutation reassigns firm i the AI trajectory of a donor firm pi(i),
#   remapped by CALENDAR YEAR (inner join), keeping firm i's own outcome,
#   robotics stock, size, and fixed effects. After two-way demeaning the
#   permutation distribution is centered at zero under the sharp null; the
#   actual +0.055 landing far outside is a design-based confirmation.
# =====================================================================
log('T7 randomization inference (permute firm-level AI trajectory) ...')
base = p.dropna(subset=['ln_emp', 'ln_ai', 'ln_rob', 'size']).copy()
base = base[['permno', 'year', 'ln_emp', 'ln_ai', 'ln_rob', 'size']]
ai_long = base[['permno', 'year', 'ln_ai']].rename(columns={'permno': 'donor', 'ln_ai': 'ln_ai_p'})
oth = base[['permno', 'year', 'ln_emp', 'ln_rob', 'size']]     # firm keeps its own outcome/covariates
firms = np.sort(base.permno.unique())

def coef_ln_ai(dat):
    d = dat.set_index(['permno', 'year'])
    r = PanelOLS(d['ln_emp'], d[['ln_ai', 'ln_rob', 'size']],
                 entity_effects=True, time_effects=True, drop_absorbed=True,
                 check_rank=False).fit(cov_type='clustered', cluster_entity=True)
    return r.params['ln_ai']

actual = coef_ln_ai(base.rename(columns={'ln_ai': 'ln_ai'}))
log(f'  actual ln_ai->ln_emp coef = {actual:+.5f}')
NPERM = 500
perms = []
for i in range(NPERM):
    donor = np.random.permutation(firms)
    mp = pd.DataFrame({'permno': firms, 'donor': donor})
    dd = oth.merge(mp, on='permno', how='left').merge(ai_long, on=['donor', 'year'], how='inner')
    dd = dd.rename(columns={'ln_ai_p': 'ln_ai'})[['permno', 'year', 'ln_emp', 'ln_ai', 'ln_rob', 'size']]
    try:
        perms.append(coef_ln_ai(dd))
    except Exception as e:
        if i < 3: log(f'    perm {i} ERR {str(e)[:60]}')
perms = np.array(perms)
p_ri = float(np.mean(np.abs(perms) >= abs(actual)))
log(f'  perms={len(perms)} mean={perms.mean():+.5f} (sanity: ~0) sd={perms.std():.5f} '
    f'95%=[{np.percentile(perms,2.5):+.5f},{np.percentile(perms,97.5):+.5f}] RI p={p_ri:.4f}')
t7 = pd.DataFrame([{'outcome': 'ln(Employment)', 'treatment': 'ln(1+AI stock)',
                    'actual': actual, 'perm_mean': perms.mean(), 'perm_sd': perms.std(),
                    'perm_q025': np.percentile(perms, 2.5), 'perm_q975': np.percentile(perms, 97.5),
                    'p_ri': p_ri, 'nperm': len(perms)}])
t7.to_csv(os.path.join(OUT, 't7_ri.csv'), index=False)

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(perms, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(actual, color='crimson', lw=2,
           label=f'Actual coef. = {actual:+.3f}\n(RI $p$ = {p_ri:.3f})')
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo AI-stock coefficient on ln(Employment)\nunder permuted firm AI trajectories')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Randomization inference: 500 permutations of the firm AI trajectory', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig2_randinf.pdf')); plt.close(fig)

# =====================================================================
# T8 — Minimum detectable effects (MDE) at 80% power, per treatment x outcome.
#   MDE = (z_.975 + z_.80) * SE ~= 2.80 * SE(coef). Expressed as a share of the
#   outcome's cross-firm SD. A small MDE/SD on the genuine nulls (robotics->
#   employment, robotics->ROA, AI->value) shows they are informative, not
#   underpowered: an elasticity that size would have been detected.
# =====================================================================
log('T8 minimum detectable effects ...')
Z = 1.959964 + 0.841621
OUTC = [('ln_emp', 'ln(Employment)'), ('ln_prod', 'ln(Sales/Emp)'),
        ('roa', 'ROA'), ('tobinq', "Tobin's Q")]
t8 = []
for y, ylab in OUTC:
    r = fe(y, ['ln_ai', 'ln_rob', 'size'], p)
    ysd = p[y].std()
    for tv, tlab in [('ln_ai', 'AI stock'), ('ln_rob', 'Robotics stock')]:
        coef = r.params[tv]; se = r.std_errors[tv]; tstat = r.tstats[tv]
        mde = Z * se
        t8.append({'outcome': ylab, 'treatment': tlab, 'coef': coef, 'se': se,
                   't': tstat, 'mde': mde, 'mde_pct_sd': 100 * mde / ysd,
                   'sig': abs(tstat) >= 1.96})
        log(f'  {ylab:15s} <- {tlab:15s} coef={coef:+.4f} SE={se:.4f} '
            f'MDE={mde:.4f}={100*mde/ysd:.1f}% of outcome SD  {"[NULL]" if abs(tstat)<1.96 else ""}')
t8d = pd.DataFrame(t8); t8d.to_csv(os.path.join(OUT, 't8_power.csv'), index=False)

# =====================================================================
# Render LaTeX for the new tables (+ an event-study coefficient table)
# =====================================================================
# --- tab_eventstudy: AI first-patent event study (from existing t3) ---
es = pd.read_csv(os.path.join(OUT, 't3_eventstudy.csv'))
emp = es[es.outcome == 'ln(Employment)'].sort_values('k')
prod = es[es.outcome == 'ln(Sales/Emp)'].sort_values('k')
body = ''
for k in range(-5, 6):
    re = emp[emp.k == k].iloc[0]; rp = prod[prod.k == k].iloc[0]
    if k == -1:
        body += f"$k={k}$ (base) & --- & --- & --- & --- \\\\\n"
    else:
        body += (f"$k={k:+d}$ & {re['coef']:+.4f}{stars(re['t'])} & ({re['t']:+.2f}) "
                 f"& {rp['coef']:+.4f}{stars(rp['t'])} & ({rp['t']:+.2f}) \\\\\n")
w('tab_eventstudy.tex', r"""\begin{tabular}{lcccc}
\toprule
& \multicolumn{2}{c}{ln(Employment)} & \multicolumn{2}{c}{ln(Sales/Emp)} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Event time $k$ & Coef. & $t$-stat & Coef. & $t$-stat \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- tab_hetero (T5) ---
body = ''
for _, r in t5.iterrows():
    body += (f"{r['moderator']} & {r['ai_base']:+.4f}{stars(r['ai_base_t'])} & "
             f"{r['ai_int']:+.4f}{stars(r['ai_int_t'])} & "
             f"{r['rob_base']:+.3f}{stars(r['rob_base_t'])} & "
             f"{r['rob_int']:+.3f}{stars(r['rob_int_t'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lcccc}
\toprule
& \multicolumn{2}{c}{AI stock $\to$ ln(Emp.)} & \multicolumn{2}{c}{Robotics stock $\to$ Q} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Moderator $M$ & Base & $\times M$ & Base & $\times M$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- tab_altfe (T6) ---
body = ''
for _, r in t6d.iterrows():
    body += (f"{r['spec']} & {r['ai_emp']:+.4f}{stars(r['ai_emp_t'])} & ({r['ai_emp_t']:+.2f}) "
             f"& {r['rob_q']:+.3f}{stars(r['rob_q_t'])} & ({r['rob_q_t']:+.2f}) & {r['N']:,} \\\\\n")
w('tab_altfe.tex', r"""\begin{tabular}{lccccc}
\toprule
& \multicolumn{2}{c}{AI $\to$ ln(Emp.)} & \multicolumn{2}{c}{Robotics $\to$ Q} & \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Specification & Coef. & $t$-stat & Coef. & $t$-stat & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- tab_ri (T7) ---
r = t7.iloc[0]
p_disp = f"$<${1.0/max(r['nperm'],1):.3f}" if r['p_ri'] == 0 else f"{r['p_ri']:.3f}"
w('tab_ri.tex', r"""\begin{tabular}{lccccc}
\toprule
Coefficient & Actual & Perm.\ mean & Perm.\ SD & Perm.\ 95\% interval & RI $p$ \\
\midrule
""" + (f"AI stock $\\to$ ln(Emp.) & {r['actual']:+.4f} & {r['perm_mean']:+.4f} & {r['perm_sd']:.4f} "
       f"& [{r['perm_q025']:+.4f}, {r['perm_q975']:+.4f}] & {p_disp} \\\\\n") + r"""\bottomrule
\end{tabular}""")

# --- tab_power (T8) ---
body = ''
for _, r in t8d.iterrows():
    tag = '' if r['sig'] else ' (null)'
    body += (f"{r['outcome']} & {r['treatment']}{tag} & {r['coef']:+.4f} & {r['se']:.4f} "
             f"& {r['mde']:.4f} & {r['mde_pct_sd']:.1f}\\% \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{llcccc}
\toprule
Outcome & Treatment & Coef. & SE & MDE(80\%) & \% of outcome SD \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([{'ri_actual': actual, 'ri_p': p_ri, 'ri_perm_mean': perms.mean(),
               'ri_q025': np.percentile(perms, 2.5), 'ri_q975': np.percentile(perms, 97.5),
               'altfe_ai_iy': float(t6d.iloc[1]['ai_emp']), 'altfe_ai_iy_t': float(t6d.iloc[1]['ai_emp_t']),
               'altfe_rob_iy': float(t6d.iloc[1]['rob_q']), 'altfe_rob_iy_t': float(t6d.iloc[1]['rob_q_t']),
               'mde_rob_emp': float(t8d[(t8d.outcome=='ln(Employment)')&(t8d.treatment=='Robotics stock')]['mde_pct_sd'].iloc[0]),
               'mde_rob_roa': float(t8d[(t8d.outcome=='ROA')&(t8d.treatment=='Robotics stock')]['mde_pct_sd'].iloc[0])
               }]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE — extension tables (t5-t8) + tab_eventstudy + fig2_randinf written.')
logf.close()
print('Extension tables written to', TEX)
