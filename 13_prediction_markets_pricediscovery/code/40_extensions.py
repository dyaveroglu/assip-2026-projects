#!/usr/bin/env python3
"""
Project 13 (Kalshi vs Polymarket) -- Step 40: journal-track extensions.

Adds four NEW real tables that deepen the price-discovery result WITHOUT touching
the analyst's reserved contribution (rule-by-rule settlement verification, a second
hand-matched event family, and the order-book liquidity memo -- STUDENT_TASKS.md).
All identification here uses OBSERVABLE data only: the aligned hourly price panel and
per-pair characteristics already produced by 10_build.py / 20_analyze.py.

  t9_inference.csv   Design-based inference on the venue-leadership statistic:
                     nonparametric bootstrap CI on the pooled Hasbrouck share, a
                     sign test on who-leads, and a cross-pairing placebo (Kalshi
                     leg vs a MISMATCHED Polymarket outcome from the same meeting).
                     Also writes fig5_bootstrap.pdf.
  t10_hetero.csv     Heterogeneity of Polymarket's information share along four
                     OBSERVABLE pair gradients (liquidity/overlap, price variation,
                     contestedness, meeting horizon). Coarse: it cannot separate a
                     genuine informational lag from a thin tape -- the order-book
                     decomposition is deliberately left to the student.
  t11_altspec.csv    Robustness of the pooled leadership statistic to estimator and
                     window choices (fixed lags, second-half window, liquid-only,
                     the ordering-free Gonzalo-Granger measure, and a model-free
                     return lead-lag regression).
  t12_power.csv      Power / minimum-detectable-leadership: the SE and MDE(80%) of
                     the pooled information share, and the binomial power of the
                     sign test, so the strength (and limits) of the finding are
                     stated as quantities, not adjectives.

Every number is written to output/tables/*.csv and rendered to paper/tables/*.tex,
so the paper cannot drift from the code. Reuses the estimator in 20_analyze.py.
"""
import os, sys, glob, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'code'))
# reuse the exact estimator used for the main tables
from importlib import import_module
an = import_module('20_analyze')

