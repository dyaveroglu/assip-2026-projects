#!/usr/bin/env python3
"""
Project 08 — Step 05: post-filing returns and the final analytic sample.

For each candidate filing we compute buy-and-hold returns over the K trading
months AFTER the filing date (K = 3, 6, 12), and market-adjusted buy-and-hold
abnormal returns (BHAR):

    firm_cum_K   = prod_{m=1..K}(1 + r_{i,m}) - 1
    mkt_cum_K    = prod_{m=1..K}(1 + r_{mkt,m}) - 1        (r_mkt = mktrf + rf)
    BHAR_K       = firm_cum_K - mkt_cum_K

Firm returns: crsp.msf_v2 (monthly, through 2025-12). Market: ff.factors_monthly.
The first return month is the first month-end strictly after the filing date, so
the filing day itself is excluded. The final sample keeps filings with a valid
12-month BHAR (both windows have return data through 2025-12) and trims to
FINAL_PER_WINDOW per window with a fixed seed.
"""
import os, datetime, warnings, time
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs')
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'returns_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

SEED = 20260707
FINAL_PER_WINDOW = 110
HORIZONS = [3, 6, 12]

cand = pd.read_csv(os.path.join(INT, 'candidates.csv'))
cand['filing_date'] = pd.to_datetime(cand['filing_date'])
permnos = tuple(int(x) for x in cand.permno.unique())
log(f'candidates: {len(cand)} filings, {len(permnos)} permnos')

import wrds
def connect():
    for i in range(5):
        try: return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'  wrds retry {i}: {str(e)[:80]}'); time.sleep(5*(i+1))
    raise SystemExit('WRDS connection failed')
db = connect(); log('connected to WRDS')

msf = db.raw_sql(f"""SELECT permno, mthcaldt AS date, mthret AS ret, ticker
                     FROM crsp.msf_v2
                     WHERE permno IN {permnos}
                       AND mthcaldt BETWEEN '2018-12-01' AND '2025-12-31'""")
msf['date'] = pd.to_datetime(msf['date'])
msf['ret'] = pd.to_numeric(msf['ret'], errors='coerce')
msf['ym'] = msf['date'].dt.year*100 + msf['date'].dt.month
msf.to_csv(os.path.join(RAW, 'crsp_monthly.csv'), index=False)
log(f'crsp monthly rows: {len(msf)} for {msf.permno.nunique()} permnos')

ff = db.raw_sql("""SELECT date, mktrf, rf FROM ff.factors_monthly
                   WHERE date BETWEEN '2018-12-01' AND '2025-12-31'""")
ff['date'] = pd.to_datetime(ff['date'])
ff['mktret'] = pd.to_numeric(ff['mktrf'], errors='coerce') + pd.to_numeric(ff['rf'], errors='coerce')
ff['ym'] = ff['date'].dt.year*100 + ff['date'].dt.month
ff.to_csv(os.path.join(RAW, 'ff_monthly.csv'), index=False)
mkt_by_ym = ff.set_index('ym')['mktret']
log(f'ff monthly rows: {len(ff)}')
db.close()

# ticker as of the filing month, for anonymization later
tick = (msf.dropna(subset=['ticker']).sort_values('date')
           .groupby('permno')['ticker'].last())

def fwd(permno, fdate):
    g = msf[(msf.permno == permno) & (msf.date > fdate)].sort_values('date')
    g = g.dropna(subset=['ret'])
    out = {}
    for K in HORIZONS:
        gk = g.head(K)
        if len(gk) < K:
            out[f'firm_cum_{K}'] = np.nan; out[f'bhar_{K}'] = np.nan; continue
        firm_cum = float(np.prod(1.0 + gk['ret'].values) - 1.0)
        yms = gk['ym'].values
        mk = mkt_by_ym.reindex(yms).values
        if np.isnan(mk).any():
            mkt_cum = np.nan
        else:
            mkt_cum = float(np.prod(1.0 + mk) - 1.0)
        out[f'firm_cum_{K}'] = firm_cum
        out[f'bhar_{K}'] = firm_cum - mkt_cum if not np.isnan(mkt_cum) else np.nan
    return out

rows = []
for _, r in cand.iterrows():
    d = fwd(int(r.permno), r.filing_date)
    d.update(id=r.id, permno=int(r.permno), window=r.window,
             filing_date=r.filing_date, ticker=tick.get(int(r.permno), None))
    rows.append(d)
ret = pd.DataFrame(rows)
ret.to_csv(os.path.join(INT, 'returns.csv'), index=False)
log(f'returns computed: {len(ret)} | non-null bhar_12 = {ret.bhar_12.notna().sum()}')

# finalize: require a valid 12-month BHAR, trim per window
final_ids = []
for tag in ('pre','post'):
    sub = ret[(ret.window == tag) & ret.bhar_12.notna()]
    sub = sub.sample(n=min(FINAL_PER_WINDOW, len(sub)), random_state=SEED)
    final_ids.append(sub)
    log(f'  window {tag}: {sub.shape[0]} filings with valid 12m BHAR (of '
        f'{(ret.window==tag).sum()} candidates)')
finaldf = pd.concat(final_ids, ignore_index=True)['id']
sample = cand[cand.id.isin(finaldf)].merge(
    ret.drop(columns=['window','filing_date']), on='id', how='left')
sample = sample.sort_values(['window','filing_date']).reset_index(drop=True)
sample.to_csv(os.path.join(INT, 'sample_final.csv'), index=False)
log(f'FINAL sample: {len(sample)}  pre={ (sample.window=="pre").sum() } '
    f'post={ (sample.window=="post").sum() }')
log('bhar_12 by window:\n' +
    sample.groupby('window')['bhar_12'].agg(['count','mean','std']).round(4).to_string())
logf.close()
