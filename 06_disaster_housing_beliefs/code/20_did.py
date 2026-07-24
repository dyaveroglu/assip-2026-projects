#!/usr/bin/env python3
"""
Project 06 — Step 20: exposure DiD and belief moderation.

Two-way fixed-effects stacked DiD on ln(ZHVI):
   ln_zhvi_{i,t} = a_i (county x event) + d_t (event x calendar-month)
                   + b * (treat_i * post_t) + e
where treat = FEMA IHP-designated (hard-hit) county, post = months after landfall.
SE clustered by county. Belief moderation adds treat*post*Moderator (and post*Moderator).

Writes output/tables/{t1_balance,t2_did,t3_belief,t4_eventstudy,t5_eventstudy_beliefsplit}.csv
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels.panel import PanelOLS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
os.makedirs(OUT, exist_ok=True); LOG = os.path.join(HERE, 'logs')
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'did_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

p = pd.read_csv(os.path.join(PROC, 'panel.csv'),
                dtype={'fips': str, 'ce_id': str, 'em_id': str})
p['worried_z'] = p.worried_z.astype(float)
log(f'panel loaded: {len(p):,} rows, {p.ce_id.nunique()} county-events, {p.fips.nunique()} counties')

def panel_twfe(df, xcols, entity_eff=True, month_fe=True, cluster='fips'):
    """PanelOLS: county-event entity FE (+ event x calendar-month FE via other_effects),
    SE clustered by county. Panel time index = rel_month (numeric, unique within entity)."""
    d = df.copy()
    d['emcode'] = pd.factorize(d['em_id'])[0]
    d = d.set_index(['ce_id', 'rel_month'])
    y = d['ln_zhvi']; X = d[xcols]
    other = d[['emcode']] if month_fe else None
    m = PanelOLS(y, X, entity_effects=entity_eff, other_effects=other, drop_absorbed=True)
    return m.fit(cov_type='clustered', clusters=d[cluster])

def grab(res, key):
    return dict(coef=res.params[key], t=res.tstats[key], se=res.std_errors[key],
                p=res.pvalues[key], N=int(res.nobs))

# ============================================================ T1: balance / summary
ccov = p.drop_duplicates('ce_id').copy()
# pre-landfall trend: avg monthly ln change over the pre window, per county-event
pre = p[p.rel_month < 0].sort_values(['ce_id', 'rel_month'])
tr = (pre.groupby('ce_id')['ln_zhvi'].agg(lambda s: (s.iloc[-1]-s.iloc[0])/(len(s)-1)))
ccov = ccov.merge(tr.rename('pre_trend'), on='ce_id', how='left')
rows = []
for name, col in [('Worried about warming (%)', 'worried'),
                  ('Believe warming happening (%)', 'happening'),
                  ('2020 GOP vote share', 'per_gop'),
                  ('NRI hurricane risk score', 'HRCN_RISKS'),
                  ('NRI overall risk score', 'RISK_SCORE'),
                  ('ln ZHVI at landfall', 'ln_zhvi'),
                  ('Pre-period monthly ln-ZHVI trend', 'pre_trend')]:
    if col == 'ln_zhvi':
        base = p[p.rel_month == 0].groupby('ce_id')['ln_zhvi'].first()
        cc = ccov.merge(base.rename('lnz0'), on='ce_id'); c = 'lnz0'
    else:
        cc = ccov; c = col
    t = cc[cc.treat == 1][c].astype(float); k = cc[cc.treat == 0][c].astype(float)
    from scipy import stats
    diff = t.mean() - k.mean()
    tstat = stats.ttest_ind(t.dropna(), k.dropna(), equal_var=False).statistic
    rows.append(dict(var=name, treated=t.mean(), control=k.mean(), diff=diff, t=tstat))
t1 = pd.DataFrame(rows)
t1.loc[len(t1)] = dict(var='N (county-events)', treated=(ccov.treat==1).sum(),
                       control=(ccov.treat==0).sum(), diff=np.nan, t=np.nan)
t1.to_csv(os.path.join(OUT, 't1_balance.csv'), index=False)
log('T1 balance:\n' + t1.round(3).to_string(index=False))

# ============================================================ T2: baseline DiD
res_rows = []
# (1) naive pooled OLS (no FE) with clustered SE via PanelOLS entity/time off + explicit terms
import statsmodels.formula.api as smf
m1 = smf.ols('ln_zhvi ~ treat + post + treatpost', data=p).fit(
        cov_type='cluster', cov_kwds={'groups': p.fips})
res_rows.append(dict(spec='(1) Pooled OLS, no FE', **{
    'coef': m1.params['treatpost'], 't': m1.tvalues['treatpost'],
    'se': m1.bse['treatpost'], 'N': int(m1.nobs), 'fe': 'none'}))
# (2) county-event FE only
r2 = panel_twfe(p, ["treatpost"], month_fe=False)
g = grab(r2, 'treatpost'); res_rows.append(dict(spec='(2) + county$\\times$event FE',
    coef=g['coef'], t=g['t'], se=g['se'], N=g['N'], fe='cty'))
# (3) two-way FE  (preferred)
r3 = panel_twfe(p, ['treatpost'])
g = grab(r3, 'treatpost'); res_rows.append(dict(spec='(3) + event$\\times$month FE (preferred)',
    coef=g['coef'], t=g['t'], se=g['se'], N=g['N'], fe='twoway'))
# (4) preferred, controls restricted to FEMA-designated (any program) counties
pd_ = p[(p.treat == 1) | (p.designated == 1)]
r4 = panel_twfe(pd_, ['treatpost'])
g = grab(r4, 'treatpost'); res_rows.append(dict(spec='(4) Controls = designated only',
    coef=g['coef'], t=g['t'], se=g['se'], N=g['N'], fe='twoway'))
# (5) Helene only, (6) Ian only
for ev in ['Helene', 'Ian']:
    rr = panel_twfe(p[p.event == ev], ['treatpost'])
    g = grab(rr, 'treatpost'); res_rows.append(dict(spec=f'({"5" if ev=="Helene" else "6"}) {ev} only',
        coef=g['coef'], t=g['t'], se=g['se'], N=g['N'], fe='twoway'))
# (7) preferred + treated-specific linear trend (detrended DiD)
p['treat_rel'] = p.treat * p.rel_month
r7 = panel_twfe(p, ['treatpost', 'treat_rel'])
g = grab(r7, 'treatpost'); res_rows.append(dict(spec='(7) + treated linear trend (detrended)',
    coef=g['coef'], t=g['t'], se=g['se'], N=g['N'], fe='twoway'))
t2 = pd.DataFrame(res_rows); t2.to_csv(os.path.join(OUT, 't2_did.csv'), index=False)
log('T2 baseline DiD (DV=ln ZHVI):\n' + t2.round(4).to_string(index=False))

# ============================================================ T3: belief moderation (headline)
p['tp_high']   = p.treatpost * p.high_belief
p['po_high']   = p.post * p.high_belief
p['tp_wor']    = p.treatpost * p.worried_z
p['po_wor']    = p.post * p.worried_z
p['tp_gop']    = p.treatpost * p.gop_z
p['po_gop']    = p.post * p.gop_z
p['tp_hrcn']   = p.treatpost * p.hrcn_z
p['po_hrcn']   = p.post * p.hrcn_z

specs3 = [
    ('(1) High-belief split', ['treatpost', 'tp_high', 'po_high'], 'tp_high'),
    ('(2) Worried (continuous, z)', ['treatpost', 'tp_wor', 'po_wor'], 'tp_wor'),
    ('(3) GOP vote share (inverse belief, z)', ['treatpost', 'tp_gop', 'po_gop'], 'tp_gop'),
    ('(4) NRI hurricane risk (z)', ['treatpost', 'tp_hrcn', 'po_hrcn'], 'tp_hrcn'),
]
r3rows = []
for name, xs, key in specs3:
    rr = panel_twfe(p.dropna(subset=xs), xs)
    r3rows.append(dict(spec=name, base=rr.params['treatpost'], base_t=rr.tstats['treatpost'],
                       inter=rr.params[key], inter_t=rr.tstats[key],
                       inter_se=rr.std_errors[key], N=int(rr.nobs)))
# (5) worried continuous, Helene only
rr = panel_twfe(p[p.event == 'Helene'].dropna(subset=['tp_wor', 'po_wor']),
                ['treatpost', 'tp_wor', 'po_wor'])
r3rows.append(dict(spec='(5) Worried (z), Helene only', base=rr.params['treatpost'],
                   base_t=rr.tstats['treatpost'], inter=rr.params['tp_wor'],
                   inter_t=rr.tstats['tp_wor'], inter_se=rr.std_errors['tp_wor'], N=int(rr.nobs)))
# (6) high-belief split, DETRENDED: add treated-specific AND high-belief-specific linear trends
p['treat_rel']   = p.treat * p.rel_month
p['high_rel']    = p.high_belief * p.rel_month
p['tphigh_rel']  = p.treat * p.high_belief * p.rel_month
rr = panel_twfe(p, ['treatpost', 'tp_high', 'po_high', 'treat_rel', 'high_rel', 'tphigh_rel'])
r3rows.append(dict(spec='(6) High-belief split, detrended', base=rr.params['treatpost'],
                   base_t=rr.tstats['treatpost'], inter=rr.params['tp_high'],
                   inter_t=rr.tstats['tp_high'], inter_se=rr.std_errors['tp_high'], N=int(rr.nobs)))
t3 = pd.DataFrame(r3rows); t3.to_csv(os.path.join(OUT, 't3_belief.csv'), index=False)
log('T3 belief moderation (interaction = treat*post*Moderator):\n' + t3.round(4).to_string(index=False))

# ---- pre-trend diagnostic: differential treated-vs-control linear slope, PRE window only
pre_only = p[p.rel_month < 0].copy()
prerows = []
for grp, sub in [('Full sample', pre_only), ('High belief', pre_only[pre_only.high_belief == 1]),
                 ('Low belief', pre_only[pre_only.high_belief == 0])]:
    s = sub.copy(); s['treat_rel'] = s.treat * s.rel_month
    rr = panel_twfe(s, ['treat_rel'])
    prerows.append(dict(group=grp, pretrend_slope=rr.params['treat_rel'],
                        t=rr.tstats['treat_rel'], se=rr.std_errors['treat_rel'], N=int(rr.nobs)))
t6 = pd.DataFrame(prerows); t6.to_csv(os.path.join(OUT, 't6_pretrend.csv'), index=False)
log('T6 pre-trend slopes (treated-vs-control, per month, pre-landfall):\n'
    + t6.round(5).to_string(index=False))

# ============================================================ T4: dynamic event study (pooled)
es = p.copy()
KS = [k for k in range(-24, 21) if k != 0]      # omit landfall month (rel=0) as baseline
xcols = []
for k in KS:
    c = f'd{k:+d}'.replace('+', 'p').replace('-', 'm')
    es[c] = ((es.rel_month == k) & (es.treat == 1)).astype(int)
    xcols.append((k, c))
rr = panel_twfe(es, [c for _, c in xcols])
erows = [dict(rel_month=k, coef=rr.params[c], se=rr.std_errors[c], t=rr.tstats[c]) for k, c in xcols]
erows.append(dict(rel_month=0, coef=0.0, se=0.0, t=np.nan))
t4 = pd.DataFrame(erows).sort_values('rel_month')
t4.to_csv(os.path.join(OUT, 't4_eventstudy.csv'), index=False)
log(f'T4 event study: pre-avg |coef|={t4[t4.rel_month<0].coef.abs().mean():.4f}, '
    f'post +20 coef={t4[t4.rel_month==20].coef.values[0]:+.4f}')

# ============================================================ T5: belief-split event study (for fig)
splitrows = []
for grp, sub in [('High belief', p[p.high_belief == 1]), ('Low belief', p[p.high_belief == 0])]:
    e = sub.copy(); cs = []
    for k in KS:
        c = f'd{k:+d}'.replace('+', 'p').replace('-', 'm')
        e[c] = ((e.rel_month == k) & (e.treat == 1)).astype(int); cs.append((k, c))
    rr = panel_twfe(e, [c for _, c in cs])
    for k, c in cs:
        splitrows.append(dict(group=grp, rel_month=k, coef=rr.params[c], se=rr.std_errors[c]))
    splitrows.append(dict(group=grp, rel_month=0, coef=0.0, se=0.0))
t5 = pd.DataFrame(splitrows).sort_values(['group', 'rel_month'])
t5.to_csv(os.path.join(OUT, 't5_eventstudy_beliefsplit.csv'), index=False)
log('T5 belief-split event study written')
log('DONE 20_did')
logf.close()
