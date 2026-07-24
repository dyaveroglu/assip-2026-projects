#!/usr/bin/env python3
"""
Project 09 (ChatGPT) — Step 20: build the analytical panel, long-short portfolios,
and cross-sectional CAR regressions.

Question: around ChatGPT (and GPT-4), did high-AI-exposure firms earn abnormal
returns, and does the sign depend on whether AI SUBSTITUTES for the firm's core
output (substitution bucket) vs COMPLEMENTS its labor (supplier / user buckets)?

Design:
  DV  = market-model CAR (primary: car_0_5_cg, the 5-day post-ChatGPT window).
  Key = z_aiie  (Felten-Raj-Seamans AI Industry Exposure, 4-digit NAICS,
                 winsorized 1/99 and standardized -> coef = effect of +1 SD).
  Controls (predetermined): ln(ME), 6-mo momentum, B/M, ln(emp).
  SE  : clustered by 4-digit NAICS (exposure varies at the industry level) as the
        MAIN standard error; HC1 reported as robustness.

Long-short: AIIE quintiles (equal-weighted), Q5-Q1 CAR with a two-sample t.
Heterogeneity: supplier / substitution / user buckets (the SIGN channel).
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
for d in (PROC, OUT): os.makedirs(d, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'reg_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()
def wins(s, p=0.01):
    lo, hi = s.quantile(p), s.quantile(1-p); return s.clip(lo, hi)
def z(s):
    return (s - s.mean())/s.std()

# ------------------------------------------------------------- assemble ------
cars = pd.read_csv(os.path.join(INT, 'cars.csv'))
uni = pd.read_csv(os.path.join(RAW, 'crsp_universe.csv'))[['permno','permco','ticker','comnam','siccd','naics4']]
aiie = pd.read_csv(os.path.join(INT, 'aiie_by_naics4.csv'))
buck = pd.read_csv(os.path.join(INT, 'naics_buckets.csv'))[['naics4','bucket']]
link = pd.read_csv(os.path.join(RAW, 'ccm_link.csv'))
fun = pd.read_csv(os.path.join(RAW, 'compustat_funda.csv'))

# size + momentum from CRSP daily
dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date']); dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
me = dsf[(dsf.date >= '2022-10-01') & (dsf.date <= '2022-10-31')].sort_values('date')
me = me.groupby('permno').tail(1).copy()
me['ME'] = me['prc'].abs() * me['shrout']            # $000
me = me[['permno','ME']]
mm = dsf[(dsf.date >= '2022-05-01') & (dsf.date <= '2022-10-31')].dropna(subset=['ret'])
mom = mm.groupby('permno')['ret'].apply(lambda r: np.prod(1+r.values)-1).rename('mom').reset_index()

df = uni.merge(aiie[['naics4','aiie','industry']], on='naics4', how='inner')
df = df.merge(buck, on='naics4', how='left')
df = df.merge(cars, on='permno', how='inner')
df = df.merge(me, on='permno', how='left').merge(mom, on='permno', how='left')
# compustat controls
fun = fun.merge(link, on='gvkey', how='inner')
df = df.merge(fun[['permno','ceq','emp','at','sale']], on='permno', how='left')
df['bm'] = (df['ceq']*1000.0) / df['ME']            # ceq in $mn, ME in $000
df['lnme'] = np.log(df['ME'].clip(lower=1))
df['lnemp'] = np.log(df['emp'].clip(lower=0.001))
log(f'merged panel: {len(df)} firms; matched AIIE industries={df.naics4.nunique()}; '
    f'bucket counts={df.bucket.value_counts().to_dict()}')

# winsorize + z-score
for v in ['aiie','lnme','mom','bm','lnemp']:
    df[v+'_w'] = wins(df[v])
    df['z_'+v] = z(df[v+'_w'])
# CAR outliers: winsorize the DV lightly to tame micro-cap noise (report raw too)
for c in [c for c in df.columns if c.startswith('car_')]:
    df[c+'_w'] = wins(df[c], 0.005)
df.to_csv(os.path.join(PROC, 'analytical_panel.csv'), index=False)
log(f'wrote analytical_panel.csv ({len(df)} firms)')

FIN = df.siccd.between(6000, 6999)   # financial SIC (SVB-confound-sensitive)
df['financial'] = FIN.astype(int)

# ---------------- Table 1: summary statistics -------------------------------
svars = {'car_0_5_cg':'CAR[0,+5] ChatGPT','car_0_10_cg':'CAR[0,+10] ChatGPT',
         'car_0_5_g4':'CAR[0,+5] GPT-4','aiie':'AIIE (industry AI exposure)',
         'lnme':'ln(ME)','mom':'6-mo momentum','bm':'Book/Market','lnemp':'ln(employees)'}
t1 = df[list(svars)].rename(columns=svars).describe(percentiles=[.25,.5,.75]).T
t1 = t1[['count','mean','std','25%','50%','75%']]
t1.to_csv(os.path.join(OUT,'t1_sumstats.csv'))
log('T1 summary stats:\n'+t1.round(4).to_string())

# ---------------- Table 2: AIIE-quintile long-short (both events) ----------
def quintile_ls(col):
    d = df.dropna(subset=[col,'aiie']).copy()
    d['q'] = pd.qcut(d.aiie, 5, labels=[1,2,3,4,5])
    g = d.groupby('q')[col].agg(['mean','count'])
    lo = d[d.q==1][col]; hi = d[d.q==5][col]
    diff = hi.mean()-lo.mean()
    se = np.sqrt(hi.var()/len(hi)+lo.var()/len(lo)); t = diff/se
    return g, diff, t, len(d)
rows=[]
for col,lbl in [('car_0_1_cg','ChatGPT $[0,+1]$'),('car_0_5_cg','ChatGPT $[0,+5]$'),
                ('car_0_10_cg','ChatGPT $[0,+10]$'),('car_pre_cg','ChatGPT $[-10,-2]$ plac.'),
                ('car_0_5_g4','GPT-4 $[0,+5]$'),('car_0_10_g4','GPT-4 $[0,+10]$')]:
    g,diff,t,n = quintile_ls(col)
    row={'window':lbl}
    for q in [1,2,3,4,5]:
        row[f'Q{q}']=g.loc[q,'mean']
    row['LS_Q5_Q1']=diff; row['t_LS']=t; row['N']=n
    rows.append(row)
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT,'t2_longshort.csv'), index=False)
log('T2 AIIE quintile mean CAR + long-short:\n'+t2.round(4).to_string(index=False))

# ---------------- Table 3: cross-sectional regressions (ChatGPT) -----------
def fit(formula, data, cluster=None):
    d = data.dropna(subset=[formula.split('~')[0].strip()] +
                    [t for t in ['z_aiie','z_lnme','z_mom','z_bm','z_lnemp'] if t in formula])
    if cluster:
        return smf.ols(formula, d).fit(cov_type='cluster', cov_kwds={'groups': d[cluster]}), d
    return smf.ols(formula, d).fit(cov_type='HC1'), d

# Primary DV = CAR[0,+10] ChatGPT (diffuse-adoption window). Col (5) confirms in
# the tight [0,+1] window. All specs industry-clustered.
specs = {
 '(1)': 'car_0_10_cg_w ~ z_aiie',
 '(2)': 'car_0_10_cg_w ~ z_aiie + z_lnme + z_mom',
 '(3)': 'car_0_10_cg_w ~ z_aiie + z_lnme + z_mom + z_bm + z_lnemp',
 '(4)': 'car_0_10_cg_w ~ z_aiie + z_lnme + z_mom + z_bm + z_lnemp',   # non-financial
 '(5)': 'car_0_1_cg_w ~ z_aiie + z_lnme + z_mom + z_bm + z_lnemp',    # tight [0,+1]
}
terms=['z_aiie','z_lnme','z_mom','z_bm','z_lnemp','Intercept']
tbl=[]
for name,f in specs.items():
    data = df[df.financial==0] if name=='(4)' else df
    m,d = fit(f, data, cluster='naics4')
    col={'spec':name,'N':int(m.nobs),'R2':m.rsquared,'nclust':d.naics4.nunique()}
    for t in terms:
        if t in m.params: col[t]=m.params[t]; col[t+'_t']=m.tvalues[t]
    tbl.append(col)
t3=pd.DataFrame(tbl); t3.to_csv(os.path.join(OUT,'t3_crosssec.csv'), index=False)
log('T3 cross-sectional (DV=CAR ChatGPT; industry-clustered t):\n'+t3.round(4).to_string(index=False))

# ---------------- Table 4: SIGN channel — substitution vs complement -------
# mean CAR by bucket + interaction test
bmean=[]
for col,lbl in [('car_0_5_cg','ChatGPT [0,+5]'),('car_0_10_cg','ChatGPT [0,+10]'),('car_0_5_g4','GPT-4 [0,+5]')]:
    for b in ['supplier','substitution','user']:
        s=df[df.bucket==b][col].dropna()
        bmean.append({'window':lbl,'bucket':b,'mean_CAR':s.mean(),'t':s.mean()/(s.std()/np.sqrt(len(s))) if len(s)>1 else np.nan,'N':len(s)})
t4a=pd.DataFrame(bmean); t4a.to_csv(os.path.join(OUT,'t4_buckets.csv'), index=False)
log('T4a mean CAR by bucket:\n'+t4a.round(4).to_string(index=False))

# SIGN test: bucket-dummy regression (base = user). Coefs = differential CAR of
# AI SUPPLIERS and SUBSTITUTION-threatened firms vs ordinary AI users, over the
# diffuse-adoption [0,+10] ChatGPT window, with predetermined controls.
d=df.dropna(subset=['car_0_10_cg_w','z_lnme','z_mom','z_bm','z_lnemp']).copy()
d['substitution']=(d.bucket=='substitution').astype(int)
d['supplier']=(d.bucket=='supplier').astype(int)
mi=smf.ols('car_0_10_cg_w ~ supplier + substitution + z_lnme + z_mom + z_bm + z_lnemp',
           d).fit(cov_type='cluster',cov_kwds={'groups':d.naics4})
inter=[]
for k in ['supplier','substitution','z_lnme','z_mom','Intercept']:
    if k in mi.params: inter.append({'term':k,'coef':mi.params[k],'t':mi.tvalues[k]})
# difference supplier - substitution
diff = mi.params['supplier']-mi.params['substitution']
inter.append({'term':'supplier - substitution (diff)','coef':diff,'t':np.nan})
t4b=pd.DataFrame(inter); t4b['N']=int(mi.nobs); t4b['R2']=mi.rsquared; t4b['nclust']=d.naics4.nunique()
t4b.to_csv(os.path.join(OUT,'t4_interaction.csv'), index=False)
log('T4b bucket-dummy sign test (DV=CAR[0,+10] ChatGPT; base=user):\n'+t4b.round(4).to_string(index=False))

# ---------------- Table 5: robustness --------------------------------------
rob=[]
def add(name, formula, data, dv, cluster='naics4', hc1=False):
    if hc1:
        d=data.dropna(subset=[dv]); m=smf.ols(formula,d).fit(cov_type='HC1')
    else:
        m,d=fit(formula,data,cluster=cluster)
    row={'spec':name,'coef_aiie':m.params.get('z_aiie',np.nan),
         't_aiie':m.tvalues.get('z_aiie',np.nan),'N':int(m.nobs),'R2':m.rsquared}
    rob.append(row)
FULL='z_aiie + z_lnme + z_mom + z_bm + z_lnemp'
add('ChatGPT [0,+5], HC1 SE', f'car_0_5_cg_w ~ {FULL}', df, 'car_0_5_cg_w', hc1=True)
add('ChatGPT [0,+5], drop financials', f'car_0_5_cg_w ~ {FULL}', df[df.financial==0], 'car_0_5_cg_w')
add('ChatGPT [0,+1]', f'car_0_1_cg_w ~ {FULL}', df, 'car_0_1_cg_w')
add('ChatGPT [-1,+1]', f'car_m1_1_cg_w ~ {FULL}', df, 'car_m1_1_cg_w')
add('ChatGPT [-10,-2] PLACEBO', f'car_pre_cg_w ~ {FULL}', df, 'car_pre_cg_w')
add('GPT-4 [0,+5] (SVB-contaminated)', f'car_0_5_g4_w ~ {FULL}', df, 'car_0_5_g4_w')
add('GPT-4 [0,+5], drop financials', f'car_0_5_g4_w ~ {FULL}', df[df.financial==0], 'car_0_5_g4_w')
t5=pd.DataFrame(rob); t5.to_csv(os.path.join(OUT,'t5_robust.csv'), index=False)
log('T5 robustness (coef/t on z_aiie):\n'+t5.round(4).to_string(index=False))

log('DONE 20_regressions'); logf.close()
