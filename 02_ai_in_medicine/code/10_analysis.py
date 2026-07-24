#!/usr/bin/env python3
"""
Project 02 — The Diffusion of AI into Medicine.

Uses the shared patent panel (AI ∩ CPC A61 medical patents, KPSS firm link, Compustat).
(1) Trend: growth of medical-AI patents. (2) Who captures it: incumbent health firms vs
entrant tech firms. (3) Value: do firms accumulating medical-AI patents have higher Q,
and is the effect larger for entrants?
"""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from linearmodels import PanelOLS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE,'output','tables'); os.makedirs(OUT, exist_ok=True)
SH = '/mnt/d/ccli/assip26/data'
p = pd.read_csv(f'{SH}/patent_analytical_panel.csv')
fy = pd.read_csv(f'{SH}/patent_firm_year.csv')
def log(m): print(m, flush=True)

def sector(s):
    try: s = int(s)
    except: return 'Other'
    if (2833<=s<=2836) or s in (3826,3827,3841,3842,3843,3845) or (8000<=s<=8099): return 'Incumbent (health)'
    if (7370<=s<=7379) or (3570<=s<=3579) or s in (3674,3661,3663,3669,3670,3672): return 'Entrant (tech)'
    return 'Other'
p['sector'] = p['sich'].map(sector)
p['entrant'] = (p.sector=='Entrant (tech)').astype(int)

# T1: trend of medical-AI patents (firm-matched)
tr = fy.groupby('year')[['ai','med','aimed','visai']].sum()
tr = tr[tr.index>=2000]
tr.to_csv(os.path.join(OUT,'t1_trend.csv'))
log('T1 medical-AI trend (recent):\n'+tr.tail(12).to_string())

# T2: who holds medical-AI patents, by sector
hold = (p[p.aimed>0].groupby('sector')
        .agg(firm_years=('permno','size'), firms=('permno','nunique'), aimed_patents=('aimed','sum')))
hold['share_patents'] = hold.aimed_patents/hold.aimed_patents.sum()
hold.to_csv(os.path.join(OUT,'t2_sector.csv'))
log('T2 medical-AI holders by sector:\n'+hold.round(3).to_string())

# T3: value regressions
def fe(y, xs, data, inter=False):
    d = data.dropna(subset=[y]+xs).copy().set_index(['permno','year'])
    return PanelOLS(d[y], d[xs], entity_effects=True, time_effects=True,
                    drop_absorbed=True, check_rank=False).fit(cov_type='clustered', cluster_entity=True)
p['ln_aimed_x_ent'] = p.ln_aimed * p.entrant
specs = [
    ('Q on med-AI', 'tobinq', ['ln_aimed','ln_ai','ln_med','size']),
    ('Q on med-AI $\\times$ entrant', 'tobinq', ['ln_aimed','ln_aimed_x_ent','entrant','ln_ai','ln_med','size']),
    ('ln(MktCap) on med-AI', 'mktcap_ln', ['ln_aimed','ln_ai','ln_med','size']),
]
p['mktcap_ln'] = np.log(p.mktcap.replace(0,np.nan))
rows=[]
for name,y,xs in specs:
    r = fe(y,xs,p)
    d={'spec':name,'N':int(r.nobs),'r2':r.rsquared_within}
    for x in ['ln_aimed','ln_aimed_x_ent']:
        if x in r.params: d[x]=r.params[x]; d[x+'_t']=r.tstats[x]
    rows.append(d)
t3 = pd.DataFrame(rows); t3.to_csv(os.path.join(OUT,'t3_value.csv'), index=False)
log('T3 value regressions (ln_aimed = medical-AI stock):\n'+t3.round(4).to_string(index=False))
