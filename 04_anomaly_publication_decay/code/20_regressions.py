#!/usr/bin/env python3
"""
Project 04 -- Step 20: publication-decay regressions + tables.

DV = monthly long-short (LS) portfolio return of an anomaly (in percent).

H1  Anomaly LS returns fall after publication. We estimate, on the pooled
    anomaly-month panel,
        ret_{i,t} = a + b1*PostSample_{i,t} + b2*PostPub_{i,t} + FE + e
    (b1, b2 are declines vs the in-sample regime), and the NESTED
    McLean-Pontiff decomposition
        ret_{i,t} = a + g1*OOS_{i,t} + g2*Pub_{i,t} + FE + e
    where OOS=1 after the sample ends and Pub=1 after publication, so g2 is
    the *extra* decline attributable to publication itself.

H2  Decay is larger for mispricing- than risk-framed anomalies:
        ret ~ PostSample + PostPub + PostPub:Risk + PostSample:Risk + Risk
    A positive PostPub:Risk would mean risk anomalies decay LESS.

SE: clustered by anomaly (and two-way by anomaly & month in the demanding
specs). Two-way anomaly+month FE via linearmodels.PanelOLS.

Outputs: output/tables/t1_sumstats.csv ... t6_eventtime.csv
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed')
OUT  = os.path.join(HERE, 'output', 'tables'); os.makedirs(OUT, exist_ok=True)
LOG  = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'reg_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

d = pd.read_csv(os.path.join(PROC, 'anomaly_panel.csv'))
d['date'] = pd.to_datetime(d['date'])
log(f'panel: {len(d):,} anomaly-months, {d.signal.nunique()} anomalies, '
    f'{d.date.dt.year.min()}-{d.date.dt.year.max()}')

# ============================================================ helpers
def ols_cluster(df, formula, groups):
    """OLS with one- or two-way clustered SE (groups: Series or 2-col frame)."""
    g = groups.values if hasattr(groups, 'values') else groups
    return smf.ols(formula, df).fit(cov_type='cluster', cov_kwds={'groups': g})

def grab(m, name):
    return (m.params.get(name, np.nan), m.tvalues.get(name, np.nan))

INS_POOLED = d.loc[d.insample == 1, 'ret'].mean()   # pooled in-sample mean (%)

# ============================================================ T1 summary stats
n_anom = d.signal.nunique()
reg = d.groupby('regime')['ret'].agg(n_obs='count', mean='mean', sd='std', med='median')
reg = reg.reindex(['insample', 'postsample', 'postpub'])
reg['n_anom'] = [d.loc[d.regime == r, 'signal'].nunique() for r in reg.index]
reg['pct_of_insample'] = 100 * reg['mean'] / reg.loc['insample', 'mean']
t1 = reg.reset_index().rename(columns={'index': 'regime'})
# header block: overall panel facts
facts = pd.DataFrame({
    'stat': ['n_anomalies', 'n_anomaly_months', 'first_year', 'last_year',
             'median_months_per_anomaly', 'n_risk_framed', 'n_mispricing_framed',
             'pooled_insample_mean_pct'],
    'value': [n_anom, len(d), int(d.date.dt.year.min()), int(d.date.dt.year.max()),
              int(d.groupby('signal').size().median()),
              int(d.groupby('signal')['risk_framed'].first().sum()),
              int((1 - d.groupby('signal')['risk_framed'].first()).sum()),
              round(INS_POOLED, 4)]})
t1.to_csv(os.path.join(OUT, 't1_sumstats.csv'), index=False)
facts.to_csv(os.path.join(OUT, 't1_facts.csv'), index=False)
log('T1 regime summary:\n' + t1.round(4).to_string(index=False))
log('T1 facts:\n' + facts.to_string(index=False))

# ============================================================ T2 regime means + decays
# equal-weighted across anomalies: per-anomaly regime mean, then average
pa = d.groupby(['signal', 'regime'])['ret'].mean().unstack()
rows = []
for r in ['insample', 'postsample', 'postpub']:
    s = pa[r].dropna()
    tval = s.mean() / (s.std() / np.sqrt(len(s)))
    rows.append({'regime': r, 'ew_mean': s.mean(), 'ew_t': tval, 'n_anom': len(s),
                 'pooled_mean': d.loc[d.regime == r, 'ret'].mean()})
t2 = pd.DataFrame(rows)
t2['ew_pct_of_insample'] = 100 * t2['ew_mean'] / t2.loc[0, 'ew_mean']
# paired declines (per anomaly, vs its own in-sample mean)
declines = []
for r in ['postsample', 'postpub']:
    sub = pa[['insample', r]].dropna()
    diff = sub[r] - sub['insample']
    tval = diff.mean() / (diff.std() / np.sqrt(len(diff)))
    declines.append({'contrast': f'{r} - insample', 'mean_diff': diff.mean(),
                     't': tval, 'n_anom': len(diff),
                     'pct_decline': 100 * diff.mean() / sub['insample'].mean()})
t2b = pd.DataFrame(declines)
t2.to_csv(os.path.join(OUT, 't2_regime_means.csv'), index=False)
t2b.to_csv(os.path.join(OUT, 't2_declines.csv'), index=False)
log('T2 regime means (equal-weight across anomalies):\n' + t2.round(4).to_string(index=False))
log('T2 paired declines:\n' + t2b.round(4).to_string(index=False))

# ============================================================ T3 progressive panel regressions
def run_spec(df, fe, cluster2):
    """Return dict with postsample, postpub (mutually-exclusive) and pub_extra
       (nested Pub coef) under a given FE / clustering scheme."""
    grp = df[['sid', 'mid']] if cluster2 else df['sid']
    if fe == 'none':
        m = ols_cluster(df, 'ret ~ postsample + postpub', grp)
        mn = ols_cluster(df, 'ret ~ oos + pub', grp)
        N, R2 = int(m.nobs), m.rsquared
    elif fe == 'anom':
        m = ols_cluster(df, 'ret ~ postsample + postpub + C(sid)', grp)
        mn = ols_cluster(df, 'ret ~ oos + pub + C(sid)', grp)
        N, R2 = int(m.nobs), m.rsquared
    elif fe == 'anom_year':
        m = ols_cluster(df, 'ret ~ postsample + postpub + C(sid) + C(year)', grp)
        mn = ols_cluster(df, 'ret ~ oos + pub + C(sid) + C(year)', grp)
        N, R2 = int(m.nobs), m.rsquared
    elif fe == 'anom_month':  # two-way FE via PanelOLS
        p = df.set_index(['sid', 'date'])
        m = PanelOLS.from_formula('ret ~ postsample + postpub + EntityEffects + TimeEffects',
                                  p).fit(cov_type='clustered', cluster_entity=True, cluster_time=True)
        mn = PanelOLS.from_formula('ret ~ oos + pub + EntityEffects + TimeEffects',
                                   p).fit(cov_type='clustered', cluster_entity=True, cluster_time=True)
        ps, pst = m.params['postsample'], m.tstats['postsample']
        pp, ppt = m.params['postpub'], m.tstats['postpub']
        pe, pet = mn.params['pub'], mn.tstats['pub']
        return dict(postsample=ps, postsample_t=pst, postpub=pp, postpub_t=ppt,
                    pub_extra=pe, pub_extra_t=pet, N=int(m.nobs), R2=float(m.rsquared_within))
    ps, pst = grab(m, 'postsample'); pp, ppt = grab(m, 'postpub')
    pe, pet = grab(mn, 'pub')
    return dict(postsample=ps, postsample_t=pst, postpub=pp, postpub_t=ppt,
                pub_extra=pe, pub_extra_t=pet, N=N, R2=R2)

specs = [
    ('(1) No FE',              'none',       False, 'anomaly'),
    ('(2) Anomaly FE',         'anom',       False, 'anomaly'),
    ('(3) Anomaly + Year FE',  'anom_year',  True,  'anomaly & month'),
    ('(4) Anomaly + Month FE', 'anom_month', True,  'anomaly & month'),
]
rows = []
for name, fe, c2, clab in specs:
    r = run_spec(d, fe, c2)
    r['spec'] = name; r['cluster'] = clab
    r['pct_decline_postpub'] = 100 * r['postpub'] / INS_POOLED
    rows.append(r)
    log(f'{name}: postsample={r["postsample"]:.4f}(t={r["postsample_t"]:.2f}) '
        f'postpub={r["postpub"]:.4f}(t={r["postpub_t"]:.2f}) '
        f'pub_extra={r["pub_extra"]:.4f}(t={r["pub_extra_t"]:.2f}) N={r["N"]}')
t3 = pd.DataFrame(rows)[['spec', 'postsample', 'postsample_t', 'postpub', 'postpub_t',
                         'pub_extra', 'pub_extra_t', 'pct_decline_postpub', 'cluster', 'N', 'R2']]
t3.to_csv(os.path.join(OUT, 't3_panel.csv'), index=False)

# ============================================================ T4 heterogeneity (risk vs mispricing)
def hetero(df, riskvar, label):
    f = (f'ret ~ postsample + postpub + postpub:{riskvar} + postsample:{riskvar} + {riskvar}')
    m = ols_cluster(df, f, df['sid'])
    out = {'split': label}
    for k, col in [('postpub', 'postpub'), (f'postpub:{riskvar}', 'postpub_x_risk'),
                   ('postsample', 'postsample'), (f'postsample:{riskvar}', 'postsample_x_risk'),
                   (riskvar, 'risk_main')]:
        c, t = grab(m, k); out[col] = c; out[col + '_t'] = t
    out['N'] = int(m.nobs)
    # implied post-pub decline for each group
    out['decay_mispricing'] = out['postpub']
    out['decay_risk'] = out['postpub'] + out['postpub_x_risk']
    return out
rows = [hetero(d, 'risk_framed', 'Broad risk proxy (incl. liquidity)'),
        hetero(d, 'risk_framed_narrow', 'Narrow risk proxy (excl. liquidity)')]
t4 = pd.DataFrame(rows)
t4.to_csv(os.path.join(OUT, 't4_hetero.csv'), index=False)
log('T4 heterogeneity:\n' + t4.round(4).to_string(index=False))

# ============================================================ T5 robustness
rob = []
# (a) normalized DV: 100 = own in-sample mean, so coef reads as % of in-sample
dn = d.dropna(subset=['ret_norm'])
m = ols_cluster(dn, 'ret_norm ~ postsample + postpub + C(sid)', dn['sid'])
rob.append({'spec': 'Normalized DV (in-sample=100), Anom FE',
            'postsample': m.params['postsample'], 'postsample_t': m.tvalues['postsample'],
            'postpub': m.params['postpub'], 'postpub_t': m.tvalues['postpub'], 'N': int(m.nobs)})
# (b) modern era only (>=1963, CRSP/Compustat era)
dm = d[d.year >= 1963]
m = ols_cluster(dm, 'ret ~ postsample + postpub + C(sid)', dm['sid'])
rob.append({'spec': 'Sample >= 1963, Anom FE',
            'postsample': m.params['postsample'], 'postsample_t': m.tvalues['postsample'],
            'postpub': m.params['postpub'], 'postpub_t': m.tvalues['postpub'], 'N': int(m.nobs)})
# (c) require >=36 post-pub months (well-measured post-pub anomalies)
good = d.groupby('signal')['postpub'].sum()
keep = good[good >= 36].index
dk = d[d.signal.isin(keep)]
m = ols_cluster(dk, 'ret ~ postsample + postpub + C(sid)', dk['sid'])
rob.append({'spec': f'>=36 post-pub months ({len(keep)} anomalies), Anom FE',
            'postsample': m.params['postsample'], 'postsample_t': m.tvalues['postsample'],
            'postpub': m.params['postpub'], 'postpub_t': m.tvalues['postpub'], 'N': int(m.nobs)})
# (d) winsorize returns 1/99
dw = d.copy(); lo, hi = dw.ret.quantile(.01), dw.ret.quantile(.99)
dw['ret'] = dw.ret.clip(lo, hi)
m = ols_cluster(dw, 'ret ~ postsample + postpub + C(sid)', dw['sid'])
rob.append({'spec': 'Winsorized 1/99, Anom FE',
            'postsample': m.params['postsample'], 'postsample_t': m.tvalues['postsample'],
            'postpub': m.params['postpub'], 'postpub_t': m.tvalues['postpub'], 'N': int(m.nobs)})
# (e) PLACEBO: fake publication year = pubyear - 12 (should show weaker/earlier effect)
dp = d.copy()
dp['pubyear_fake'] = dp['pubyear'] - 12
dp['postpub'] = (dp['year'] >= dp['pubyear_fake']).astype(int)
dp['postsample'] = ((dp['year'] > dp['sampend']) & (dp['year'] < dp['pubyear_fake'])).astype(int)
m = ols_cluster(dp, 'ret ~ postsample + postpub + C(sid)', dp['sid'])
rob.append({'spec': 'PLACEBO pub-year minus 12, Anom FE',
            'postsample': m.params['postsample'], 'postsample_t': m.tvalues['postsample'],
            'postpub': m.params['postpub'], 'postpub_t': m.tvalues['postpub'], 'N': int(m.nobs)})
t5 = pd.DataFrame(rob)
t5.to_csv(os.path.join(OUT, 't5_robust.csv'), index=False)
log('T5 robustness:\n' + t5.round(4).to_string(index=False))

# ============================================================ T6 event-time profile
# average LS return by event-year bin, relative to in-sample mean; for the figure
d['evt_bin'] = np.clip(d['evt_year'], -30, 20)
et = (d.groupby('evt_bin')['ret'].agg(mean='mean', n='count')).reset_index()
et['pct_of_insample'] = 100 * et['mean'] / INS_POOLED
et.to_csv(os.path.join(OUT, 't6_eventtime.csv'), index=False)
# also a compact 3-bucket "event-window" table (pre/around/well-after pub)
buckets = pd.cut(d['evt_year'], [-1e9, -1, 4, 9, 1e9],
                 labels=['pre-pub', '0-4y post', '5-9y post', '>=10y post'])
tb = d.groupby(buckets)['ret'].agg(mean='mean', n='count').reset_index()
tb.columns = ['event_window', 'mean_ret', 'n']
tb['pct_of_insample'] = 100 * tb['mean_ret'] / INS_POOLED
tb.to_csv(os.path.join(OUT, 't6_event_buckets.csv'), index=False)
log('T6 event buckets:\n' + tb.round(3).to_string(index=False))

log('regressions step complete -- all tables written to output/tables/')
logf.close()
