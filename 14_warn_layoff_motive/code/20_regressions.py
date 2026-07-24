#!/usr/bin/env python3
"""
Project 14 (WARN) - Step 20: cross-sectional CAR analysis + tables.

Q: Do CARs to mass-layoff (WARN) announcements differ by the SIZE of the layoff,
   the SIZE of the firm, and (crudely) the layoff MOTIVE?

DV  = CAR[0,+5] (market model). Robustness on CAR[0,+2], CAR[-1,+5].
Key = rel_layoff (cluster headcount / firm employees), ln_headcount,
      ln_at (firm size), is_closure (closure vs ongoing-operation layoff -- a
      CRUDE automated proxy for strategic-exit vs cost-cutting; the hand-coded
      motive is the student task), is_tech.
Predictors winsorized 1/99 and z-scored (coeff = effect of +1 SD, in CAR pts).
SE  = clustered by firm (permno); some firms file multiple WARN events.

Writes t1..t6 CSVs to output/tables/. Every number traces to these CSVs.
Reports honest nulls -- most layoff-characteristic coefficients are ~0.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(HERE, 'data', 'interim'); PROC = os.path.join(HERE, 'data', 'processed')
OUT = os.path.join(HERE, 'output', 'tables'); LOG = os.path.join(HERE, 'logs')
for d in (PROC, OUT): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'reg_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

def wins(s, p=0.01):
    s = pd.to_numeric(s, errors='coerce'); lo, hi = s.quantile(p), s.quantile(1-p)
    return s.clip(lo, hi)
def z(s):
    return (s - s.mean()) / s.std()

cars = pd.read_csv(os.path.join(INT, 'cars.csv'), parse_dates=['event_date'])
ev = pd.read_csv(os.path.join(INT, 'warn_events.csv'), parse_dates=['event_date'])
df = cars.merge(ev, on=['permno', 'event_date'], how='inner', suffixes=('', '_ev'))
log(f'merged CAR x event panel: {len(df)} firm-events, {df.permno.nunique()} firms')

CARW = ['car_m1_1', 'car_0_1', 'car_0_2', 'car_0_5', 'car_m1_5', 'car_pre']
for v in ['rel_layoff', 'ln_headcount', 'ln_at', 'ln_mktcap', 'headcount']:
    df[v] = pd.to_numeric(df[v], errors='coerce')
for v in ['rel_layoff', 'ln_headcount', 'ln_at', 'ln_mktcap']:
    df['z_'+v] = z(wins(df[v]))
df['below_med_size'] = (df.ln_at < df.ln_at.median()).astype(int)
df.to_csv(os.path.join(PROC, 'analytical_panel.csv'), index=False)
log(f'analytical panel saved: {len(df)} rows; closures {int(df.is_closure.sum())}, '
    f'tech {int(df.is_tech.sum())}')

# ---- Table 1: summary statistics --------------------------------------
svars = {'car_0_5': 'CAR[0,+5]', 'car_0_2': 'CAR[0,+2]', 'car_m1_1': 'CAR[-1,+1]',
         'headcount': 'Layoff headcount', 'rel_layoff': 'Rel. layoff (head/emp)',
         'ln_at': 'ln(Assets)', 'ln_mktcap': 'ln(Mkt cap)',
         'is_closure': 'Closure (0/1)', 'is_tech': 'Tech (0/1)'}
t1 = df[list(svars)].rename(columns=svars).describe(percentiles=[.25, .5, .75]).T
t1 = t1[['count', 'mean', 'std', '25%', '50%', '75%']]
t1.to_csv(os.path.join(OUT, 't1_sumstats.csv'))
log('Table 1:\n' + t1.round(4).to_string())

# ---- Table 2: mean CARs by window (event-study result) ----------------
rows = []
lbl = {'car_m1_1': '[-1,+1]', 'car_0_1': '[0,+1]', 'car_0_2': '[0,+2]',
       'car_0_5': '[0,+5]', 'car_m1_5': '[-1,+5]', 'car_pre': '[-10,-2] placebo'}
for w in CARW:
    s = df[w].dropna(); t = s.mean() / (s.std()/np.sqrt(len(s)))
    pos = (s > 0).mean()
    rows.append({'window': lbl[w], 'mean': s.mean(), 'median': s.median(),
                 't_stat': t, 'pct_pos': pos, 'n': len(s)})
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT, 't2_car_windows.csv'), index=False)
log('Table 2 (CARs by window):\n' + t2.round(4).to_string(index=False))

# ---- Table 3: mean CAR[0,+5] by subgroup ------------------------------
def grp(mask, name):
    s = df.loc[mask, 'car_0_5'].dropna(); t = s.mean()/(s.std()/np.sqrt(len(s))) if len(s)>1 else np.nan
    return {'group': name, 'mean_car': s.mean(), 'median_car': s.median(), 't_stat': t, 'n': len(s)}
sz_med = df.ln_at.median()
g = [grp(df.is_closure == 1, 'Closure'), grp(df.is_closure == 0, 'Ongoing-op layoff'),
     grp(df.is_tech == 1, 'Tech'), grp(df.is_tech == 0, 'Non-tech'),
     grp(df.ln_at < sz_med, 'Small firm (below-median assets)'),
     grp(df.ln_at >= sz_med, 'Large firm (above-median assets)'),
     grp(df.rel_layoff >= df.rel_layoff.median(), 'Large rel. layoff (top half)'),
     grp(df.rel_layoff < df.rel_layoff.median(), 'Small rel. layoff (bottom half)')]
t3 = pd.DataFrame(g); t3.to_csv(os.path.join(OUT, 't3_car_groups.csv'), index=False)
log('Table 3 (CAR[0,+5] by group):\n' + t3.round(4).to_string(index=False))

# ---- Table 4: main cross-sectional regressions ------------------------
def run(formula, data, cluster='permno'):
    d = data.dropna(subset=[formula.split('~')[0].strip()] +
                    [t for t in ['z_rel_layoff','z_ln_headcount','z_ln_at','z_ln_mktcap']
                     if t in formula])
    m = smf.ols(formula, data=d).fit(cov_type='cluster',
                                     cov_kwds={'groups': d[cluster]})
    return m
specs = {
    '(1) Rel. layoff': 'car_0_5 ~ z_rel_layoff',
    '(2) ln(Headcount)': 'car_0_5 ~ z_ln_headcount',
    '(3) ln(Assets)': 'car_0_5 ~ z_ln_at',
    '(4) All three': 'car_0_5 ~ z_rel_layoff + z_ln_headcount + z_ln_at',
    '(5) +Motive/Tech/Yr FE': 'car_0_5 ~ z_rel_layoff + z_ln_headcount + z_ln_at + is_closure + is_tech + C(year)',
}
res = {n: run(f, df) for n, f in specs.items()}
terms = ['z_rel_layoff', 'z_ln_headcount', 'z_ln_at', 'is_closure', 'is_tech']
tbl = []
for n, m in res.items():
    col = {'spec': n, 'N': int(m.nobs), 'R2': m.rsquared}
    for t in terms:
        if t in m.params:
            col[t] = m.params[t]; col[t+'_t'] = m.tvalues[t]
    tbl.append(col)
t4 = pd.DataFrame(tbl); t4.to_csv(os.path.join(OUT, 't4_crosssec.csv'), index=False)
log('Table 4 (cross-section, DV=CAR[0,+5], z-scored, firm-clustered t):\n' +
    t4.round(4).to_string(index=False))

# ---- Table 5: heterogeneity / motive interactions ---------------------
rob = {
 'Closure x Rel.layoff': 'car_0_5 ~ z_rel_layoff*is_closure + z_ln_at',
 'Size x Rel.layoff': 'car_0_5 ~ z_rel_layoff*below_med_size + z_ln_at',
 'Tech x Rel.layoff': 'car_0_5 ~ z_rel_layoff*is_tech + z_ln_at',
}
rb = []
for n, f in rob.items():
    m = run(f, df)
    d = {'spec': n, 'N': int(m.nobs), 'R2': m.rsquared}
    for t in m.params.index:
        if t == 'Intercept': continue
        d[t] = m.params[t]; d[t+'_t'] = m.tvalues[t]
    rb.append(d)
t5 = pd.DataFrame(rb); t5.to_csv(os.path.join(OUT, 't5_hetero.csv'), index=False)
log('Table 5 (heterogeneity):\n' + t5.round(4).to_string(index=False))

# ---- Table 6: robustness (alt DV / sample / winsor) -------------------
def run_dv(dv, data, extra='z_rel_layoff + z_ln_headcount + z_ln_at + is_closure + is_tech'):
    f = f'{dv} ~ {extra}'
    return run(f, data)
r6 = []
for name, dv, data in [
    ('DV=CAR[0,+5] (base)', 'car_0_5', df),
    ('DV=CAR[0,+2]', 'car_0_2', df),
    ('DV=CAR[-1,+5]', 'car_m1_5', df),
    ('Exclude 2022', 'car_0_5', df[df.year != 2022]),
    ('US firms only', 'car_0_5', df[df.us == 1]),
    ('ln(Mktcap) for size', 'car_0_5', df),
]:
    if name == 'ln(Mktcap) for size':
        m = run('car_0_5 ~ z_rel_layoff + z_ln_headcount + z_ln_mktcap + is_closure + is_tech', data)
        key_size = 'z_ln_mktcap'
    else:
        m = run_dv(dv, data); key_size = 'z_ln_at'
    d = {'spec': name, 'N': int(m.nobs), 'R2': m.rsquared,
         'b_size': m.params.get(key_size, np.nan), 't_size': m.tvalues.get(key_size, np.nan),
         'b_rel': m.params.get('z_rel_layoff', np.nan), 't_rel': m.tvalues.get('z_rel_layoff', np.nan),
         'b_closure': m.params.get('is_closure', np.nan), 't_closure': m.tvalues.get('is_closure', np.nan)}
    r6.append(d)
t6 = pd.DataFrame(r6); t6.to_csv(os.path.join(OUT, 't6_robust.csv'), index=False)
log('Table 6 (robustness):\n' + t6.round(4).to_string(index=False))
log('DONE - tables t1..t6 written to output/tables/')
logf.close()
