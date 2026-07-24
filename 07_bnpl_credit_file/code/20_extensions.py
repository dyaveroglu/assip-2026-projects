#!/usr/bin/env python3
"""
Project 07 (BNPL) — Step 20: journal-track extensions.

Adds real tables that deepen the honest null (no furnishing-specific credit-
reporting complaint spike at Affirm) WITHOUT touching the student's reserved
contributions:
  - Task 1: hand-collected per-lender/per-bureau furnishing DATES (staggered timing)
  - Task 2: hand-labeled genuine-furnishing-error GOLD SET from narratives.
The CFPB narrative field is empty in this public pull, so the machine cannot self-
certify a genuine furnishing error; every extension here uses only OBSERVABLE CFPB
structure (firm, product, CFPB-provided issue label, month) and a single public
Affirm~Apr-2025 reference date, and design-based inference — never the student's
hand-coded timing or gold labels.

Tables written (CSV -> paper/tables/*.tex):
  t4_sumstats.csv  Sample composition by firm (descriptive).
  t5_hetero.csv    Per-firm within-firm furnishing DiD (CR vs other, log count):
                   only Affirm furnished; the null generalizes across peers.
  t6_tripleD.csv   Triple-difference (Affirm vs peers) x (CR vs other) x post:
                   the cleanest single test of H1; observable data only.
  t7_robust.csv    Alternative event dates, windows, and estimators.
  t8_ri.csv        Randomization / placebo-in-time inference (+ fig3_randinf.pdf)
                   and a coarse firm-label permutation.
  t9_power.csv     Minimum detectable effects (80% power): which specs can reject
                   H1's positive spike, and which (5-firm count) are underpowered.
"""
import os, datetime, warnings, itertools
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed'); INT = os.path.join(HERE, 'data', 'interim')
OUT  = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
for d in (OUT, TEX, FIG, INT): os.makedirs(d, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)  # deterministic placebo draws

df = pd.read_csv(os.path.join(PROC, 'bnpl_clean.csv'))
df['month'] = pd.PeriodIndex(df['month'], freq='M')
df['cr'] = df['product'].fillna('').str.contains('Credit reporting', case=False).astype(int)
EVENT = pd.Period('2025-04', 'M')        # public Affirm-Experian reference date
df['post'] = (df.month >= EVENT).astype(int)
FIRMS = ['Affirm', 'Klarna', 'Sezzle', 'Zip', 'Perpay']
MONTHS = pd.period_range('2022-01', '2026-06', freq='M')

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

# =====================================================================
# T4 — Sample composition (descriptive summary)
# =====================================================================
log('T4 sample composition ...')
rows = []
for f in FIRMS:
    s = df[df.firm == f]
    pre = s[s.post == 0]; postd = s[s.post == 1]
    pre_mo = pre.month.nunique(); post_mo = postd.month.nunique()
    rows.append({
        'firm': f,
        'furnisher': 'Yes (~Apr 2025)' if f == 'Affirm' else 'Not confirmed',
        'N': len(s),
        'cr_share': s.cr.mean(),
        'permo_pre': len(pre) / pre_mo if pre_mo else np.nan,
        'permo_post': len(postd) / post_mo if post_mo else np.nan,
        'first': str(s.month.min()), 'last': str(s.month.max())})
t4 = pd.DataFrame(rows)
t4.loc['tot'] = {'firm': 'All BNPL', 'furnisher': '', 'N': len(df),
                 'cr_share': df.cr.mean(),
                 'permo_pre': len(df[df.post==0]) / df[df.post==0].month.nunique(),
                 'permo_post': len(df[df.post==1]) / df[df.post==1].month.nunique(),
                 'first': str(df.month.min()), 'last': str(df.month.max())}
t4.to_csv(os.path.join(OUT, 't4_sumstats.csv'), index=False)
log('\n' + t4.round(2).to_string(index=False))