RAW  = os.path.join(HERE, 'data', 'raw')
PROC = os.path.join(HERE, 'data', 'processed')
OUT  = os.path.join(HERE, 'output', 'tables')
TEX  = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
for d in (OUT, TEX, FIG): os.makedirs(d, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'40_extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

np.random.seed(20260724)   # deterministic bootstrap / placebo permutations
STEP = 3600
MIN_OBS = 150
MIN_SD  = 0.02

def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

# ---------------------------------------------------------------------------
# Load the per-pair analysis outputs (all observable, already computed)
# ---------------------------------------------------------------------------
hb  = pd.read_csv(os.path.join(OUT, 't5_hasbrouck.csv'))
sm  = pd.read_csv(os.path.join(OUT, 't2_sumstats.csv'))
ll  = pd.read_csv(os.path.join(OUT, 't3_leadlag.csv'))
sel = pd.read_csv(os.path.join(PROC, 'pairs_selected.csv'))
panel = pd.read_csv(os.path.join(PROC, 'matched_panel.csv'))

pp = hb.merge(sm[['pair', 'corr_level', 'mean_abs_gap', 'kalshi_ret_sd',
                  'poly_ret_sd', 'kalshi_mean', 'poly_mean']], on='pair')
pp = pp.merge(sel[['pair', 'kalshi_sd', 'poly_sd', 'overlap_days']], on='pair')
pp = pp.merge(ll[['pair', 'peak_lag']], on='pair')
pp['IS_poly'] = pp['IS_poly_mid'].astype(float)
pp['maxsd']   = pp[['kalshi_sd', 'poly_sd']].max(axis=1)
pp['contested'] = np.minimum((pp['kalshi_mean'] + pp['poly_mean']) / 2,
                             1 - (pp['kalshi_mean'] + pp['poly_mean']) / 2)
pp['far'] = (pp['meeting'] == '26OCT').astype(int)     # far-dated at the data cut
N = len(pp)
real_mean   = float(pp['IS_poly'].mean())
real_wmean  = float(np.average(pp['IS_poly'], weights=pp['n']))
real_median = float(pp['IS_poly'].median())
n_poly_lead = int((pp['IS_poly'] > 0.5).sum())
log(f'loaded {N} matched pairs. mean IS_poly={real_mean:.3f} wmean={real_wmean:.3f} '
    f'median={real_median:.3f} poly leads {n_poly_lead}/{N}')

# ===========================================================================
# T9 -- Design-based inference on the leadership statistic
#   (a) nonparametric bootstrap CI on the pooled Hasbrouck share
#   (b) sign test on who-leads (binomial vs 0.5)
#   (c) cross-pairing placebo: Kalshi leg vs a MISMATCHED Poly outcome
# ===========================================================================
log('T9 design-based inference ...')
B = 5000
is_vec = pp['IS_poly'].values; wts = pp['n'].values
boot_eq, boot_w = [], []
for _ in range(B):
    idx = np.random.randint(0, N, N)
    boot_eq.append(is_vec[idx].mean())
    boot_w.append(np.average(is_vec[idx], weights=wts[idx]))
boot_eq = np.array(boot_eq); boot_w = np.array(boot_w)
ci_eq = (np.percentile(boot_eq, 2.5), np.percentile(boot_eq, 97.5))
ci_w  = (np.percentile(boot_w,  2.5), np.percentile(boot_w, 97.5))
# one-sample t vs 0.5 (equal weight)
se_eq = is_vec.std(ddof=1) / np.sqrt(N)
t_eq  = (real_mean - 0.5) / se_eq
p_eq  = 2 * (1 - stats.t.cdf(abs(t_eq), df=N - 1))
# sign test
p_sign = float(stats.binomtest(n_poly_lead, N, 0.5).pvalue)
log(f'  bootstrap eq mean CI=[{ci_eq[0]:.3f},{ci_eq[1]:.3f}]  t(vs .5)={t_eq:.2f} p={p_eq:.3f}')
log(f'  bootstrap wt mean CI=[{ci_w[0]:.3f},{ci_w[1]:.3f}]')
log(f'  sign test: poly leads {n_poly_lead}/{N}, binomial p={p_sign:.3f}')

# ---- cross-pairing placebo -------------------------------------------------
# Load every raw leg, keyed by meeting_outcome. A placebo pair aligns a Kalshi
# leg with a Polymarket leg for a DIFFERENT outcome of the SAME meeting (so the
# trading windows overlap but the two contracts settle on different events).
def loadraw(sub, key):
    f = os.path.join(RAW, sub, key + '.csv')
    if not os.path.exists(f): return None
    d = pd.read_csv(f)[['ts', 'price']].dropna().sort_values('ts')
    d = d[(d.price >= 0) & (d.price <= 1)].drop_duplicates('ts')
    return d if len(d) >= 5 else None

def align(k, p):
    lo = int(max(k.ts.min(), p.ts.min())); hi = int(min(k.ts.max(), p.ts.max()))
    if hi - lo < MIN_OBS * STEP: return None
    grid = np.arange(lo, hi + 1, STEP)
    def asof(d):
        t = d.ts.values; pr = d.price.values
        idx = np.searchsorted(t, grid, side='right') - 1
        return np.where(idx >= 0, pr[np.clip(idx, 0, len(pr) - 1)], np.nan)
    kp = asof(k); pv = asof(p)
    m = ~(np.isnan(kp) | np.isnan(pv))
    kp, pv = kp[m], pv[m]
    if len(kp) < MIN_OBS or max(kp.std(), pv.std()) < MIN_SD: return None
    return kp, pv

def is_poly_of(kp, pv):
    p1 = np.clip(kp, 1e-4, 1 - 1e-4); p2 = np.clip(pv, 1e-4, 1 - 1e-4)
    k = an.pick_k(p1, p2)
    alpha, G, Omega, aic, nn = an.fit_vecm(p1, p2, k)
    lo, hi = an.hasbrouck_is(alpha, Omega)
    if not (np.isfinite(lo) and np.isfinite(hi)): return np.nan
    return 1 - (lo + hi) / 2      # Polymarket share

OUTCOMES = ['no_change', 'cut25', 'cut50p', 'hike25', 'hike50p']
MEETINGS = ['26JUN', '26JUL', '26SEP', '26OCT']
placebo = []
for mt in MEETINGS:
    legsK = {o: loadraw('kalshi', f'{mt}_{o}') for o in OUTCOMES}
    legsP = {o: loadraw('poly',   f'{mt}_{o}') for o in OUTCOMES}
    for oa in OUTCOMES:
        for ob in OUTCOMES:
            if oa == ob: continue
            k, p = legsK.get(oa), legsP.get(ob)
            if k is None or p is None: continue
            al = align(k, p)
            if al is None: continue
            v = is_poly_of(*al)
            if np.isfinite(v):
                placebo.append(dict(meeting=mt, kalshi=oa, poly=ob, IS_poly=v))
placebo = pd.DataFrame(placebo)
plc_mean = float(placebo['IS_poly'].mean())
plc_lead = float((placebo['IS_poly'] > 0.5).mean())
log(f'  placebo mismatched pairs: {len(placebo)}  mean IS_poly={plc_mean:.3f}  '
    f'poly-leads share={plc_lead:.3f}')

t9 = pd.DataFrame([
    dict(stat='Pooled IS_poly (equal-weight)', value=real_mean,
         lo=ci_eq[0], hi=ci_eq[1], pval=p_eq, note='bootstrap 95% CI; t-test vs 0.5'),
    dict(stat='Pooled IS_poly (activity-weight)', value=real_wmean,
         lo=ci_w[0], hi=ci_w[1], pval=np.nan, note='bootstrap 95% CI'),
    dict(stat='Median IS_poly', value=real_median, lo=np.nan, hi=np.nan,
         pval=np.nan, note='across 15 pairs'),
    dict(stat=f'Sign test (Poly leads {n_poly_lead}/{N})', value=n_poly_lead / N,
         lo=np.nan, hi=np.nan, pval=p_sign, note='two-sided binomial vs 0.5'),
    dict(stat=f'Cross-pairing placebo ({len(placebo)} mismatched)', value=plc_mean,
         lo=np.nan, hi=np.nan, pval=np.nan,
         note=f'poly-leads share {plc_lead:.2f}; mismatched same-meeting outcomes'),
])
t9.to_csv(os.path.join(OUT, 't9_inference.csv'), index=False)
placebo.to_csv(os.path.join(OUT, 't9_placebo_pairs.csv'), index=False)

# fig5: bootstrap distribution of the pooled (equal-weight) Hasbrouck share
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(boot_eq, bins=40, color='0.75', edgecolor='0.4', linewidth=0.4)
ax.axvline(0.5, color='0.3', lw=1.0, ls=':', label='No leadership (0.5)')
ax.axvline(real_mean, color='crimson', lw=2,
           label=f'Pooled IS$_P$ = {real_mean:.2f}\n95% CI [{ci_eq[0]:.2f}, {ci_eq[1]:.2f}]')
ax.axvspan(ci_eq[0], ci_eq[1], color='crimson', alpha=0.10)
ax.set_xlabel("Bootstrap pooled Polymarket information share (5,000 resamples of 15 pairs)")
ax.set_ylabel('Frequency'); ax.legend(frameon=False, fontsize=9)
ax.set_title('Design-based inference on venue leadership', fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig5_bootstrap.pdf')); plt.close(fig)

# ===========================================================================
# T10 -- Heterogeneity of Polymarket's information share by OBSERVABLE gradients
#   Median split on each moderator; report mean IS_poly high vs low + gap.
#   Coarse by construction: it cannot separate informational lag from thin tape.
# ===========================================================================
log('T10 heterogeneity by observable gradient ...')
def split(col, label, thr=None, hi_is_top=True):
    d = pp.dropna(subset=[col]).copy()
    if thr is None: thr = d[col].median()
    hi = d[d[col] >  thr]; lo = d[d[col] <= thr]
    if not hi_is_top: hi, lo = lo, hi
    return dict(moderator=label,
                n_hi=len(hi), is_hi=float(hi['IS_poly'].mean()),
                n_lo=len(lo), is_lo=float(lo['IS_poly'].mean()),
                gap=float(hi['IS_poly'].mean() - lo['IS_poly'].mean()))
MODS = [
    ('n',         'Liquidity (overlapping hours)'),
    ('maxsd',     'Price variation (max venue SD)'),
    ('contested', 'Contestedness ($\\min(\\bar p,1-\\bar p)$)'),
]
t10 = [split(c, l) for c, l in MODS]
# horizon: far-dated (October) vs near-dated
far = pp[pp['far'] == 1]; near = pp[pp['far'] == 0]
t10.append(dict(moderator='Near-dated meeting (Jun/Jul/Sep vs Oct)',
                n_hi=len(near), is_hi=float(near['IS_poly'].mean()),
                n_lo=len(far),  is_lo=float(far['IS_poly'].mean()),
                gap=float(near['IS_poly'].mean() - far['IS_poly'].mean())))
t10 = pd.DataFrame(t10)
t10.to_csv(os.path.join(OUT, 't10_hetero.csv'), index=False)
for _, r in t10.iterrows():
    log(f"  {r['moderator'][:40]:40s} hi(n={r['n_hi']}):{r['is_hi']:.3f}  "
        f"lo(n={r['n_lo']}):{r['is_lo']:.3f}  gap={r['gap']:+.3f}")

# ===========================================================================
# T11 -- Robustness of the pooled leadership statistic to estimator/window
# ===========================================================================
log('T11 alternative estimators & windows ...')
rows = []
def pooled_from_panel(kfilter=None, wpart='full', fixed_k=None):
    """Recompute pooled IS_poly over the 15 selected pairs under a variant."""
    vals, ns = [], []
    for pair in pp['pair']:
        g = panel[panel.pair == pair].sort_values('ts')
        p1 = g.kalshi_p.clip(1e-4, 1 - 1e-4).values
        p2 = g.poly_p.clip(1e-4, 1 - 1e-4).values
        if wpart == 'second':                       # mature-market second half
            h = len(p1) // 2; p1, p2 = p1[h:], p2[h:]
        if len(p1) < 60: continue
        k = fixed_k if fixed_k else an.pick_k(p1, p2)
        try:
            alpha, G, Om, aic, nn = an.fit_vecm(p1, p2, k)
            lo, hi = an.hasbrouck_is(alpha, Om)
            if np.isfinite(lo) and np.isfinite(hi):
                vals.append(1 - (lo + hi) / 2); ns.append(nn)
        except Exception:
            pass
    vals = np.array(vals); ns = np.array(ns)
    return vals.mean(), np.average(vals, weights=ns), int((vals > 0.5).sum()), len(vals)

# baseline (AIC lag)
m, wm, nl, nn = real_mean, real_wmean, n_poly_lead, N
rows.append(dict(variant='Baseline (Hasbrouck, AIC lag)', mean=m, wmean=wm, leads=f'{nl}/{nn}'))
for k in (2, 4):
    m, wm, nl, nn = pooled_from_panel(fixed_k=k)
    rows.append(dict(variant=f'Fixed lag $k={k}$', mean=m, wmean=wm, leads=f'{nl}/{nn}'))
m, wm, nl, nn = pooled_from_panel(wpart='second')
rows.append(dict(variant='Second-half window (mature market)', mean=m, wmean=wm, leads=f'{nl}/{nn}'))
# liquid-only (>=1000 overlapping hours)
liq = pp[pp['n'] >= 1000]
rows.append(dict(variant='Liquid pairs only ($N\\ge1000$)',
                 mean=float(liq['IS_poly'].mean()),
                 wmean=float(np.average(liq['IS_poly'], weights=liq['n'])),
                 leads=f"{int((liq['IS_poly']>0.5).sum())}/{len(liq)}"))
# Gonzalo-Granger (ordering-free), winsorize the meaningless out-of-[0,1] value
gg = pp['GG_kalshi'].clip(0, 1)
gg_poly = 1 - gg
rows.append(dict(variant='Gonzalo--Granger weight (ordering-free)',
                 mean=float(gg_poly.mean()),
                 wmean=float(np.average(gg_poly, weights=pp['n'])),
                 leads=f"{int((gg_poly>0.5).sum())}/{len(gg_poly)}"))
# model-free return lead-lag regression: dPoly_t on dKalshi_{t-1}, dKalshi_t on
# dPoly_{t-1}; "poly leads" if its lagged coef predicts Kalshi more than the reverse.
plead = 0; ntot = 0; betas = []
for pair in pp['pair']:
    g = panel[panel.pair == pair].sort_values('ts')
    d1 = np.diff(g.kalshi_p.values); d2 = np.diff(g.poly_p.values)
    if len(d1) < 60 or d1.std() == 0 or d2.std() == 0: continue
    # regress Kalshi change on lagged Poly change  (Poly -> Kalshi predictability)
    bpk = np.corrcoef(d1[1:], d2[:-1])[0, 1]
    # regress Poly change on lagged Kalshi change  (Kalshi -> Poly predictability)
    bkp = np.corrcoef(d2[1:], d1[:-1])[0, 1]
    ntot += 1; betas.append(abs(bpk) - abs(bkp))
    if abs(bpk) > abs(bkp): plead += 1
rows.append(dict(variant='Return lead--lag (model-free)', mean=np.nan, wmean=np.nan,
                 leads=f'{plead}/{ntot}'))
t11 = pd.DataFrame(rows); t11.to_csv(os.path.join(OUT, 't11_altspec.csv'), index=False)
for _, r in t11.iterrows():
    log(f"  {r['variant'][:38]:38s} mean={r['mean'] if pd.isna(r['mean']) else round(r['mean'],3)}"
        f"  wmean={r['wmean'] if pd.isna(r['wmean']) else round(r['wmean'],3)}  leads={r['leads']}")

# ===========================================================================
# T12 -- Power / minimum-detectable leadership
#   (a) MDE(80%) on the pooled information share = 2.80 * SE(mean IS_poly)
#   (b) binomial power of the sign test to detect a given leadership fraction
# ===========================================================================
log('T12 power / minimum-detectable leadership ...')
Z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)     # ~= 2.802
rows = []
# equal-weight
sd_is = is_vec.std(ddof=1)
se = sd_is / np.sqrt(N)
mde = Z * se
rows.append(dict(measure='Pooled IS_poly (equal-weight)', mean=real_mean,
                 lead=real_mean - 0.5, sd=sd_is, se=se, mde=mde,
                 detected=(real_mean - 0.5) > mde))
# liquid subsample (where the design is well identified)
se_l = liq['IS_poly'].std(ddof=1) / np.sqrt(len(liq))
mde_l = Z * se_l
rows.append(dict(measure=f'Pooled IS_poly, liquid pairs ($N\\ge1000$, n={len(liq)})',
                 mean=float(liq['IS_poly'].mean()),
                 lead=float(liq['IS_poly'].mean()) - 0.5,
                 sd=float(liq['IS_poly'].std(ddof=1)), se=se_l, mde=mde_l,
                 detected=(float(liq['IS_poly'].mean()) - 0.5) > mde_l))
t12 = pd.DataFrame(rows); t12.to_csv(os.path.join(OUT, 't12_power.csv'), index=False)
# binomial power of the sign test (n pairs) to detect true leadership fraction q
def binom_power(n, q, alpha=0.05):
    # two-sided sign test; reject if #leads >= crit_hi or <= crit_lo under H0=0.5
    from scipy.stats import binom
    crit_hi = binom.ppf(1 - alpha / 2, n, 0.5)
    return float(1 - binom.cdf(crit_hi, n, q) + binom.cdf(n - crit_hi - 1, n, q))
pow_rows = [dict(n=N, q=q, power=binom_power(N, q)) for q in (0.6, 0.7, 0.8, 0.9)]
powdf = pd.DataFrame(pow_rows); powdf.to_csv(os.path.join(OUT, 't12_signpower.csv'), index=False)
for _, r in t12.iterrows():
    log(f"  {r['measure'][:44]:44s} lead={r['lead']:+.3f} MDE(80%)={r['mde']:.3f} "
        f"detected={r['detected']}")
for _, r in powdf.iterrows():
    log(f"  sign-test power @ q={r['q']:.1f}: {r['power']:.3f}")

# ===========================================================================
# Render LaTeX for the four new tables
# ===========================================================================
def f3(x): return '' if pd.isna(x) else f'{x:.3f}'
def f2(x): return '' if pd.isna(x) else f'{x:.2f}'

# --- T9 inference
body = ''
for _, r in t9.iterrows():
    ci = '' if pd.isna(r['lo']) else f"[{r['lo']:.3f},\\,{r['hi']:.3f}]"
    pv = '' if pd.isna(r['pval']) else f"{r['pval']:.3f}"
    lab = r['stat'].replace('IS_poly', 'IS$_{P}$')
    body += f"{lab} & {r['value']:.3f} & {ci} & {pv} \\\\\n"
w('tab_inference.tex', r"""\begin{tabular}{lccc}
\toprule
Statistic & Value & 95\% CI & $p$-value \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T10 hetero
body = ''
for _, r in t10.iterrows():
    body += (f"{r['moderator']} & {int(r['n_hi'])} & {r['is_hi']:.3f} & {int(r['n_lo'])} "
             f"& {r['is_lo']:.3f} & {r['gap']:+.3f} \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lccccc}
\toprule
& \multicolumn{2}{c}{High / near} & \multicolumn{2}{c}{Low / far} & \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Observable moderator (median split) & $n$ & IS$_P$ & $n$ & IS$_P$ & Gap \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T11 altspec
body = ''
for _, r in t11.iterrows():
    body += (f"{r['variant']} & {f3(r['mean'])} & {f3(r['wmean'])} & {r['leads']} \\\\\n")
w('tab_altspec.tex', r"""\begin{tabular}{lccc}
\toprule
Specification & IS$_P$ (equal) & IS$_P$ (activity) & Poly leads \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# --- T12 power
body = ''
for _, r in t12.iterrows():
    lab = r['measure'].replace('IS_poly', 'IS$_{P}$')
    body += (f"{lab} & {r['mean']:.3f} & {r['lead']:+.3f} & {r['se']:.3f} "
             f"& {r['mde']:.3f} & {'yes' if r['detected'] else 'no'} \\\\\n")
sp = ' / '.join(f"{r['power']:.2f}" for _, r in powdf.iterrows())
w('tab_power.tex', r"""\begin{tabular}{lccccc}
\toprule
Leadership measure & IS$_P$ & Lead ($-0.5$) & SE & MDE(80\%) & Detected? \\
\midrule
""" + body + r"""\midrule
\multicolumn{6}{l}{\footnotesize Sign-test power ($n=15$) to detect true Poly-leads share
$q=0.6/0.7/0.8/0.9$: """ + sp + r""".} \\
\bottomrule
\end{tabular}""")

# stash meta for the paper prose
pd.DataFrame([dict(
    mean_IS_poly=real_mean, wmean_IS_poly=real_wmean, median_IS_poly=real_median,
    ci_eq_lo=ci_eq[0], ci_eq_hi=ci_eq[1], ci_w_lo=ci_w[0], ci_w_hi=ci_w[1],
    t_vs_half=t_eq, p_vs_half=p_eq, n_poly_lead=n_poly_lead, N=N, p_sign=p_sign,
    placebo_n=len(placebo), placebo_mean=plc_mean, placebo_lead=plc_lead,
    se_eq=se, mde_eq=mde, lead_eq=real_mean - 0.5,
    liq_mean=float(liq['IS_poly'].mean()), liq_n=len(liq),
    liq_lead=float(liq['IS_poly'].mean()) - 0.5, liq_mde=mde_l,
    sign_power_q80=binom_power(N, 0.8), sign_power_q90=binom_power(N, 0.9),
)]).to_csv(os.path.join(OUT, 't0_meta_ext.csv'), index=False)

log('DONE -- extension tables + fig5 written.')
logf.close()
print('Extension tables written to', TEX)
