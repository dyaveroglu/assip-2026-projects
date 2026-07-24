#!/usr/bin/env python3
"""Shared firm-year analytical panel for the patent papers (#01, #02).
Merges the patent firm-year panel with Compustat outcomes; builds cumulative
AI/robotics/medical patent stocks and first-adoption event time.
Writes assip26/data/patent_analytical_panel.csv."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

SH = '/mnt/d/ccli/assip26/data'
fy = pd.read_csv(f'{SH}/patent_firm_year.csv')
first = pd.read_csv(f'{SH}/patent_firm_first.csv')
comp = pd.read_csv(f'{SH}/compustat_annual.csv').rename(columns={'fyear':'year'})

innov = set(first.permno) & set(comp.permno)
p = comp[comp.permno.isin(innov) & comp.year.between(1995, 2024)].copy()
p = p.merge(fy[['permno','year','ai','rob','robbroad','med','aimed','visai','n_patents','xi_sum']],
            on=['permno','year'], how='left')
for c in ['ai','rob','robbroad','med','aimed','visai','n_patents','xi_sum']:
    p[c] = p[c].fillna(0)
p = p.sort_values(['permno','year'])

# cumulative patent stocks
for c in ['ai','rob','robbroad','med','aimed','n_patents']:
    p[c+'_stk'] = p.groupby('permno')[c].cumsum()
p['ln_ai']  = np.log1p(p.ai_stk)
p['ln_rob'] = np.log1p(p.rob_stk)
p['ln_robbroad'] = np.log1p(p.robbroad_stk)
p['ln_med'] = np.log1p(p.med_stk)
p['ln_aimed'] = np.log1p(p.aimed_stk)
p['ln_pat'] = np.log1p(p.n_patents_stk)
# AI vs robotics tilt among patenters
p['ai_share']  = p.ai_stk / p.n_patents_stk.replace(0, np.nan)
p['rob_share'] = p.rob_stk / p.n_patents_stk.replace(0, np.nan)

# outcomes
p['ln_emp'] = np.log(p.emp.replace(0, np.nan))
p['prod']   = p.sale / p.emp.replace(0, np.nan)          # $M sales per 1000 employees
p['ln_prod']= np.log(p['prod'].replace(0, np.nan))

# first-adoption event time
p = p.merge(first, on='permno', how='left')
p['evt_ai']  = p.year - p.first_ai_year
p['evt_rob'] = p.year - p.first_rob_year
p['evt_robbroad'] = p.year - p.first_robbroad_year
p.to_csv(f'{SH}/patent_analytical_panel.csv', index=False)
print(f'analytical panel: {len(p):,} firm-years, {p.permno.nunique():,} firms')
print('nonmissing ln_emp:', p['ln_emp'].notna().sum(), '| prod:', p['prod'].notna().sum())
print(p[['ln_ai','ln_rob','ai_share','rob_share','ln_emp','prod','roa','tobinq']].describe().round(3).to_string())