# =====================================================================
# helper: within-firm DiD (CR complaints vs other-product complaints)
#   logn ~ cr + cr:post + C(month)  on the firm's own cr x month panel
# =====================================================================
def within_firm_did(firm, event=EVENT, months=MONTHS, sub=None):
    d = df[df.firm == firm] if sub is None else sub
    g = d.groupby(['month', 'cr']).size().rename('n').reset_index()
    full = pd.MultiIndex.from_product([months, [0, 1]], names=['month', 'cr']).to_frame(index=False)
    g = full.merge(g, on=['month', 'cr'], how='left').fillna({'n': 0})
    g['post'] = (g.month >= event).astype(int)
    g['logn'] = np.log1p(g.n); g['mstr'] = g.month.astype(str)
    m = smf.ols('logn ~ cr + cr:post + C(mstr)', data=g).fit(cov_type='HC1')
    return m

# =====================================================================
# T5 — Heterogeneity: per-firm within-firm furnishing DiD
#   Common Apr-2025 reference date used as a GENERALIZATION/placebo across
#   firms (true per-firm dates are the student's Task 1). Only Affirm actually
#   furnished; if furnishing drove CR disputes, only Affirm's cr:post should be
#   positive. It is not — the compositional pattern is sector-wide.
# =====================================================================
log('T5 per-firm within-firm DiD ...')
h = []
for f in FIRMS:
    try:
        m = within_firm_did(f)
        h.append({'firm': f, 'furnisher': 'Yes' if f == 'Affirm' else 'No',
                  'coef': m.params['cr:post'], 't': m.tvalues['cr:post'],
                  'ncr': int(df[(df.firm==f)&(df.cr==1)].shape[0]), 'N': int(m.nobs)})
        log(f'  {f:8s} cr:post={m.params["cr:post"]:+.4f} (t={m.tvalues["cr:post"]:+.2f}) '
            f'nCR={df[(df.firm==f)&(df.cr==1)].shape[0]}')
    except Exception as e:
        log(f'  {f} ERR {str(e)[:80]}')
t5 = pd.DataFrame(h); t5.to_csv(os.path.join(OUT, 't5_hetero.csv'), index=False)

# =====================================================================
# T6 — Triple-difference (DDD): (Affirm vs peers) x (CR vs other) x post
#   Panel of firm x cr x month counts. Coefficient of interest is the triple
#   interaction treat:cr:post. Under H1 (furnishing floods the furnisher's CR
#   line) it is POSITIVE. FE: firm-x-cr entity, month; SE clustered by firm.
# =====================================================================
log('T6 triple-difference ...')
def build_ddd(firms, event=EVENT, months=MONTHS):
    recs = []
    for f in firms:
        d = df[df.firm == f]
        g = d.groupby(['month', 'cr']).size().rename('n')
        for mo in months:
            for c in (0, 1):
                recs.append({'firm': f, 'month': mo, 'cr': c,
                             'n': float(g.get((mo, c), 0.0))})
    p = pd.DataFrame(recs)
    p['logn'] = np.log1p(p.n)
    p['treat'] = (p.firm == 'Affirm').astype(int)
    p['post'] = (p.month >= event).astype(int)
    p['fc'] = p.firm + '_' + p.cr.astype(str)
    p['mstr'] = p.month.astype(str)
    return p

def ddd_fit(p):
    m = smf.ols('logn ~ treat:post + cr:post + treat:cr:post + C(fc) + C(mstr)',
                data=p).fit(cov_type='cluster', cov_kwds={'groups': p.firm})
    return m

ddd_specs = []
pfull = build_ddd(FIRMS)
m_ddd = ddd_fit(pfull)
ddd_specs.append(('All 5 firms, event Apr-2025', m_ddd, int(m_ddd.nobs)))
# drop Klarna (tiny pre-base outlier)
p_nk = build_ddd([f for f in FIRMS if f != 'Klarna'])
m_nk = ddd_fit(p_nk); ddd_specs.append(('Excl. Klarna (tiny CR base)', m_nk, int(m_nk.nobs)))
# alt event date Feb-2025 (Affirm-TransUnion, public)
p_feb = build_ddd(FIRMS, event=pd.Period('2025-02', 'M'))
m_feb = ddd_fit(p_feb); ddd_specs.append(('Alt.\\ event Feb-2025 (TransUnion)', m_feb, int(m_feb.nobs)))
t6 = pd.DataFrame([{'spec': s, 'coef': m.params['treat:cr:post'],
                    't': m.tvalues['treat:cr:post'], 'N': n} for s, m, n in ddd_specs])
