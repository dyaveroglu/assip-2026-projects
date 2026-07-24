#!/usr/bin/env python3
"""
Project 05 (Tariff / import exposure) - Step 00: pull raw data.

Pulls, for the April 2025 reciprocal-tariff event study:
  (a) the U.S. common-stock universe active in 2025 (crsp.stocknames_v2),
  (b) CRSP daily returns 2024-01 .. 2025-05 (crsp.dsf_v2) for the market-model
      estimation window + the April 2025 event windows,
  (c) the daily market return from Fama-French (ff.factors_daily; mkt = mktrf+rf),
      because crsp.dsi has no 2025 rows,
  (d) Compustat FY2023/2024 fundamentals (naicsh, sich, at, sale, cogs, ...)
      for the import-exposure controls + the NAICS industry key,
  (e) the CCM gvkey<->permno link,
  (f) the BEA 1997-2023 Summary Import Matrix + BEA Gross Output by industry
      (public bea.gov files) used to build industry imported-input intensity.

Everything is written raw & date-stamped to data/raw/. Nothing is fabricated;
every number traces to a query/file logged below.
"""
import os, sys, time, datetime, warnings
warnings.filterwarnings('ignore')
import pandas as pd
from urllib.request import urlopen, Request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

# ---------------------------------------------------------------- WRDS connect
import wrds
def connect(n=6):
    for i in range(n):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'WRDS connect retry {i}: {str(e)[:80]}'); time.sleep(5*(i+1))
    raise RuntimeError('cannot connect to WRDS')
db = connect()
log('connected to WRDS')

# ---- (a) universe: US common stock active in 2025 -------------------------
uni = db.raw_sql("""
SELECT permno, permco, ticker, issuernm AS comnam, siccd, primaryexch,
       sharetype, securitytype, securitysubtype, issuertype, usincflg
FROM crsp.stocknames_v2
WHERE securityenddt >= '2025-01-01' AND securitybegdt <= '2025-04-30'
  AND sharetype='NS' AND securitytype='EQTY'
  AND securitysubtype='COM' AND primaryexch IN ('N','A','Q')
""")
uni = uni.sort_values(['permno']).drop_duplicates('permno')
uni.to_csv(os.path.join(RAW, 'universe.csv'), index=False)
log(f'(a) universe: {len(uni)} permnos ({uni.permco.nunique()} permcos); '
    f'issuertype={uni.issuertype.value_counts().to_dict()}')

permnos = tuple(int(x) for x in uni.permno.unique())

# ---- (b) CRSP daily returns 2024-01 .. 2025-05 ----------------------------
# chunk permnos to keep the IN() list sane
def pull_ret(pns):
    q = f"""
    SELECT permno, dlycaldt AS date, dlyret AS ret, dlyprc AS prc,
           shrout, dlyvol AS vol, dlycap AS mktcap
    FROM crsp.dsf_v2
    WHERE dlycaldt BETWEEN '2024-01-01' AND '2025-05-01'
      AND permno IN {pns}
    """
    return db.raw_sql(q)
chunks = [permnos[i:i+1500] for i in range(0, len(permnos), 1500)]
parts = []
for k, ch in enumerate(chunks):
    for attempt in range(4):
        try:
            parts.append(pull_ret(ch)); break
        except Exception as e:
            log(f'  ret chunk {k} retry {attempt}: {str(e)[:80]}'); time.sleep(8)
    log(f'  ret chunk {k+1}/{len(chunks)} done, rows so far {sum(len(p) for p in parts)}')
dsf = pd.concat(parts, ignore_index=True)
dsf.to_csv(os.path.join(RAW, 'crsp_daily.csv'), index=False)
log(f'(b) crsp daily rows: {len(dsf)} for {dsf.permno.nunique()} permnos '
    f'({dsf.date.min()}..{dsf.date.max()})')

# ---- (c) market return (Fama-French daily) --------------------------------
mkt = db.raw_sql("""
SELECT date, mktrf, rf, smb, hml, umd
FROM ff.factors_daily
WHERE date BETWEEN '2024-01-01' AND '2025-05-01'
""")
mkt['mktret'] = mkt['mktrf'] + mkt['rf']
mkt.to_csv(os.path.join(RAW, 'market_ff.csv'), index=False)
log(f'(c) market (FF) rows: {len(mkt)}; Apr-2025 mktret: ' +
    str(mkt[(mkt.date>='2025-04-02')&(mkt.date<='2025-04-10')][['date','mktret']].to_dict('records')))

# ---- (d) Compustat fundamentals (FY2023/2024) -----------------------------
comp = db.raw_sql("""
SELECT gvkey, datadate, fyear, tic, conm, cik, naicsh, sich,
       at, sale, revt, cogs, xsga, ceq, csho, prcc_f, dltt, dlc, che, ppent, ni, oibdp
FROM comp.funda
WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
  AND fyear IN (2023, 2024) AND datadate <= '2025-03-31'
""")
comp.to_csv(os.path.join(RAW, 'compustat_funda.csv'), index=False)
log(f'(d) compustat funda rows: {len(comp)} ({comp.gvkey.nunique()} gvkeys); '
    f'naicsh nonnull={comp.naicsh.notna().sum()}, cogs nonnull={comp.cogs.notna().sum()}')

# ---- (e) CCM link ---------------------------------------------------------
lnk = db.raw_sql("""
SELECT gvkey, lpermno AS permno, linkdt, linkenddt, linktype, linkprim
FROM crsp.ccmxpf_lnkhist
WHERE linktype IN ('LC','LU','LS') AND linkprim IN ('P','C')
""")
lnk.to_csv(os.path.join(RAW, 'ccm_link.csv'), index=False)
log(f'(e) ccm link rows: {len(lnk)}')
db.close()

# ---- (f) BEA public files: Summary Import Matrix + Gross Output ------------
BEA = {
 'bea_import_matrix.xlsx':
   'https://apps.bea.gov/industry/xls/io-annual/ImportMatrices_Before_Redefinitions_SUM_1997-2023.xlsx',
 'bea_gross_output.xlsx':
   'https://apps.bea.gov/industry/Release/XLS/GDPxInd/GrossOutput.xlsx',
}
for fname, url in BEA.items():
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (research)'})
        data = urlopen(req, timeout=60).read()
        open(os.path.join(RAW, fname), 'wb').write(data)
        log(f'(f) downloaded {fname}: {len(data)} bytes')
    except Exception as e:
        log(f'(f) FAILED {fname}: {str(e)[:120]}')

log('DONE - raw data written to data/raw/')
logf.close()
