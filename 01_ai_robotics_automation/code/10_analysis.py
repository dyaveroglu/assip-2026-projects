#!/usr/bin/env python3
"""
Project 01 — Cognitive vs Physical Automation: firm outcomes from AI vs robotics patents.

Design 1: two-way (firm + year) fixed-effects panel of firm outcomes on cumulative
          AI-patent stock vs robotics-patent stock. Do cognitive (AI) and physical
          (robotics) innovation associate with DIFFERENT labor/productivity outcomes?
Design 2: event study around a firm's FIRST AI patent (well-powered; 4,277 adopters).
"""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels import PanelOLS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); os.makedirs(OUT, exist_ok=True)
p = pd.read_csv('/mnt/d/ccli/assip26/data/patent_analytical_panel.csv')

def log(m): print(m, flush=True)

# ---- Table 1: summary stats ----
sv = ['ln_emp','ln_prod','roa','tobinq','ln_ai','ln_rob','ai_share','rob_share','size']
t1 = p[sv].describe(percentiles=[.25,.5,.75]).T[['count','mean','std','25%','50%','75%']]
t1.to_csv(os.path.join(OUT,'t1_sumstats.csv')); log('T1:\n'+t1.round(3).to_string())

# ---- Design 1: two-way FE panel ----
def fe(y, xs, data):
    d = data.dropna(subset=[y]+xs).copy()
    d = d.set_index(['permno','year'])
    res = PanelOLS(d[y], d[xs], entity_effects=True, time_effects=True,
                   drop_absorbed=True, check_rank=False).fit(cov_type='clustered', cluster_entity=True)
    return res
XS = ['ln_ai','ln_rob','size']
rows=[]
for y,lab in [('ln_emp','ln(Employment)'),('ln_prod','ln(Sales/Emp)'),('roa','ROA'),('tobinq',"Tobin's Q")]:
    r = fe(y, XS, p)
    row={'outcome':lab,'N':int(r.nobs),'r2':r.rsquared_within}
    for x in XS:
        row[x]=r.params[x]; row[x+'_t']=r.tstats[x]
    rows.append(row)
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT,'t2_panelfe.csv'), index=False)
log('T2 two-way FE (coef, _t = clustered t):\n'+t2.round(4).to_string(index=False))

# ---- Design 2: AI-adoption event study ----
adopt = p[(p.first_ai_year>=2000)&(p.first_ai_year<=2020)].copy()
adopt['k'] = (adopt.year - adopt.first_ai_year).clip(-5,5)
es_rows=[]
for y,lab in [('ln_emp','ln(Employment)'),('ln_prod','ln(Sales/Emp)')]:
    d = adopt.dropna(subset=[y]).copy()
    # relative-time dummies, base = -1
    for k in range(-5,6):
        if k==-1: continue
        d[f'k_{k}'] = (d.k==k).astype(int)
    kcols=[f'k_{k}' for k in range(-5,6) if k!=-1]
    dd=d.set_index(['permno','year'])
    r=PanelOLS(dd[y], dd[kcols], entity_effects=True, time_effects=True,
               drop_absorbed=True, check_rank=False).fit(cov_type='clustered', cluster_entity=True)
    for k in range(-5,6):
        if k==-1:
            es_rows.append({'outcome':lab,'k':k,'coef':0.0,'t':np.nan}); continue
        es_rows.append({'outcome':lab,'k':k,'coef':r.params[f'k_{k}'],'t':r.tstats[f'k_{k}']})
    log(f'  event study {lab}: N={int(r.nobs)}')
t3 = pd.DataFrame(es_rows); t3.to_csv(os.path.join(OUT,'t3_eventstudy.csv'), index=False)
log('T3 AI-adoption event study written')

# ---- robustness: robotics adoption (thin: 354 firms) — honest power note ----
rob = p[(p.first_rob_year>=2000)&(p.first_rob_year<=2020)].copy()
log(f'robotics adopters in window: {rob.permno.nunique()} firms (thin — report as underpowered)')

# ---- Robustness: BROADENED robotics (B25J + autonomous vehicles + legged robots) ----
XSB = ['ln_ai','ln_robbroad','size']
rowsb = []
for y,lab in [('ln_emp','ln(Employment)'),('ln_prod','ln(Sales/Emp)'),('roa','ROA'),('tobinq',"Tobin's Q")]:
    r = fe(y, XSB, p)
    row = {'outcome':lab,'N':int(r.nobs),'r2':r.rsquared_within}
    for x in XSB: row[x]=r.params[x]; row[x+'_t']=r.tstats[x]
    rowsb.append(row)
t4 = pd.DataFrame(rowsb); t4.to_csv(os.path.join(OUT,'t4_robbroad.csv'), index=False)
log('T4 robustness (broadened robotics, ln_robbroad):\n'+t4.round(4).to_string(index=False))
n_rb = p[(p.first_robbroad_year>=2000)&(p.first_robbroad_year<=2020)].permno.nunique()
log(f'broadened-robotics adopters in window: {n_rb} firms (vs 354/165 for B25J-only)')