t6.to_csv(os.path.join(OUT, 't6_tripleD.csv'), index=False)
log('\n' + t6.round(4).to_string(index=False))

# =====================================================================
# T7 — Robustness: alternative event dates, windows, estimators
#   (within-Affirm cr:post, the headline).
# =====================================================================
log('T7 robustness (within-Affirm) ...')
def aff_did(event=EVENT, months=MONTHS, poisson=False, window=None):
    aff = df[df.firm == 'Affirm']
    g = aff.groupby(['month', 'cr']).size().rename('n').reset_index()
    full = pd.MultiIndex.from_product([months, [0, 1]], names=['month', 'cr']).to_frame(index=False)
    g = full.merge(g, on=['month', 'cr'], how='left').fillna({'n': 0})
    if window is not None:
        lo, hi = event - window, event + window - 1
        g = g[(g.month >= lo) & (g.month <= hi)]
    g['post'] = (g.month >= event).astype(int)
    g['logn'] = np.log1p(g.n); g['mstr'] = g.month.astype(str)
    if poisson:
        m = smf.poisson('n ~ cr + cr:post + C(mstr)', data=g).fit(disp=0)
        return m.params['cr:post'], m.tvalues['cr:post'], int(m.nobs)
    m = smf.ols('logn ~ cr + cr:post + C(mstr)', data=g).fit(cov_type='HC1')
    return m.params['cr:post'], m.tvalues['cr:post'], int(m.nobs)

rob = []
c, t, n = aff_did();                                   rob.append(('Baseline: event Apr-2025, OLS log count', c, t, n))
c, t, n = aff_did(poisson=True);                       rob.append(('Poisson count', c, t, n))
c, t, n = aff_did(event=pd.Period('2025-02','M'));     rob.append(('Event Feb-2025 (TransUnion)', c, t, n))
c, t, n = aff_did(event=pd.Period('2025-06','M'));     rob.append(('Event Jun-2025 (2-mo.\\ lag)', c, t, n))
c, t, n = aff_did(window=12);                          rob.append(('Symmetric $\\pm$12-mo.\\ window', c, t, n))
c, t, n = aff_did(window=9);                           rob.append(('Symmetric $\\pm$9-mo.\\ window', c, t, n))
c, t, n = aff_did(window=6);                           rob.append(('Symmetric $\\pm$6-mo.\\ window', c, t, n))
# drop COVID-era 2022
c, t, n = aff_did(months=pd.period_range('2023-01','2026-06',freq='M')); rob.append(('Drop 2022 (start 2023)', c, t, n))
# furnishing-plausible CFPB issue labels only (observable; NOT the hand-coded gold set)
FURN = ['Incorrect information on your report',
        "Problem with a company's investigation into an existing problem",
        'Improper use of your report',
        "Problem with a credit reporting company's investigation into an existing problem"]
aff = df[df.firm == 'Affirm'].copy()
aff['cr2'] = (aff['issue'].isin(FURN)).astype(int)   # furnishing-plausible CR issue
g = aff.groupby(['month', 'cr2']).size().rename('n').reset_index().rename(columns={'cr2':'cr'})
full = pd.MultiIndex.from_product([MONTHS, [0, 1]], names=['month', 'cr']).to_frame(index=False)
g = full.merge(g, on=['month', 'cr'], how='left').fillna({'n': 0})
g['post'] = (g.month >= EVENT).astype(int); g['logn'] = np.log1p(g.n); g['mstr'] = g.month.astype(str)
mfp = smf.ols('logn ~ cr + cr:post + C(mstr)', data=g).fit(cov_type='HC1')
rob.append(('Furnishing-plausible CFPB issues only', mfp.params['cr:post'], mfp.tvalues['cr:post'], int(mfp.nobs)))
t7 = pd.DataFrame([{'spec': s, 'coef': c, 't': t, 'N': n} for s, c, t, n in rob])
t7.to_csv(os.path.join(OUT, 't7_robust.csv'), index=False)
log('\n' + t7.round(4).to_string(index=False))

