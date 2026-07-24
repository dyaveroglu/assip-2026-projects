#!/usr/bin/env python3
"""
Project 15 (Cohort capstone) — Step 00: pull a broad CRSP sample spanning every
event window in the 2023-2026 policy-shock atlas.

CRSP standard daily (crsp.dsf) ends 2024-12-31; 2025-2026 comes from crsp.dsf_v2.
Market benchmark = Fama-French daily (mkt = mktrf + rf), which extends to 2026.
Sample = ~2,000 largest firms (2022 market cap), window 2021-06 .. 2026-06.
"""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); os.makedirs(RAW, exist_ok=True)
def log(m): print(m, flush=True)

comp = pd.read_csv('/mnt/d/ccli/assip26/data/compustat_annual.csv')
top = (comp[comp.fyear == 2022].dropna(subset=['mktcap'])
       .sort_values('mktcap', ascending=False).head(2000))
permnos = tuple(int(x) for x in top.permno.unique())
log(f'sample: {len(permnos)} firms')

db = wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
# legacy daily through 2024
d1 = db.raw_sql(f"""SELECT permno, date, ret FROM crsp.dsf
                    WHERE permno IN {permnos} AND date BETWEEN '2021-06-01' AND '2024-12-31'""")
log(f'dsf (<=2024): {len(d1):,} rows')
# v2 daily for 2025-2026
try:
    d2 = db.raw_sql(f"""SELECT permno, dlycaldt AS date, dlyret AS ret FROM crsp.dsf_v2
                        WHERE permno IN {permnos} AND dlycaldt BETWEEN '2025-01-01' AND '2026-06-30'""")
    log(f'dsf_v2 (2025-26): {len(d2):,} rows ({d2.date.min()} .. {d2.date.max()})')
except Exception as e:
    d2 = pd.DataFrame(columns=['permno','date','ret']); log(f'dsf_v2 skipped: {repr(e)[:80]}')
dsf = pd.concat([d1, d2], ignore_index=True)
dsf.to_csv(os.path.join(RAW, 'crsp_daily.csv'), index=False)
log(f'combined daily: {len(dsf):,} rows for {dsf.permno.nunique()} firms')

ff = db.raw_sql("""SELECT date, mktrf, rf FROM ff.factors_daily
                   WHERE date BETWEEN '2021-06-01' AND '2026-06-30'""")
ff['mktret'] = pd.to_numeric(ff.mktrf, errors='coerce') + pd.to_numeric(ff.rf, errors='coerce')
ff.to_csv(os.path.join(RAW, 'ff_market.csv'), index=False)
log(f'FF market: {len(ff)} rows ({ff.date.min()} .. {ff.date.max()})')
db.close(); log('DONE')
