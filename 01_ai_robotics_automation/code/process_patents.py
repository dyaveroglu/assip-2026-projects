#!/usr/bin/env python3
"""
Shared patent panel builder (projects #01 and #02). Runs ON HOPPER where the raw
data lives (/scratch/lgao9/assip26_patents/). Produces a firm(permno)-year panel
flagging AI (USPTO AIPD), robotics (CPC B25J), and medical (CPC A61) patents,
linked to CRSP firms via the KPSS patent->permno crosswalk, with KPSS market value.

Outputs to /groups/LGAO/assip26/data/:
  patent_firm_year.csv   permno, year, n_patents, ai, rob, med, aimed, xi_sum
  patent_firm_first.csv  permno, first_ai_year, first_rob_year, first_med_year
"""
import os, re, pandas as pd, numpy as np

D = '/scratch/lgao9/assip26_patents'
OUT = '/groups/LGAO/assip26/data'; os.makedirs(OUT, exist_ok=True)
def norm(s): return s.astype(str).str.replace(r'\D', '', regex=True)
def log(m): print(m, flush=True)

# --- KPSS: patent -> permno, value, year ----------------------------------
k = pd.read_csv(f'{D}/KPSS_2024.csv', usecols=['patent_num','permno','issue_date','xi_real'],
                dtype={'patent_num': str})
k['pn'] = norm(k['patent_num'])
k['year'] = pd.to_numeric(k['issue_date'], errors='coerce') // 10000  # issue_date is YYYYMMDD int
k = k.dropna(subset=['permno', 'year'])
k = k[(k['year'] >= 1926) & (k['year'] <= 2025)]
k['permno'] = k['permno'].astype(float).astype(int)
k['year'] = k['year'].astype(int)
log(f'KPSS patents matched to firms: {len(k):,}  ({k.permno.nunique():,} firms, '
    f'years {k.year.min()}-{k.year.max()})')

# --- AIPD: AI flag (granted patents only) ---------------------------------
ai_head = pd.read_csv(f'{D}/ai_model_predictions.csv', nrows=0).columns.tolist()
comp = [c for c in ai_head if c.startswith('predict50_') and c != 'predict50_any_ai']
ai = pd.read_csv(f'{D}/ai_model_predictions.csv',
                 usecols=['doc_id','flag_patent','predict50_any_ai']+comp,
                 dtype={'doc_id': str})
ai = ai[ai['flag_patent'].astype(str).isin(['1','1.0','True'])]
ai['pn'] = norm(ai['doc_id'])
def truthy(col): return ai[col].astype(str).isin(['1','1.0','True'])
ai_ids = set(ai.loc[truthy('predict50_any_ai'), 'pn'])
# vision-AI (for medical-AI imaging/diagnostics angle in #02)
vis_col = next((c for c in comp if 'vision' in c), None)
vis_ids = set(ai.loc[truthy(vis_col), 'pn']) if vis_col else set()
log(f'AIPD granted patents: {len(ai):,}; AI-flagged: {len(ai_ids):,}; vision-AI: {len(vis_ids):,}')
del ai  # free memory before the big CPC read

# --- CPC: robotics (B25J), robotics-broad, medical (A61), chunked ----------
# robotics-broad = industrial manipulators (B25J) + autonomous-vehicle control
# (G05D1) + legged/walking machines (B62D57) + robotics cross-ref (Y10S901).
rob_ids, med_ids, robbroad_ids = set(), set(), set()
for chunk in pd.read_csv(f'{D}/g_cpc_current.tsv', sep='\t',
                         usecols=['patent_id','cpc_subclass','cpc_group'], dtype=str, chunksize=3_000_000):
    sub = chunk['cpc_subclass'].fillna('').str.upper()
    grp = chunk['cpc_group'].fillna('').str.upper().str.replace(' ', '')
    pn = norm(chunk['patent_id'])
    is_b25j = sub.eq('B25J')
    rob_ids.update(pn[is_b25j].tolist())
    med_ids.update(pn[sub.str.startswith('A61')].tolist())
    is_broad = (is_b25j | grp.str.startswith('G05D1') | grp.str.startswith('B62D57')
                | grp.str.startswith('Y10S901'))
    robbroad_ids.update(pn[is_broad].tolist())
log(f'CPC robotics B25J: {len(rob_ids):,}; robotics-broad: {len(robbroad_ids):,}; medical A61: {len(med_ids):,}')

# --- flag KPSS (firm-matched) patents -------------------------------------
k['is_ai']  = k.pn.isin(ai_ids)
k['is_rob'] = k.pn.isin(rob_ids)
k['is_robbroad'] = k.pn.isin(robbroad_ids)
k['is_med'] = k.pn.isin(med_ids)
k['is_visai'] = k.pn.isin(vis_ids)
k['is_aimed'] = k.is_ai & k.is_med
k['is_airob'] = k.is_ai & k.is_rob
log(f'firm-matched: AI={k.is_ai.sum():,}  robotics={k.is_rob.sum():,}  '
    f'medical={k.is_med.sum():,}  AI&medical={k.is_aimed.sum():,}')

# --- firm-year panel ------------------------------------------------------
fy = k.groupby(['permno','year']).agg(
    n_patents=('pn','size'), ai=('is_ai','sum'), rob=('is_rob','sum'),
    robbroad=('is_robbroad','sum'),
    med=('is_med','sum'), aimed=('is_aimed','sum'), airob=('is_airob','sum'),
    visai=('is_visai','sum'), xi_sum=('xi_real','sum')).reset_index()
fy.to_csv(f'{OUT}/patent_firm_year.csv', index=False)

first = pd.DataFrame({'permno': sorted(k.permno.unique())}).set_index('permno')
for flag, name in [('is_ai','first_ai_year'),('is_rob','first_rob_year'),
                   ('is_robbroad','first_robbroad_year'),
                   ('is_med','first_med_year'),('is_aimed','first_aimed_year')]:
    first[name] = k[k[flag]].groupby('permno').year.min()
first.reset_index().to_csv(f'{OUT}/patent_firm_first.csv', index=False)
log(f'WROTE {OUT}/patent_firm_year.csv ({len(fy):,} firm-years) and patent_firm_first.csv')
log('DONE')