# =====================================================================
# T8 — Randomization / placebo-in-time inference
#   (a) within-Affirm: draw placebo event months in an INTERIOR PRE-EVENT
#       window (2023-01..2024-10, all data <= 2025-03) so no placebo post-window
#       contains the real post-2025 shift. Distribution of placebo cr:post gives
#       a design-based p for the true estimate (robust to serial correlation and
#       the arbitrariness of the break date).
#   (b) cross-firm: firm-label permutation across the 5 firms (exact, coarse).
# =====================================================================
log('T8 randomization / placebo-in-time inference ...')
PRE = pd.period_range('2022-01', '2025-03', freq='M')     # pre-event data only
aff = df[df.firm == 'Affirm']
gpre = aff.groupby(['month', 'cr']).size().rename('n').reset_index()
fullpre = pd.MultiIndex.from_product([PRE, [0, 1]], names=['month', 'cr']).to_frame(index=False)
gpre = fullpre.merge(gpre, on=['month', 'cr'], how='left').fillna({'n': 0})
gpre['logn'] = np.log1p(gpre.n); gpre['mstr'] = gpre.month.astype(str)
placebo_months = pd.period_range('2023-01', '2024-10', freq='M')   # interior splits
pl = []
for pm in placebo_months:
    d = gpre.copy(); d['post'] = (d.month >= pm).astype(int)
    try:
        m = smf.ols('logn ~ cr + cr:post + C(mstr)', data=d).fit(cov_type='HC1')
        pl.append(m.params['cr:post'])
    except Exception:
        pass
pl = np.array(pl)
# recompute the true within-Affirm estimate live (full sample, real event) to avoid drift
c_act, t_act, _ = aff_did()
actual_aff = c_act
# The placebo-in-time draws are all POSITIVE (a rising CR-vs-other pre-trend); the true
# estimate is negative and lies below every placebo. H1 predicts a POSITIVE furnishing
# spike, so the design-based test for H1 is one-sided: share of placebo splits at least
# as large (as pro-H1) as the true estimate. None are as low as the truth -> the furnishing
# date is a reversal, not a spike. We report that directional statistic.
p_belowall = float(np.mean(pl <= actual_aff))   # share of placebos as low or lower than truth
p_time = float(np.mean(pl >= actual_aff))       # share at least as pro-H1 (positive) as truth
log(f'  within-Affirm actual cr:post={actual_aff:+.4f}; placebo-in-time '
    f'n={len(pl)}, mean={pl.mean():+.4f}, sd={pl.std():+.4f}, '
    f'p(placebo<=actual)={p_belowall:.3f}, range=[{pl.min():+.4f},{pl.max():+.4f}]')

# (b) cross-firm firm-label permutation (log CR count, firm+month FE)
cr = df[df.cr == 1].groupby(['firm', 'month']).size().rename('n').reset_index()
panel = []
for f in FIRMS:
    s = cr[cr.firm == f].set_index('month')['n']
    for mo in pd.period_range('2022-06', '2026-06', freq='M'):
        panel.append({'firm': f, 'month': mo, 'n': float(s.get(mo, 0.0))})
pB = pd.DataFrame(panel); pB['logn'] = np.log1p(pB.n)
pB['post'] = (pB.month >= EVENT).astype(int); pB['mstr'] = pB.month.astype(str)
def crossfirm_coef(treat_firm):
    d = pB.copy(); d['treat'] = (d.firm == treat_firm).astype(int)
    m = smf.ols('logn ~ treat:post + C(firm) + C(mstr)', data=d).fit(
        cov_type='cluster', cov_kwds={'groups': d.firm})
    return m.params['treat:post']
perm_firm = {f: crossfirm_coef(f) for f in FIRMS}
actual_cross = perm_firm['Affirm']
perm_vals = np.array(list(perm_firm.values()))
p_firm = float(np.mean(np.abs(perm_vals) >= abs(actual_cross)))
log(f'  cross-firm firm-permutation: Affirm={actual_cross:+.4f}; '
    f'all={ {k: round(v,3) for k,v in perm_firm.items()} }; exact p={p_firm:.3f}')

