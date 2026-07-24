#!/usr/bin/env python3
"""
Project 10 (SVB) — Step 20: cross-sectional CAR regressions + tables.

Q: In the SVB window, was the equity collapse driven more by uninsured-deposit
   exposure or by hidden HTM/securities losses, controlling for size?

DV  = CAR[0,+3] (market-model). Robustness: other windows, exclude GSIBs.
Key = uninsured_ratio (RCON5597 / assets), sec_loss_eq (unrealized securities
      loss / equity), htm_loss_eq (HTM-only). Predictors winsorized 1/99 and
      z-scored so coefficients read as "effect of a 1-SD increase, in CAR pts".
SE  = heteroskedasticity-robust (HC1).
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(HERE, 'data', 'interim'); PROC = os.path.join(HERE, 'data', 'processed')
OUT = os.path.join(HERE, 'output', 'tables'); os.makedirs(OUT, exist_ok=True); os.makedirs(PROC, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'reg_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

def wins(s, p=0.01):
    lo, hi = s.quantile(p), s.quantile(1-p); return s.clip(lo, hi)
def z(s):
    return (s - s.mean()) / s.std()

cars = pd.read_csv(os.path.join(INT, 'cars.csv'))
panel = pd.read_csv(os.path.join(INT, 'bank_reg_panel.csv'))
df = cars.merge(panel, on='permno', how='inner')
GSIB = {'JPM','BAC','C','WFC','GS','MS','BK','STT'}
df['gsib'] = df.ticker.isin(GSIB).astype(int)

for v in ['uninsured_ratio','htm_loss_eq','sec_loss_eq','size']:
    df[v+'_w'] = wins(df[v])
    df['z_'+v] = z(df[v+'_w'])
df.to_csv(os.path.join(PROC, 'analytical_panel.csv'), index=False)
log(f'merged analytical panel: {len(df)} banks (uninsured nonnull={df.uninsured_ratio.notna().sum()})')

# ---- Table 1: summary statistics -----------------------------------------
svars = {'car_0_3':'CAR[0,+3]', 'car_0_1':'CAR[0,+1]', 'uninsured_ratio':'Uninsured deposits/Assets',
         'sec_loss_eq':'Securities unreal. loss/Equity', 'htm_loss_eq':'HTM unreal. loss/Equity',
         'size':'ln(Assets)'}
t1 = df[list(svars)].rename(columns=svars).describe(percentiles=[.25,.5,.75]).T
t1 = t1[['count','mean','std','25%','50%','75%']]
t1.to_csv(os.path.join(OUT, 't1_sumstats.csv'))
log('Table 1 (summary stats):\n' + t1.round(4).to_string())

# ---- Table 2: correlations -----------------------------------------------
t2 = df[['car_0_3','uninsured_ratio','sec_loss_eq','htm_loss_eq','size']].corr()
t2.to_csv(os.path.join(OUT, 't2_corr.csv'))

# ---- Table 3: mean CARs by window (with t-stats) -------------------------
rows = []
for w, lbl in [('car_0_1','[0,+1]'),('car_0_3','[0,+3]'),('car_0_5','[0,+5]'),
               ('car_m1_3','[-1,+3]'),('car_pre','[-6,-2] placebo')]:
    s = df[w].dropna(); t = s.mean()/(s.std()/np.sqrt(len(s)))
    rows.append({'window':lbl,'mean':s.mean(),'median':s.median(),'t_stat':t,'n':len(s)})
t3 = pd.DataFrame(rows); t3.to_csv(os.path.join(OUT, 't3_car_windows.csv'), index=False)
log('Table 3 (CARs by window):\n' + t3.round(4).to_string(index=False))

# ---- Table 4: main cross-sectional horse race ----------------------------
specs = {
    '(1) Uninsured': 'car_0_3 ~ z_uninsured_ratio',
    '(2) Sec loss':  'car_0_3 ~ z_sec_loss_eq',
    '(3) Both':      'car_0_3 ~ z_uninsured_ratio + z_sec_loss_eq',
    '(4) + Size':    'car_0_3 ~ z_uninsured_ratio + z_sec_loss_eq + z_size',
    '(5) No GSIB':   'car_0_3 ~ z_uninsured_ratio + z_sec_loss_eq + z_size',
}
def run(formula, data):
    m = smf.ols(formula, data=data).fit(cov_type='HC1')
    return m
res = {}
for name, f in specs.items():
    data = df if name != '(5) No GSIB' else df[df.gsib == 0]
    res[name] = run(f, data.dropna(subset=['car_0_3'] + [t for t in ['z_uninsured_ratio','z_sec_loss_eq','z_size'] if t in f]))

# assemble a tidy coefficient table
terms = ['z_uninsured_ratio','z_sec_loss_eq','z_size','Intercept']
tbl = []
for name, m in res.items():
    col = {'spec': name, 'N': int(m.nobs), 'R2': m.rsquared}
    for t in terms:
        if t in m.params:
            col[t] = m.params[t]; col[t+'_t'] = m.tvalues[t]
    tbl.append(col)
t4 = pd.DataFrame(tbl)
t4.to_csv(os.path.join(OUT, 't4_crosssec.csv'), index=False)
log('Table 4 (cross-sectional horse race; z-scored predictors, HC1 t in _t):\n' +
    t4.round(4).to_string(index=False))

# ---- Table 5: robustness — HTM-only, alt window, sum-uninsured ------------
rob = {
 'HTM-only loss': 'car_0_3 ~ z_uninsured_ratio + z_htm_loss_eq + z_size',
 'DV=CAR[0,+1]':  'car_0_1 ~ z_uninsured_ratio + z_sec_loss_eq + z_size',
 'DV=CAR[-1,+3]': 'car_m1_3 ~ z_uninsured_ratio + z_sec_loss_eq + z_size',
}
rb = []
for name, f in rob.items():
    m = run(f, df.dropna(subset=[f.split('~')[0].strip()]))
    d = {'spec': name, 'N': int(m.nobs), 'R2': m.rsquared}
    for t in ['z_uninsured_ratio','z_sec_loss_eq','z_htm_loss_eq','z_size']:
        if t in m.params: d[t] = m.params[t]; d[t+'_t'] = m.tvalues[t]
    rb.append(d)
t5 = pd.DataFrame(rb); t5.to_csv(os.path.join(OUT, 't5_robust.csv'), index=False)
log('Table 5 (robustness):\n' + t5.round(4).to_string(index=False))
log('DONE — tables written to output/tables/')
logf.close()
