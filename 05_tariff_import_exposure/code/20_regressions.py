#!/usr/bin/env python3
"""
Project 05 - Step 20: build the analytical panel + cross-sectional CAR regressions.

Q: Did high imported-input-exposure firms underperform on the Apr-2025 tariff
   SHOCK and rebound on the Apr-9 PAUSE (a paired, opposite-signed test)?

DV_shock = CAR[Apr3,Apr4] ; DV_pause = CAR[Apr9] ; DV_placebo = CAR[Mar27,Apr2].
Key regressor = z_imp_intensity (industry imported-input intensity, standardized).
Controls: size=ln(assets), market beta, COGS/sales, leverage, book/market.
SE clustered by NAICS-3 industry (exposure is measured at the industry level);
HC1 reported as robustness. Predictors winsorized 1/99 and standardized so a
coefficient reads as "CAR points per 1-SD increase in exposure".
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
LOG = os.path.join(HERE, 'logs')
for d in (PROC, OUT): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'reg_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()
def wins(s, p=0.01):
    lo, hi = s.quantile(p), s.quantile(1-p); return s.clip(lo, hi)
def z(s):
    return (s - s.mean())/s.std()

# ---- load pieces -----------------------------------------------------------
cars = pd.read_csv(os.path.join(INT, 'cars.csv'))
uni = pd.read_csv(os.path.join(RAW, 'universe.csv'))
comp = pd.read_csv(os.path.join(RAW, 'compustat_funda.csv'))
link = pd.read_csv(os.path.join(RAW, 'ccm_link.csv'))
xw = pd.read_csv(os.path.join(INT, 'industry_import_intensity.csv'))
xw['naics3'] = xw['naics3'].astype(str)

# ---- permno -> gvkey (CCM link active on 2025-03-31) -----------------------
EV = pd.Timestamp('2025-03-31')
link['linkdt'] = pd.to_datetime(link['linkdt'], errors='coerce')
link['linkenddt'] = pd.to_datetime(link['linkenddt'], errors='coerce')  # NaT = ongoing
lk = link[(link.linkdt <= EV) & (link.linkenddt.isna() | (link.linkenddt >= EV))].copy()
lk = lk.sort_values('linkprim').drop_duplicates('permno')            # prefer 'C'/'P'
log(f'active CCM links on {EV.date()}: {len(lk)} permnos')

# ---- Compustat: latest fundamentals per gvkey ------------------------------
comp['datadate'] = pd.to_datetime(comp['datadate'])
comp = comp.sort_values(['gvkey', 'datadate']).drop_duplicates('gvkey', keep='last')
comp = comp.merge(lk[['gvkey', 'permno']], on='gvkey', how='inner')
log(f'Compustat firms linked to a permno: {len(comp)}')

# ---- NAICS-3 industry key + import intensity -------------------------------
def naics3(x):
    try:
        s = str(int(float(x)))
        return s[:3] if len(s) >= 3 else s
    except Exception: return None
comp['naics3'] = comp['naicsh'].map(naics3)
comp = comp.merge(xw[['naics3', 'imp_intensity']], on='naics3', how='left')

# ---- firm controls ---------------------------------------------------------
comp['size'] = np.log(comp['at'].clip(lower=1))
comp['cogs_int'] = (comp['cogs'] / comp['sale'].replace(0, np.nan)).clip(0, 1.5)
comp['lev'] = (comp['dltt'].fillna(0) + comp['dlc'].fillna(0)) / comp['at'].clip(lower=1)
comp['mktcap'] = comp['csho'] * comp['prcc_f']
comp['bm'] = (comp['ceq'] / comp['mktcap'].replace(0, np.nan)).clip(-2, 20)
comp['manuf'] = comp['naics3'].astype(str).str[:2].isin(
    ['31', '32', '33']).astype(int)   # goods-producing manufacturing

# ---- merge to CARs ---------------------------------------------------------
df = cars.merge(comp[['permno', 'gvkey', 'tic', 'conm', 'naics3', 'imp_intensity',
                      'size', 'cogs_int', 'lev', 'bm', 'mktcap', 'manuf']],
                on='permno', how='inner')
df = df.merge(uni[['permno', 'ticker', 'comnam', 'siccd']], on='permno', how='left')
df = df.dropna(subset=['imp_intensity'])
log(f'analytical panel: {len(df)} firms with import intensity across '
    f'{df.naics3.nunique()} NAICS-3 industries')

# standardize (winsorized) predictors
for v in ['imp_intensity', 'size', 'cogs_int', 'lev', 'bm', 'beta']:
    df['z_'+v] = z(wins(df[v]))
df.to_csv(os.path.join(PROC, 'analytical_panel.csv'), index=False)

# ---- Table 1: summary statistics ------------------------------------------
svars = {'car_s01': 'CAR shock [Apr3,4]', 'car_p0': 'CAR pause [Apr9]',
         'car_pre': 'CAR pre [Mar27,Apr2]', 'car_round': 'CAR round-trip',
         'imp_intensity': 'Imported-input intensity', 'beta': 'Market beta',
         'size': 'ln(Assets)', 'cogs_int': 'COGS/Sales', 'lev': 'Leverage',
         'bm': 'Book/Market'}
t1 = df[list(svars)].rename(columns=svars).describe(percentiles=[.25, .5, .75]).T
t1 = t1[['count', 'mean', 'std', '25%', '50%', '75%']]
t1.to_csv(os.path.join(OUT, 't1_sumstats.csv'))
log('Table 1 (summary stats):\n' + t1.round(4).to_string())

# ---- Table 2: mean CARs by window (event summary) --------------------------
rows = []
for w, lbl in [('car_s0', 'Shock [Apr3]'), ('car_s01', 'Shock [Apr3,4]'),
               ('car_s03', 'Shock [Apr3-8]'), ('car_pre', 'Pre [Mar27-Apr2]'),
               ('car_p0', 'Pause [Apr9]'), ('car_p01', 'Pause [Apr9,10]'),
               ('car_p03', 'Pause [Apr9-14]')]:
    s = df[w].dropna(); t = s.mean()/(s.std()/np.sqrt(len(s)))
    rows.append({'window': lbl, 'mean': s.mean(), 'median': s.median(),
                 't_stat': t, 'n': len(s)})
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT, 't2_car_windows.csv'), index=False)
log('Table 2 (mean CARs by window; abnormal vs FF market):\n' + t2.round(4).to_string(index=False))

# ---- regression runner (cluster by NAICS-3) --------------------------------
def run(dv, rhs, data, cluster='naics3'):
    f = dv + ' ~ ' + ' + '.join(rhs)
    d = data.dropna(subset=[dv] + rhs + [cluster]).copy()
    m = smf.ols(f, data=d).fit(cov_type='cluster', cov_kwds={'groups': d[cluster]})
    return m
def tidy(specs, dv, data):
    terms = ['z_imp_intensity', 'z_size', 'z_beta', 'z_cogs_int', 'z_lev', 'z_bm', 'manuf', 'Intercept']
    out = []
    for name, rhs in specs.items():
        m = run(dv, rhs, data)
        col = {'spec': name, 'N': int(m.nobs), 'R2': m.rsquared,
               'nclust': int(m.df_resid and len(np.unique(m.model.data.orig_exog.index)) and 0) or 0}
        col['nclust'] = data.dropna(subset=[dv]+rhs+['naics3']).naics3.nunique()
        for t in terms:
            if t in m.params:
                col[t] = m.params[t]; col[t+'_t'] = m.tvalues[t]
        out.append(col)
    return pd.DataFrame(out)

base = ['z_imp_intensity']
spec_size = base + ['z_size', 'z_beta']
spec_full = spec_size + ['z_cogs_int', 'z_lev', 'z_bm']
spec_man = spec_full + ['manuf']
specs = {'(1)': base, '(2)': spec_size, '(3)': spec_full, '(4)': spec_man}

# ---- Table 3: SHOCK (DV = CAR[Apr3,4]) -------------------------------------
t3 = tidy(specs, 'car_s01', df); t3.to_csv(os.path.join(OUT, 't3_shock.csv'), index=False)
log('Table 3 (SHOCK, DV=CAR[Apr3,4]; z-preds; cluster-by-NAICS3 t in _t):\n' +
    t3.round(4).to_string(index=False))

# ---- Table 4: PAUSE (DV = CAR[Apr9]) ---------------------------------------
t4 = tidy(specs, 'car_p0', df); t4.to_csv(os.path.join(OUT, 't4_pause.csv'), index=False)
log('Table 4 (PAUSE, DV=CAR[Apr9]):\n' + t4.round(4).to_string(index=False))

# ---- Table 5: robustness (placebo, alt windows, round-trip, HC1) -----------
rob = []
def add(name, dv, rhs, data, cluster='naics3', cov='cluster'):
    d = data.dropna(subset=[dv]+rhs+([cluster] if cluster else [])).copy()
    if cov == 'cluster':
        m = smf.ols(dv+' ~ '+' + '.join(rhs), data=d).fit(cov_type='cluster', cov_kwds={'groups': d[cluster]})
    else:
        m = smf.ols(dv+' ~ '+' + '.join(rhs), data=d).fit(cov_type='HC1')
    rob.append({'test': name, 'dv': dv, 'coef_imp': m.params['z_imp_intensity'],
                't_imp': m.tvalues['z_imp_intensity'], 'N': int(m.nobs),
                'R2': m.rsquared, 'cov': cov})
add('Placebo pre-window', 'car_pre', spec_full, df)
add('Shock [Apr3] 1-day', 'car_s0', spec_full, df)
add('Shock [Apr3-8]', 'car_s03', spec_full, df)
add('Pause [Apr9,10]', 'car_p01', spec_full, df)
add('Round-trip (pause+shock)', 'car_round', spec_full, df)
add('Shock, HC1 SE', 'car_s01', spec_full, df, cov='HC1')
add('Pause, HC1 SE', 'car_p0', spec_full, df, cov='HC1')
add('Shock, ex-microcap', 'car_s01', spec_full, df[df.mktcap > 300])
add('Pause, ex-microcap', 'car_p0', spec_full, df[df.mktcap > 300])
t5 = pd.DataFrame(rob); t5.to_csv(os.path.join(OUT, 't5_robust.csv'), index=False)
log('Table 5 (robustness; imp-intensity coef & t):\n' + t5.round(4).to_string(index=False))

# ---- Table 6: mean CAR by imported-input-intensity quartile ---------------
d = df.dropna(subset=['imp_intensity', 'car_s01', 'car_p0']).copy()
d['q'] = pd.qcut(d.imp_intensity, 4, labels=['Q1 low', 'Q2', 'Q3', 'Q4 high'])
q = d.groupby('q').agg(n=('permno', 'size'),
                       shock=('car_s01', 'mean'), pause=('car_p0', 'mean'),
                       round=('car_round', 'mean'),
                       intensity=('imp_intensity', 'mean')).reset_index()
q.to_csv(os.path.join(OUT, 't6_quartiles.csv'), index=False)
log('Table 6 (mean CAR by import-intensity quartile):\n' + q.round(4).to_string(index=False))
log('DONE - tables written to output/tables/')
logf.close()
