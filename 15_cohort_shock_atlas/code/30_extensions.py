#!/usr/bin/env python3
"""
Project 15 (Cohort shock atlas) -- Step 30: journal-track extensions.

Adds TEN new real tables that turn the descriptive atlas into a meta-study of the
2022-2025 policy-shock wave, computed entirely from OBSERVABLE data (CRSP daily
returns, the Fama-French market benchmark, and generic Compustat firm
characteristics: market capitalization, market beta, industry, idiosyncratic
volatility). It deliberately does NOT construct any shock-specific firm-level
*exposure* measure or exact intraday event time -- those are the cohort's reserved
hand-collected contribution (STUDENT_TASKS.md), and the exposure->dispersion /
pre-announcement-leakage crosswalk is left explicitly as the reserved next step.

Firm-level workhorse:
  Phase A -- recompute per-firm market-model CARs for all 10 shocks (shared
             lib/event_study.py), cache the firm x shock panel, self-check the
             cross-sectional SD against the existing t1_atlas_full.csv.
  Phase B -- a residual-based placebo engine: one market model per firm over the
             full sample -> daily abnormal returns -> cross-sectional dispersion
             at the real event date vs. hundreds of random pseudo-event dates.

New tables (CSV -> paper/tables/*.tex):
  t3_diff.csv       Differentiation is real: event-window CAR dispersion vs a
                    placebo distribution of pseudo-event dispersions (per shock).
  t4_typebucket.csv Cross-shock comparison by coarse shock family (descriptive).
  t5_meta_re.csv    Random-effects (DerSimonian-Laird) meta-analysis of mean drift
                    and pre-window CAR across shocks; Q, tau^2, I^2.
  t6_rankcorr.csv   Do shocks rank the same across windows / dispersion measures?
                    Spearman rank correlations (cross-method robustness).
  t7_pooled.csv     Pooled firm x shock regression of |CAR[0,+1]| on OBSERVABLE
                    firm traits (size, beta, idio vol) with shock FE, SE clustered
                    by firm. The workhorse cross-sectional test.
  t8_beta.csv       Systematic vs idiosyncratic differentiation: share of the
                    cross-sectional CAR variance explained by market beta.
  t9_sizesplit.csv  Size-tercile subsample splits: dispersion / drift / reversal.
  t10_overreact.csv Aggregate over-reaction test: sort firms by announcement CAR,
                    measure subsequent drift by quintile (pooled across shocks).
  t11_boot.csv      Bootstrap + leave-one-shock-out jackknife of the headline
                    corr(|market move|, dispersion): how fragile is 0.69?
  t12_power.csv     Power / minimum detectable effects: per-shock mean-CAR MDE and
                    the cross-shock correlation detectable at 80% power (n=10).

Figures: fig3_placebo.pdf (placebo dispersion), fig4_forest.pdf (meta forest),
         fig5_bootstrap.pdf (headline-correlation bootstrap).
"""
import os, sys, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats as sps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from event_study import market_model_cars

RAW  = os.path.join(HERE, 'data', 'raw')
INT  = os.path.join(HERE, 'data', 'interim')
OUT  = os.path.join(HERE, 'output', 'tables')
TEX  = os.path.join(HERE, 'paper', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
LOG  = os.path.join(HERE, 'logs')
for d in (INT, OUT, TEX, FIG, LOG): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'extensions_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line, flush=True); logf.write(line + '\n'); logf.flush()
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)
def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''

np.random.seed(20260724)  # deterministic

EVENTS = [
    ('2022-08-09','CHIPS Act signed','Industrial policy'),
    ('2022-08-16','IRA / buyback excise tax','Tax'),
    ('2022-11-30','ChatGPT release','Technology'),
    ('2023-03-09','SVB collapse','Banking'),
    ('2023-03-14','GPT-4 release','Technology'),
    ('2024-02-05','SEC 5-day 13D rule','Disclosure'),
    ('2025-04-03','Reciprocal tariff shock','Trade'),
    ('2025-04-09','Tariff pause','Trade (reversal)'),
    ('2025-07-18','GENIUS Act signed','Crypto/regulatory'),
    ('2025-11-03','Reg NMS half-cent tick','Microstructure'),
]
# coarse family buckets (avoid singleton "types"): descriptive only
FAMILY = {
    'CHIPS Act signed':'Industrial/Tax','IRA / buyback excise tax':'Industrial/Tax',
    'ChatGPT release':'Technology','GPT-4 release':'Technology',
    'SVB collapse':'Financial','GENIUS Act signed':'Financial',
    'Reciprocal tariff shock':'Trade','Tariff pause':'Trade',
    'SEC 5-day 13D rule':'Micro/Disclosure','Reg NMS half-cent tick':'Micro/Disclosure',
}
WIN = {'pre':(-5,-1),'ann':(0,1),'wk':(0,5),'wide':(-5,10),'drift':(2,10)}