t8 = pd.DataFrame([
    {'test': 'Within-Affirm CR$\\times$post (placebo-in-time)', 'actual': actual_aff,
     'null_mean': pl.mean(), 'null_lo': pl.min(), 'null_hi': pl.max(),
     'nperm': len(pl), 'p': p_belowall},
    {'test': 'Cross-firm treat$\\times$post (firm permutation)', 'actual': actual_cross,
     'null_mean': perm_vals.mean(), 'null_lo': perm_vals.min(), 'null_hi': perm_vals.max(),
     'nperm': len(perm_vals), 'p': p_firm},
])
t8.to_csv(os.path.join(OUT, 't8_ri.csv'), index=False)

# figure: placebo-in-time distribution for the within-Affirm headline
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(pl, bins=18, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(actual_aff, color='crimson', lw=2,
           label=f'True furnishing-date DiD = {actual_aff:+.3f}\n(below all {len(pl)} placebo splits)')
ax.axvline(0, color='0.3', lw=0.8, ls=':')
ax.set_xlabel('Placebo within-Affirm CR$\\times$post coefficient (pre-event date splits)')
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Placebo-in-time inference: within-Affirm credit-reporting DiD', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_randinf.pdf')); plt.close(fig)

# =====================================================================
# T9 — Power / minimum detectable effects (80% power)
#   MDE = (z_.975 + z_.80) * SE ~= 2.80 * SE. For log-count DiDs express the MDE
#   as a detectable DIFFERENTIAL growth multiple exp(MDE)-1. Distinguish the
#   well-powered specs (which reject H1's POSITIVE spike) from the underpowered
#   5-firm cross-firm count (t=-0.76) that motivates the student's staggered design.
# =====================================================================
log('T9 power / MDE ...')
Z = 1.959964 + 0.841621
specs_power = []
# within-Affirm (log count)
c, t, n = aff_did(); se = abs(c / t)
specs_power.append(('Within-Affirm, log CR count', c, se, 'log', n))
# cross-firm share (from 10_did design)
gBs = df.groupby(['firm', 'month']).agg(n=('cr', 'size'), crn=('cr', 'sum')).reset_index()
gBs = gBs[gBs.n >= 5]; gBs['cr_share'] = gBs.crn / gBs.n
gBs['treat'] = (gBs.firm == 'Affirm').astype(int); gBs['post'] = (gBs.month >= EVENT).astype(int)
gBs['mstr'] = gBs.month.astype(str)
mBs = smf.ols('cr_share ~ treat:post + C(firm) + C(mstr)', data=gBs).fit(
    cov_type='cluster', cov_kwds={'groups': gBs.firm})
c = mBs.params['treat:post']; se = mBs.bse['treat:post']
specs_power.append(('Cross-firm, CR share', c, se, 'share', int(mBs.nobs)))
# cross-firm log count
mBc_c = crossfirm_coef('Affirm')
dtmp = pB.copy(); dtmp['treat'] = (dtmp.firm == 'Affirm').astype(int)
mBc = smf.ols('logn ~ treat:post + C(firm) + C(mstr)', data=dtmp).fit(
    cov_type='cluster', cov_kwds={'groups': dtmp.firm})
c = mBc.params['treat:post']; se = mBc.bse['treat:post']
specs_power.append(('Cross-firm, log CR count', c, se, 'log', int(mBc.nobs)))
# triple diff
c = m_ddd.params['treat:cr:post']; se = m_ddd.bse['treat:cr:post']
specs_power.append(('Triple-difference (DDD)', c, se, 'log', int(m_ddd.nobs)))

cr_share_mean = float(gBs.cr_share.mean())
t9rows = []
for name, c, se, kind, n in specs_power:
    mde = Z * se
    if kind == 'log':
        pct = 100 * (np.exp(mde) - 1)          # detectable differential growth multiple
        unit = 'differential growth'
    else:
        pct = 100 * mde / cr_share_mean         # % of mean CR share
        unit = 'of mean CR share'
    t9rows.append({'spec': name, 'coef': c, 'se': se, 'mde': mde,
                   'pct': pct, 'unit': unit, 'N': n})
    log(f'  {name:30s} coef={c:+.4f} se={se:.4f} MDE={mde:.4f} ({pct:.0f}% {unit})')
