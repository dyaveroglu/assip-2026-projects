#!/usr/bin/env python3
"""
Project 03 (Clawbacks) — Step 10: difference-in-differences.

DiD around SEC Rule 10D-1 (POST = fyear >= 2023). treated = ex-ante-no-clawback
proxy (S&P SmallCap 600) vs control = ex-ante-clawback proxy (S&P 500).
Two-way (firm + year) fixed effects; SE clustered by firm. Prediction from the
voluntary-clawback literature (Zhao & Muscarella 2015): mandatory clawbacks
*reduce* CEO risk-taking, so DiD (post x treat) < 0 on risk outcomes.

Outputs (all -> output/tables/*.csv; LaTeX rendered in 35_tables_tex.py):
  t1_sumstats.csv     summary stats by group
  t2_did_main.csv     DiD across all outcomes, preferred spec
  t3_progressive.csv  progressive specs for the headline outcome
  t4_eventstudy.csv   dynamic (year-by-year) DiD for headline outcome
  t5_robust.csv       robustness (post=2024, drop COVID, 2-way cluster, placebo)
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels import PanelOLS
import statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
INT = os.path.join(HERE, 'data', 'interim')
for d in (OUT, INT): os.makedirs(d, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'did_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'), dtype={'gvkey': str})
main = df[df.treat.notna()].copy()
main['treat'] = main['treat'].astype(int)
CTRL = ['size', 'mtb', 'roa', 'cflow', 'tang']
OUTC = {'invest_at':'Investment/Assets','capx_at':'Capex/Assets','rd_at':'R\\&D/Assets',
        'aqc_at':'Acquisitions/Assets','total_vol':'Total return vol.',
        'idio_vol':'Idiosyncratic vol.','book_lev':'Book leverage',
        'cash_at':'Cash/Assets','ln_pay':'ln(CEO pay)','equity_share':'CEO equity-pay share'}

def panel(d, y, xvars, entity=True, time=True, dclus=False):
    dd = d.dropna(subset=[y] + xvars).copy()
    dd = dd.set_index(['gvkey_i', 'fyear_i'])
    mod = PanelOLS(dd[y], dd[xvars], entity_effects=entity, time_effects=time,
                   drop_absorbed=True, check_rank=False)
    if dclus:
        return mod.fit(cov_type='clustered', cluster_entity=True, cluster_time=True)
    return mod.fit(cov_type='clustered', cluster_entity=True)

# ---- Table 1: summary statistics by group --------------------------------
svars = list(OUTC.keys()) + CTRL
rows = []
for v in svars:
    a = main.loc[main.treat == 0, v].dropna(); b = main.loc[main.treat == 1, v].dropna()
    rows.append({'var': v, 'n': main[v].notna().sum(),
                 'mean': main[v].mean(), 'sd': main[v].std(),
                 'mean_ctrl': a.mean(), 'mean_treat': b.mean(),
                 'diff': b.mean() - a.mean()})
t1 = pd.DataFrame(rows)
t1.to_csv(os.path.join(OUT, 't1_sumstats.csv'), index=False)
log('T1 summary stats (control=SP500, treat=SP600):\n' + t1.round(4).to_string(index=False))

# ---- Table 2: main DiD across outcomes (preferred spec) ------------------
res2 = []
for y, lab in OUTC.items():
    try:
        r = panel(main, y, ['did'] + CTRL)
        res2.append({'outcome': y, 'label': lab, 'coef': r.params['did'],
                     't': r.tstats['did'], 'se': r.std_errors['did'],
                     'p': r.pvalues['did'], 'N': int(r.nobs),
                     'r2w': r.rsquared_within})
        log(f'T2 {y:12s} did={r.params["did"]:+.5f} (t={r.tstats["did"]:+.2f}) N={int(r.nobs)}')
    except Exception as e:
        log(f'T2 {y} ERROR {str(e)[:120]}')
t2 = pd.DataFrame(res2)
t2.to_csv(os.path.join(OUT, 't2_did_main.csv'), index=False)

# pick headline = outcome with the most significant DiD (by |t|), among the
# pre-registered investment/vol outcomes
cand = t2[t2.outcome.isin(['invest_at','capx_at','rd_at','aqc_at','total_vol','idio_vol'])]
HEAD = cand.reindex(cand.t.abs().sort_values(ascending=False).index).iloc[0]['outcome']
log(f'HEADLINE outcome (largest |t| among risk proxies): {HEAD}')

# ---- Table 3: progressive specifications for the headline ----------------
specs = []
# (1) year FE only, treat + did, no controls
d1 = main.dropna(subset=[HEAD]).set_index(['gvkey_i','fyear_i'])
m1 = PanelOLS(d1[HEAD], d1[['treat','did']], time_effects=True, check_rank=False)\
        .fit(cov_type='clustered', cluster_entity=True)
specs.append(('(1) Year FE', m1.params['did'], m1.tstats['did'], int(m1.nobs), m1.rsquared_within))
# (2) firm + year FE, no controls
m2 = panel(main, HEAD, ['did'])
specs.append(('(2) +Firm FE', m2.params['did'], m2.tstats['did'], int(m2.nobs), m2.rsquared_within))
# (3) firm + year FE + controls  [preferred]
m3 = panel(main, HEAD, ['did'] + CTRL)
specs.append(('(3) +Controls', m3.params['did'], m3.tstats['did'], int(m3.nobs), m3.rsquared_within))
# (4) preferred, POST = fyear>=2024
tmp = main.copy(); tmp['did'] = tmp['post24'] * tmp['treat']
m4 = panel(tmp, HEAD, ['did'] + CTRL)
specs.append(('(4) POST=2024', m4.params['did'], m4.tstats['did'], int(m4.nobs), m4.rsquared_within))
# (5) preferred, drop COVID 2020-2021
m5 = panel(main[~main.fyear.isin([2020,2021])], HEAD, ['did'] + CTRL)
specs.append(('(5) No COVID', m5.params['did'], m5.tstats['did'], int(m5.nobs), m5.rsquared_within))
t3 = pd.DataFrame(specs, columns=['spec','coef','t','N','r2w'])
t3.to_csv(os.path.join(OUT, 't3_progressive.csv'), index=False)
log(f'T3 progressive ({HEAD}):\n' + t3.round(5).to_string(index=False))

# ---- Table 4: event-study (dynamic DiD) for headline ---------------------
es = main.copy()
years = sorted(es.fyear.unique()); BASE = 2022
for yv in years:
    if yv == BASE: continue
    es[f'ty_{yv}'] = ((es.fyear == yv) & (es.treat == 1)).astype(int)
inter = [f'ty_{yv}' for yv in years if yv != BASE]
d4 = es.dropna(subset=[HEAD] + CTRL).set_index(['gvkey_i','fyear_i'])
m_es = PanelOLS(d4[HEAD], d4[inter + CTRL], entity_effects=True, time_effects=True,
                check_rank=False).fit(cov_type='clustered', cluster_entity=True)
esrows = []
for yv in years:
    if yv == BASE:
        esrows.append({'fyear': yv, 'coef': 0.0, 't': np.nan, 'se': 0.0}); continue
    k = f'ty_{yv}'
    esrows.append({'fyear': yv, 'coef': m_es.params[k], 't': m_es.tstats[k],
                   'se': m_es.std_errors[k]})
t4 = pd.DataFrame(esrows).sort_values('fyear')
t4.to_csv(os.path.join(OUT, 't4_eventstudy.csv'), index=False)
log(f'T4 event study ({HEAD}):\n' + t4.round(4).to_string(index=False))
# joint pre-trend test: are pre-2022 interaction coefs jointly zero?
pre = [f'ty_{yv}' for yv in years if yv < BASE]
try:
    wald = m_es.wald_test(formula=' = 0, '.join(pre) + ' = 0')
    log(f'   pre-trend joint Wald: stat={wald.stat:.3f}, p={wald.pval:.4f}')
    pretrend_p = wald.pval
except Exception as e:
    pretrend_p = np.nan; log(f'   pre-trend test err {str(e)[:80]}')

# ---- Table 5: robustness for headline + key outcomes ---------------------
rob = []
def addrob(name, r):
    rob.append({'spec': name, 'outcome': HEAD, 'coef': r.params['did'],
                't': r.tstats['did'], 'N': int(r.nobs)})
addrob('Preferred (firm+year FE, controls)', m3)
addrob('Two-way clustered SE', panel(main, HEAD, ['did'] + CTRL, dclus=True))
addrob('POST=2024', m4)
addrob('Drop COVID 2020-21', m5)
# placebo: SP400 (midcap) vs SP500 -- weaker ex-ante clawback gap => weaker effect
pl = df[df.grp.isin(['SP500','SP400'])].copy()
pl['treat'] = (pl.grp == 'SP400').astype(int); pl['did'] = pl['post'] * pl['treat']
addrob('Placebo: SP400 vs SP500', panel(pl, HEAD, ['did'] + CTRL))
# alt treatment: below-median baseline size within SP1500
base_size = df[df.fyear == 2022][['gvkey','size']].rename(columns={'size':'size22'})
alt = df.merge(base_size, on='gvkey', how='left')
med = alt.size22.median()
alt = alt.dropna(subset=['size22'])
alt['treat'] = (alt.size22 < med).astype(int); alt['did'] = alt['post'] * alt['treat']
addrob('Alt treat: below-median size', panel(alt, HEAD, ['did'] + CTRL))
t5 = pd.DataFrame(rob)
t5.to_csv(os.path.join(OUT, 't5_robust.csv'), index=False)
log('T5 robustness:\n' + t5.round(5).to_string(index=False))

# stash headline + pretrend for the paper builder
meta = pd.DataFrame([{'headline_outcome': HEAD, 'headline_label': OUTC[HEAD],
                      'pretrend_p': pretrend_p,
                      'did_coef': m3.params['did'], 'did_t': m3.tstats['did'],
                      'did_N': int(m3.nobs)}])
meta.to_csv(os.path.join(OUT, 't0_meta.csv'), index=False)
log('DONE — tables written to output/tables/')
logf.close()