# ----------------------------------------------------------------------
log('loading data ...')
dsf = pd.read_csv(os.path.join(RAW,'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date']); dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
mkt = pd.read_csv(os.path.join(RAW,'ff_market.csv'))
mkt['date'] = pd.to_datetime(mkt['date']); mkt['mktret'] = pd.to_numeric(mkt['mktret'], errors='coerce')
mkt = mkt[['date','mktret']].dropna().sort_values('date').reset_index(drop=True)

comp = pd.read_csv('/mnt/d/ccli/assip26/data/compustat_annual.csv')
char = (comp[comp.fyear == 2022][['permno','mktcap','sich']].dropna(subset=['permno'])
        .drop_duplicates('permno'))
char['logmc'] = np.log(char['mktcap'].clip(lower=1e-3))
char['ind1']  = (char['sich'].fillna(0) // 1000).astype(int)   # 1-digit SIC industry
char = char[['permno','logmc','ind1']]

# ======================================================================
# PHASE A -- firm x shock CAR panel (shared lib)
# ======================================================================
cache = os.path.join(INT,'firm_cars_by_shock.csv')
log('PHASE A: firm-level CARs for 10 shocks (market model) ...')
frames = []
for date, name, typ in EVENTS:
    ev = pd.Timestamp(date)
    cars = market_model_cars(dsf, mkt, ev, est_window=(-252,-46), event_windows=WIN, min_obs=120)
    cars['event'] = name; cars['type'] = typ; cars['date'] = date; cars['family'] = FAMILY[name]
    frames.append(cars)
    log(f'  {name:26s} n={len(cars)} sd_ann={100*cars.ann.std():.3f}%')
fc = pd.concat(frames, ignore_index=True)
for c in ['pre','ann','wk','wide','drift']:
    fc[c+'_pct'] = 100*fc[c]
fc = fc.merge(char, on='permno', how='left')
fc.to_csv(cache, index=False)
log(f'  cached firm x shock panel: {len(fc):,} rows -> {cache}')

# self-check vs existing atlas
atlas_full = pd.read_csv(os.path.join(OUT,'t1_atlas_full.csv'))
chk = (fc.groupby('event')['ann'].std().mul(100).round(3)
       .rename('recomputed').reset_index()
       .merge(atlas_full[['event','sd_ann']].round(3), on='event'))
chk['diff'] = (chk['recomputed'] - chk['sd_ann']).abs()
log('SELF-CHECK recomputed sd_ann vs t1_atlas_full (max abs diff = %.4f):' % chk['diff'].max())
log('\n'+chk.to_string(index=False))
assert chk['diff'].max() < 0.05, 'recomputed dispersion diverges from atlas -- investigate'

# per-shock summary reused below
def shock_summary(g):
    return pd.Series({
        'n':len(g),'mkt': np.nan,
        'mean_ann':g.ann_pct.mean(),'sd_ann':g.ann_pct.std(),
        'mean_pre':g.pre_pct.mean(),'sd_pre':g.pre_pct.std(),
        'mean_drift':g.drift_pct.mean(),'sd_drift':g.drift_pct.std(),
        'rev': g[['ann','drift']].dropna().corr().iloc[0,1] if len(g)>30 else np.nan})
S = fc.groupby('event').apply(shock_summary)
mkt_move = atlas_full.set_index('event')['mkt_ann_pct']
S['mkt'] = mkt_move.reindex(S.index)
S['family'] = pd.Series({e:FAMILY[e] for e in S.index})
S = S.reset_index()

# ======================================================================
# PHASE B -- residual-based placebo engine (one market model per firm)
# ======================================================================
log('PHASE B: full-sample market model per firm -> daily abnormal returns ...')
d = dsf.dropna(subset=['ret']).merge(mkt, on='date', how='inner')
# vectorized per-firm OLS: beta = cov(r,m)/var(m); alpha = mean r - beta mean m
g = d.groupby('permno')
n   = g['ret'].transform('count')
mr  = g['ret'].transform('mean'); mm = g['mktret'].transform('mean')
cov = g.apply(lambda x: ((x.ret-x.ret.mean())*(x.mktret-x.mktret.mean())).sum()).rename('cov')
var = g['mktret'].apply(lambda x: ((x-x.mean())**2).sum()).rename('var')
cnt = g['ret'].count().rename('cnt')
bt  = (cov/var).rename('beta')
firmpar = pd.concat([bt, cnt], axis=1).reset_index()
firmpar = firmpar[firmpar.cnt >= 200].copy()
d = d.merge(firmpar[['permno','beta']], on='permno', how='inner')
am = d.groupby('permno').apply(lambda x: x.ret.mean() - x.beta.iloc[0]*x.mktret.mean()).rename('alpha').reset_index()
d = d.merge(am, on='permno', how='left')
d['ar'] = d['ret'] - (d['alpha'] + d['beta']*d['mktret'])
# AR matrix: rows = trading days (market calendar), cols = firm
cal = mkt['date'].reset_index(drop=True)
pos = {dt:i for i,dt in enumerate(cal)}
d = d[d.date.isin(pos)].copy()
d['di'] = d.date.map(pos)
armat = d.pivot_table(index='di', columns='permno', values='ar', aggfunc='first')
armat = armat.reindex(range(len(cal)))
A = armat.to_numpy()                       # (ndays x nfirms)
firms = armat.columns.to_numpy()
ndays = A.shape[0]
# per-firm idiosyncratic volatility (observable trait), in %
idio = pd.DataFrame({'permno':firms,'idio_vol':100*np.nanstd(A, axis=0)})
firm_beta = firmpar.set_index('permno')['beta']
log(f'  AR matrix {A.shape}, {len(firms)} firms with >=200 obs')

def xdisp(p, w0, w1):
    """cross-sectional SD (%) of CAR[w0,w1] for event at calendar position p."""
    lo, hi = p+w0, p+w1
    if lo < 0 or hi >= ndays: return np.nan
    car = np.nansum(A[lo:hi+1, :], axis=0)
    cnt = np.sum(~np.isnan(A[lo:hi+1, :]), axis=0)
    car = np.where(cnt >= (hi-lo+1), car, np.nan)     # require full window
    return 100*np.nanstd(car)

# real event positions and a placebo pool that avoids all event neighborhoods
evpos = {}
for date, name, typ in EVENTS:
    ev = pd.Timestamp(date); i = int(cal.searchsorted(ev)); evpos[name] = i
buffer = set()
for i in evpos.values():
    buffer.update(range(i-15, i+16))
pool = [p for p in range(260, ndays-15) if p not in buffer]
NPERM = 600
placebo_pos = np.random.choice(pool, size=NPERM, replace=False)
placebo_sd = np.array([xdisp(p, 0, 1) for p in placebo_pos])
placebo_sd = placebo_sd[~np.isnan(placebo_sd)]
log(f'  placebo pool={len(pool)} dates, drew {len(placebo_sd)} valid pseudo-event dispersions '
    f'(mean={placebo_sd.mean():.3f}%, sd={placebo_sd.std():.3f})')

# ======================================================================
# T3 -- differentiation permutation test (per shock)
# ======================================================================
log('T3 differentiation vs placebo ...')
rows = []
for date, name, typ in EVENTS:
    real = xdisp(evpos[name], 0, 1)
    p = float(np.mean(placebo_sd >= real))
    rows.append({'event':name,'type':typ,'real_sd':real,
                 'placebo_mean':placebo_sd.mean(),'ratio':real/placebo_sd.mean(),
                 'pctile':100*np.mean(placebo_sd < real),'p_emp':p})
t3 = pd.DataFrame(rows).sort_values('real_sd', ascending=False)
t3.to_csv(os.path.join(OUT,'t3_diff.csv'), index=False)
log('\n'+t3.round(3).to_string(index=False))

# ======================================================================
# T4 -- cross-shock comparison by coarse family (descriptive)
# ======================================================================
log('T4 by family (descriptive) ...')
fam = (S.groupby('family')
       .agg(k=('event','size'), mkt_abs=('mkt', lambda x: x.abs().mean()),
            disp=('sd_ann','mean'), drift=('mean_drift','mean'),
            rev=('rev','mean')).reset_index().sort_values('disp', ascending=False))
fam.to_csv(os.path.join(OUT,'t4_typebucket.csv'), index=False)
log('\n'+fam.round(3).to_string(index=False))

# ======================================================================
# T5 -- random-effects (DerSimonian-Laird) meta of mean drift & pre CAR
# ======================================================================
log('T5 random-effects meta ...')
def dersimonian_laird(y, v):
    y = np.asarray(y, float); v = np.asarray(v, float)
    wf = 1.0/v; ybar = np.sum(wf*y)/np.sum(wf)
    Q = float(np.sum(wf*(y-ybar)**2)); k = len(y); df = k-1
    C = np.sum(wf) - np.sum(wf**2)/np.sum(wf)
    tau2 = max(0.0, (Q-df)/C) if C > 0 else 0.0
    ws = 1.0/(v+tau2); mu = np.sum(ws*y)/np.sum(ws); se = np.sqrt(1.0/np.sum(ws))
    I2 = max(0.0, (Q-df)/Q)*100 if Q > 0 else 0.0
    pQ = 1 - sps.chi2.cdf(Q, df) if df > 0 else np.nan
    return dict(mu=mu, se=se, lo=mu-1.96*se, hi=mu+1.96*se, Q=Q, df=df, pQ=pQ, I2=I2, tau2=tau2)
rows = []
for lab, mcol, scol in [('Mean drift CAR[+2,+10]','mean_drift','sd_drift'),
                        ('Mean pre CAR[-5,-1]','mean_pre','sd_pre')]:
    y = S[mcol].values; v = (S[scol].values**2)/S['n'].values
    r = dersimonian_laird(y, v); r['stat'] = lab; rows.append(r)
t5 = pd.DataFrame(rows)[['stat','mu','se','lo','hi','Q','df','pQ','I2','tau2']]
t5.to_csv(os.path.join(OUT,'t5_meta_re.csv'), index=False)
log('\n'+t5.round(3).to_string(index=False))
# forest inputs for drift
forest = S[['event','mean_drift','sd_drift','n']].copy()
forest['se'] = forest['sd_drift']/np.sqrt(forest['n'])

# ======================================================================
# T6 -- rank correlations across windows / dispersion measures
# ======================================================================
log('T6 rank correlations across methods ...')
def disp_by(measure, col):
    if measure == 'SD':  return fc.groupby('event')[col].std()
    if measure == 'IQR': return fc.groupby('event')[col].apply(lambda x: x.quantile(.75)-x.quantile(.25))
    if measure == 'MAD': return fc.groupby('event')[col].apply(lambda x: (x-x.median()).abs().median())
series = {
    'SD[0,+1]':  disp_by('SD','ann_pct'),
    'SD[0,+5]':  disp_by('SD','wk_pct'),
    'SD[-5,+10]':disp_by('SD','wide_pct'),
    'IQR[0,+1]': disp_by('IQR','ann_pct'),
    'MAD[0,+1]': disp_by('MAD','ann_pct'),
}
D = pd.DataFrame(series)
keys = list(series.keys()); base = keys[0]
rc = []
for k in keys[1:]:
    rho, pv = sps.spearmanr(D[base], D[k])
    rc.append({'measure':k,'spearman_vs_base':rho,'p':pv})
t6 = pd.DataFrame(rc); t6.to_csv(os.path.join(OUT,'t6_rankcorr.csv'), index=False)
log('\n'+t6.round(3).to_string(index=False))

# ======================================================================
# T7 -- pooled firm x shock regression of |CAR[0,+1]| on observables
#        shock FE, SE clustered by firm
# ======================================================================
log('T7 pooled determinants of |CAR| ...')
reg = fc.merge(idio, on='permno', how='left')
reg['absCAR'] = reg['ann_pct'].abs()
reg = reg.dropna(subset=['absCAR','logmc','beta','idio_vol','ind1'])
reg['abeta'] = (reg['beta']-1).abs()
X = reg[['logmc','beta','idio_vol']].copy()
# shock fixed effects + industry FE
sh = pd.get_dummies(reg['event'], prefix='sh', drop_first=True).astype(float)
ind = pd.get_dummies(reg['ind1'], prefix='ind', drop_first=True).astype(float)
Xf = pd.concat([X, sh, ind], axis=1)
Xf = sm.add_constant(Xf)
m7 = sm.OLS(reg['absCAR'].values, Xf.values).fit(
        cov_type='cluster', cov_kwds={'groups':reg['permno'].values})
names = ['const'] + list(Xf.columns[1:])
keep = ['logmc','beta','idio_vol']
t7 = pd.DataFrame({'var':keep,
    'coef':[m7.params[names.index(k)] for k in keep],
    't':[m7.tvalues[names.index(k)] for k in keep]})
t7['label'] = ['Log market cap','Market beta','Idiosyncratic vol.\\ (\\%)']
t7 = t7[['label','coef','t']]
t7.attrs['N'] = int(m7.nobs); t7.attrs['R2'] = m7.rsquared
t7.to_csv(os.path.join(OUT,'t7_pooled.csv'), index=False)
extra7 = pd.DataFrame([{'N':int(m7.nobs),'R2':m7.rsquared,'nfirm':reg.permno.nunique(),
                        'shockFE':1,'indFE':1}]); extra7.to_csv(os.path.join(OUT,'t7_pooled_meta.csv'), index=False)
log(f'  N={int(m7.nobs)} firms={reg.permno.nunique()} R2={m7.rsquared:.3f}')
log('\n'+t7.round(4).to_string(index=False))

# ======================================================================
# T8 -- systematic vs idiosyncratic differentiation (beta share)
# ======================================================================
log('T8 beta share of dispersion ...')
rows = []
for date, name, typ in EVENTS:
    g = fc[fc.event == name].dropna(subset=['ann','beta'])
    if len(g) < 50: continue
    xx = sm.add_constant(g['beta'].values)
    r = sm.OLS(g['ann_pct'].values, xx).fit()
    rows.append({'event':name,'slope':r.params[1],'t':r.tvalues[1],'r2':r.rsquared,
                 'sd_total':g.ann_pct.std(),'sd_resid':np.std(r.resid, ddof=2)})
t8 = pd.DataFrame(rows)
t8['idio_share'] = 100*(t8['sd_resid']/t8['sd_total'])
t8 = t8.sort_values('r2', ascending=False)
t8.to_csv(os.path.join(OUT,'t8_beta.csv'), index=False)
log('\n'+t8.round(3).to_string(index=False))

# ======================================================================
# T9 -- size-tercile subsample splits
# ======================================================================
log('T9 size-tercile splits ...')
fc['sizeterc'] = fc.groupby('event')['logmc'].transform(
    lambda x: pd.qcut(x, 3, labels=['Small','Mid','Large']) if x.notna().sum() > 10 else np.nan)
rows = []
for lab in ['Small','Mid','Large']:
    g = fc[fc.sizeterc == lab]
    rev = g[['ann','drift']].dropna().corr().iloc[0,1]
    rows.append({'group':lab,'n':len(g),'disp_ann':g.ann_pct.std(),
                 'mean_drift':g.drift_pct.mean(),'sd_drift':g.drift_pct.std(),'rev':rev})
t9 = pd.DataFrame(rows); t9.to_csv(os.path.join(OUT,'t9_sizesplit.csv'), index=False)
log('\n'+t9.round(3).to_string(index=False))

# ======================================================================
# T10 -- aggregate over-reaction: sort by announcement CAR, look at drift
# ======================================================================
log('T10 over-reaction / drift by announcement quintile ...')
q = fc.dropna(subset=['ann','drift']).reset_index(drop=True).copy()
q['quint'] = q.groupby('event')['ann'].transform(
    lambda x: pd.qcut(x, 5, labels=[1,2,3,4,5], duplicates='drop')).astype(int)
rows = []
for k in [1,2,3,4,5]:
    g = q[q.quint == k]
    dr = g.drift_pct
    se = dr.std()/np.sqrt(len(dr))
    rows.append({'quintile':k,'n':len(g),'mean_ann':g.ann_pct.mean(),
                 'mean_drift':dr.mean(),'t_drift':dr.mean()/se})
t10 = pd.DataFrame(rows)
# Q5-Q1 spread and per-step slope: WITHIN-shock (shock FE), firm-clustered errors
mc = smf.ols('drift_pct ~ C(quint) + C(event)', data=q).fit(
        cov_type='cluster', cov_kwds={'groups': q['permno'].values})
ms = smf.ols('drift_pct ~ quint + C(event)', data=q).fit(
        cov_type='cluster', cov_kwds={'groups': q['permno'].values})
sp = float(mc.params['C(quint)[T.5]']); sesp = sp/float(mc.tvalues['C(quint)[T.5]'])
slope = float(ms.params['quint']); t_slope = float(ms.tvalues['quint'])
t10.attrs['spread']=sp; t10.attrs['tspread']=sp/sesp
sprow = pd.DataFrame([{'spread_Q5_Q1':sp,'t_spread':sp/sesp,
                       'slope_per_step':slope,'t_slope':t_slope,'N':int(mc.nobs)}])
sprow.to_csv(os.path.join(OUT,'t10_overreact_spread.csv'), index=False)
t10.to_csv(os.path.join(OUT,'t10_overreact.csv'), index=False)
log('\n'+t10.round(3).to_string(index=False)+f'\n  Q5-Q1 drift spread={sp:+.3f} (t={sp/sesp:+.2f})')

# ======================================================================
# T11 -- bootstrap + jackknife of the headline corr(|mkt move|, dispersion)
# ======================================================================
log('T11 bootstrap of headline correlation ...')
xx = S['mkt'].abs().values; yy = S['sd_ann'].values
point = np.corrcoef(xx, yy)[0,1]
B = 5000; k = len(xx); bs = []
for _ in range(B):
    idx = np.random.choice(k, k, replace=True)
    if np.std(xx[idx]) < 1e-9 or np.std(yy[idx]) < 1e-9: continue
    bs.append(np.corrcoef(xx[idx], yy[idx])[0,1])
bs = np.array(bs)
loo = np.array([np.corrcoef(np.delete(xx,i), np.delete(yy,i))[0,1] for i in range(k)])
drop_names = S['event'].values
t11 = pd.DataFrame([{'stat':'corr(|mkt move|, dispersion)','point':point,
    'boot_lo':np.percentile(bs,2.5),'boot_hi':np.percentile(bs,97.5),
    'loo_min':loo.min(),'loo_max':loo.max(),
    'most_infl_drop':drop_names[np.argmin(loo)],'loo_at_min':loo.min(),
    'B':len(bs)}])
t11.to_csv(os.path.join(OUT,'t11_boot.csv'), index=False)
log('\n'+t11.round(3).to_string(index=False))

# ======================================================================
# T12 -- power / minimum detectable effects
# ======================================================================
log('T12 power / MDE ...')
Z = 1.959964 + 0.841621   # 80% power, two-sided 5%
rows = []
for _, r in S.iterrows():
    se_mean = r['sd_ann']/np.sqrt(r['n'])
    rows.append({'event':r['event'],'n':int(r['n']),'sd_ann':r['sd_ann'],
                 'se_mean':se_mean,'mde_mean':Z*se_mean})
t12 = pd.DataFrame(rows)
t12.to_csv(os.path.join(OUT,'t12_power.csv'), index=False)
# cross-shock correlation MDE (n=10): Fisher z
nsh = len(S); se_z = 1.0/np.sqrt(nsh-3)
z_mde = Z*se_z; r_mde = np.tanh(z_mde)
xmeta = pd.DataFrame([{'n_shocks':nsh,'corr_point':point,'corr_mde_80':r_mde,
                       'se_fisher_z':se_z,'mean_mde_mean_pp':t12['mde_mean'].mean()}])
xmeta.to_csv(os.path.join(OUT,'t12_power_meta.csv'), index=False)
log('\n'+t12.round(4).to_string(index=False))
log(f'  cross-shock corr MDE(80%) with n={nsh}: {r_mde:.3f} (point corr={point:.3f})')

# ======================================================================
# FIGURES
# ======================================================================
log('figures ...')
# fig3: placebo dispersion distribution vs the two extreme real shocks
fig, ax = plt.subplots(figsize=(7.2,4.3))
ax.hist(placebo_sd, bins=40, color='0.78', edgecolor='0.45', lw=0.4,
        label=f'Placebo dispersions\n({len(placebo_sd)} pseudo-events)')
tar = t3[t3.event=='Reciprocal tariff shock'].real_sd.iloc[0]
d13 = t3[t3.event=='SEC 5-day 13D rule'].real_sd.iloc[0]
ax.axvline(tar, color='crimson', lw=2, label=f'Tariff shock ({tar:.1f}%)')
ax.axvline(d13, color='navy', lw=2, ls='--', label=f'13D rule ({d13:.1f}%)')
ax.set_xlabel('Cross-sectional SD of CAR[0,+1] (%)'); ax.set_ylabel('Frequency')
ax.set_title('Real event-window differentiation vs. placebo dates', fontsize=10)
ax.legend(frameon=False, fontsize=8); fig.tight_layout()
fig.savefig(os.path.join(FIG,'fig3_placebo.pdf')); plt.close(fig)

# fig4: forest plot of mean drift with RE pooled
ff = forest.sort_values('mean_drift').reset_index(drop=True)
fig, ax = plt.subplots(figsize=(7.2,5))
yv = np.arange(len(ff))
ax.errorbar(ff.mean_drift, yv, xerr=1.96*ff.se, fmt='s', ms=5, color='C0', ecolor='C7', capsize=2)
mu = t5.iloc[0]['mu']; lo = t5.iloc[0]['lo']; hi = t5.iloc[0]['hi']
ax.axvspan(lo, hi, color='crimson', alpha=0.15)
ax.axvline(mu, color='crimson', lw=1.5, label=f'RE pooled = {mu:+.2f}% [{lo:+.2f},{hi:+.2f}]')
ax.axvline(0, color='0.4', lw=0.8, ls=':')
ax.set_yticks(yv); ax.set_yticklabels(ff.event, fontsize=7.5)
ax.set_xlabel('Mean drift CAR[+2,+10] (%) $\\pm$ 95% CI'); ax.legend(frameon=False, fontsize=8, loc='lower right')
ax.set_title('Forest plot: post-event drift across shocks', fontsize=10); fig.tight_layout()
fig.savefig(os.path.join(FIG,'fig4_forest.pdf')); plt.close(fig)

# fig5: bootstrap distribution of the headline correlation
fig, ax = plt.subplots(figsize=(7.2,4.3))
ax.hist(bs, bins=45, color='0.78', edgecolor='0.45', lw=0.4)
ax.axvline(point, color='crimson', lw=2, label=f'Point = {point:.2f}')
ax.axvline(np.percentile(bs,2.5), color='navy', lw=1.2, ls='--',
           label=f'95% CI [{np.percentile(bs,2.5):.2f}, {np.percentile(bs,97.5):.2f}]')
ax.axvline(np.percentile(bs,97.5), color='navy', lw=1.2, ls='--')
ax.set_xlabel('corr(|market move|, cross-sectional dispersion), n=10'); ax.set_ylabel('Frequency')
ax.set_title('Bootstrap of the headline correlation', fontsize=10)
ax.legend(frameon=False, fontsize=8); fig.tight_layout()
fig.savefig(os.path.join(FIG,'fig5_bootstrap.pdf')); plt.close(fig)

# ======================================================================
# RENDER LaTeX
# ======================================================================
log('rendering tex ...')
# T3
body = ''.join(f"{r['event']} & {r['type']} & {r['real_sd']:.2f} & {r['placebo_mean']:.2f} & "
               f"{r['ratio']:.2f} & {r['pctile']:.1f} & {r['p_emp']:.3f} \\\\\n"
               for _,r in t3.iterrows())
w('tab_diff.tex', r"\begin{tabular}{llccccc}"+"\n\\toprule\n"
  r"Shock & Type & SD$_{\text{event}}$ & SD$_{\text{placebo}}$ & Ratio & Pctile & $p$ \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T4
body = ''.join(f"{r['family']} & {int(r['k'])} & {r['mkt_abs']:.2f} & {r['disp']:.2f} & "
               f"{r['drift']:+.2f} & {r['rev']:+.2f} \\\\\n" for _,r in fam.iterrows())
w('tab_typebucket.tex', r"\begin{tabular}{lccccc}"+"\n\\toprule\n"
  r"Shock family & \# & $|\text{Mkt}|$ & Dispersion & Drift & Reversal \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T5
body = ''.join(f"{r['stat']} & {r['mu']:+.3f} & [{r['lo']:+.3f}, {r['hi']:+.3f}] & {r['Q']:.1f} & "
               f"{r['pQ']:.3f} & {r['I2']:.0f}\\% & {r['tau2']:.3f} \\\\\n" for _,r in t5.iterrows())
w('tab_meta_re.tex', r"\begin{tabular}{lcccccc}"+"\n\\toprule\n"
  r"Statistic & RE pooled & 95\% CI & $Q$ & $p_Q$ & $I^2$ & $\tau^2$ \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T6
body = ''.join(f"{r['measure']} & {r['spearman_vs_base']:.3f} & {r['p']:.3f} \\\\\n" for _,r in t6.iterrows())
w('tab_rankcorr.tex', r"\begin{tabular}{lcc}"+"\n\\toprule\n"
  r"Dispersion measure & Spearman $\rho$ vs.\ SD[0,+1] & $p$ \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T7
body = ''.join(f"{r['label']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) \\\\\n" for _,r in t7.iterrows())
body += (r"\midrule Shock fixed effects & \multicolumn{2}{c}{Yes} \\"+"\n"
         r"Industry fixed effects & \multicolumn{2}{c}{Yes} \\"+"\n"
         f"Firm clusters & \\multicolumn{{2}}{{c}}{{{reg.permno.nunique():,}}} \\\\\n"
         f"$N$ (firm $\\times$ shock) & \\multicolumn{{2}}{{c}}{{{int(m7.nobs):,}}} \\\\\n"
         f"$R^2$ & \\multicolumn{{2}}{{c}}{{{m7.rsquared:.3f}}} \\\\\n")
w('tab_pooled.tex', r"\begin{tabular}{lcc}"+"\n\\toprule\n"
  r"Dependent variable: $|\text{CAR}[0,+1]|$ (\%) & Coef. & $t$ \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T8
body = ''.join(f"{r['event']} & {r['slope']:+.2f}{stars(r['t'])} & {r['r2']:.3f} & "
               f"{r['sd_total']:.2f} & {r['idio_share']:.1f}\\% \\\\\n" for _,r in t8.iterrows())
w('tab_beta.tex', r"\begin{tabular}{lcccc}"+"\n\\toprule\n"
  r"Shock & Beta slope & $R^2$ & SD$_{\text{tot}}$ & Idio.\ share \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T9
body = ''.join(f"{r['group']} & {int(r['n']):,} & {r['disp_ann']:.2f} & {r['mean_drift']:+.2f} & "
               f"{r['rev']:+.2f} \\\\\n" for _,r in t9.iterrows())
w('tab_sizesplit.tex', r"\begin{tabular}{lcccc}"+"\n\\toprule\n"
  r"Size tercile & $N$ & Dispersion & Mean drift & Reversal \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T10
body = ''.join(f"{int(r['quintile'])} & {int(r['n']):,} & {r['mean_ann']:+.2f} & {r['mean_drift']:+.2f} & "
               f"({r['t_drift']:+.2f}) \\\\\n" for _,r in t10.iterrows())
body += (r"\midrule Q5$-$Q1 spread & & & "
         f"{sp:+.2f} & ({sp/sesp:+.2f}) \\\\\n")
w('tab_overreact.tex', r"\begin{tabular}{lcccc}"+"\n\\toprule\n"
  r"Announcement quintile & $N$ & Mean CAR[0,+1] & Mean drift[+2,+10] & ($t$) \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T11
r = t11.iloc[0]
body = (f"Point estimate & {r['point']:.3f} \\\\\n"
        f"Bootstrap 95\\% CI ({int(r['B'])} reps) & [{r['boot_lo']:.3f}, {r['boot_hi']:.3f}] \\\\\n"
        f"Leave-one-shock-out range & [{r['loo_min']:.3f}, {r['loo_max']:.3f}] \\\\\n"
        f"Most influential shock (drop) & {r['most_infl_drop']} ($\\rho\\!\\to\\!{r['loo_at_min']:.3f}$) \\\\\n")
w('tab_boot.tex', r"\begin{tabular}{lc}"+"\n\\toprule\n"
  r"corr($|$market move$|$, dispersion), $n=10$ & Value \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

# T12
body = ''.join(f"{r['event']} & {int(r['n']):,} & {r['sd_ann']:.2f} & {r['se_mean']:.3f} & "
               f"{r['mde_mean']:.3f} \\\\\n" for _,r in t12.iterrows())
xm = xmeta.iloc[0]
body += (r"\midrule \multicolumn{5}{l}{\emph{Cross-shock correlation (n=10):} point "
         f"$={xm['corr_point']:.2f}$; MDE at 80\\% power $={xm['corr_mde_80']:.2f}$}} \\\\\n")
w('tab_power.tex', r"\begin{tabular}{lcccc}"+"\n\\toprule\n"
  r"Shock & $N$ & SD CAR[0,+1] & SE(mean) & MDE$_{80\%}$ \\"
  "\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")

log('DONE -- 10 extension tables + 3 figures written.')
print('tex files:', sorted(os.listdir(TEX)))
logf.close()