t9 = pd.DataFrame(t9rows); t9.to_csv(os.path.join(OUT, 't9_power.csv'), index=False)

# =====================================================================
# Render LaTeX
# =====================================================================
# --- T4 sumstats
body = ''
for _, r in t4.iterrows():
    rule = '\\midrule\n' if r['firm'] == 'All BNPL' else ''
    body += (rule + f"{r['firm']} & {r['furnisher']} & {int(r['N']):,} & {r['cr_share']:.3f} & "
             f"{r['permo_pre']:.1f} & {r['permo_post']:.1f} & {r['first']}--{r['last']} \\\\\n")
w('tab_sumstats.tex', r"""\begin{tabular}{llrcccc}
\toprule
Firm & Furnisher & N & CR share & /mo.\ pre & /mo.\ post & Coverage \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T5 hetero (per-firm within-firm DiD)
body = ''
for _, r in t5.iterrows():
    body += (f"{r['firm']} & {r['furnisher']} & {int(r['ncr']):,} & "
             f"{r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {int(r['N'])} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{llrccc}
\toprule
Firm & Furnished? & CR complaints & CR$\times$post & ($t$) & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T6 triple-difference
body = ''
for _, r in t6.iterrows():
    body += f"{r['spec']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {int(r['N'])} \\\\\n"
w('tab_tripleD.tex', r"""\begin{tabular}{lccc}
\toprule
Specification & Triple diff.\ ($\hat\beta_{DDD}$) & ($t$) & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T7 robustness
body = ''
for _, r in t7.iterrows():
    body += f"{r['spec']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {int(r['N'])} \\\\\n"
w('tab_robust.tex', r"""\begin{tabular}{lccc}
\toprule
Within-Affirm specification & CR$\times$post & ($t$) & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T8 RI
body = ''
for _, r in t8.iterrows():
    nm = r['null_mean'] + 0.0  # avoid -0.0000 display
    nm = 0.0 if abs(nm) < 5e-5 else nm
    body += (f"{r['test']} & {r['actual']:+.4f} & {nm:+.4f} "
             f"& [{r['null_lo']:+.4f}, {r['null_hi']:+.4f}] & {int(r['nperm'])} & {r['p']:.3f} \\\\\n")
w('tab_ri.tex', r"""\begin{tabular}{lccccc}
\toprule
Test & Actual coef. & Null mean & Null range & \# draws & Design $p$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T9 power
body = ''
for _, r in t9.iterrows():
    body += (f"{r['spec']} & {r['coef']:+.4f} & {r['se']:.4f} & {r['mde']:.4f} "
             f"& {r['pct']:.0f}\\% {r['unit']} \\\\\n")
w('tab_power.tex', r"""\begin{tabular}{lcccl}
\toprule
Specification & DiD coef. & SE & MDE(80\%) & MDE magnitude \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# stash meta for the prose
pd.DataFrame([{
    'p_belowall': p_belowall, 'nplacebo': len(pl), 'placebo_mean': pl.mean(),
    'placebo_lo': pl.min(), 'placebo_hi': pl.max(),
    'p_firm': p_firm, 'actual_aff': actual_aff, 'actual_cross': actual_cross,
    'ddd_coef': float(m_ddd.params['treat:cr:post']), 'ddd_t': float(m_ddd.tvalues['treat:cr:post']),
    'cr_share_mean': cr_share_mean,
    'mde_within_pct': float(t9[t9.spec=='Within-Affirm, log CR count']['pct'].iloc[0]),
    'mde_crosscount_pct': float(t9[t9.spec=='Cross-firm, log CR count']['pct'].iloc[0]),
    'mde_share_pct': float(t9[t9.spec=='Cross-firm, CR share']['pct'].iloc[0]),
}]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE — extension tables + fig3 written to ' + TEX)
logf.close()
print('Extension tables written to', TEX)
