#!/usr/bin/env python3
"""Shared Compustat annual pull for the patent papers (#01, #02).
Writes assip26/data/compustat_annual.csv keyed by permno-fyear with firm outcomes."""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, wrds

SHARED = '/mnt/d/ccli/assip26/data'; os.makedirs(SHARED, exist_ok=True)
db = wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
print('connected', flush=True)

fu = db.raw_sql("""
SELECT gvkey, datadate, fyear, sich, naicsh, at, sale, revt, ni, emp, xrd, ceq,
       csho, prcc_f, dltt, dlc, che, oibdp, capx, xsga
FROM comp.funda
WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
  AND fyear BETWEEN 1990 AND 2024
""")
print('funda rows', len(fu), flush=True)
lk = db.raw_sql("""
SELECT gvkey, lpermno AS permno, linkdt, linkenddt, linktype, linkprim
FROM crsp.ccmxpf_lnkhist
WHERE linktype IN ('LC','LU','LS') AND linkprim IN ('P','C')
""")
db.close()

fu['datadate'] = pd.to_datetime(fu['datadate'])
lk['linkdt'] = pd.to_datetime(lk['linkdt'])
lk['linkenddt'] = pd.to_datetime(lk['linkenddt']).fillna(pd.Timestamp('2030-12-31'))
m = fu.merge(lk, on='gvkey', how='inner')
m = m[(m.datadate >= m.linkdt) & (m.datadate <= m.linkenddt)]
m = m.sort_values(['permno','fyear','linkprim']).drop_duplicates(['permno','fyear'], keep='first')

for c in ['at','sale','revt','ni','emp','xrd','ceq','csho','prcc_f','dltt','dlc','che','oibdp','capx','xsga']:
    m[c] = pd.to_numeric(m[c], errors='coerce')
m['size'] = np.log(m['at'].clip(lower=1))
m['roa'] = m['ni'] / m['at'].clip(lower=1)
me = m['csho'] * m['prcc_f']
m['tobinq'] = (m['at'] - m['ceq'] + me) / m['at'].clip(lower=1)
m['lev'] = (m['dltt'].fillna(0) + m['dlc'].fillna(0)) / m['at'].clip(lower=1)
m['sale_emp'] = m['sale'] / m['emp'].replace(0, np.nan)     # productivity ($M/1000 emp)
m['rd_at'] = m['xrd'].fillna(0) / m['at'].clip(lower=1)
m['mktcap'] = me
keep = ['permno','fyear','gvkey','sich','naicsh','at','sale','ni','emp','xrd','size','roa',
        'tobinq','lev','sale_emp','rd_at','mktcap','capx']
m[keep].to_csv(os.path.join(SHARED, 'compustat_annual.csv'), index=False)
print('WROTE compustat_annual.csv', len(m), 'permno-years,', m.permno.nunique(), 'firms', flush=True)
