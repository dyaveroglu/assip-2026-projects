#!/usr/bin/env python3
"""
Project 09 (ChatGPT) — Step 05: pull CRSP daily returns + firm identifiers +
Compustat controls from WRDS for the two AI-release event studies.

Events (day 0 = first trading day on/after the release):
  * ChatGPT public release   : 2022-11-30 (Wed)   -- PRIMARY (clean-ish)
  * GPT-4 release            : 2023-03-14 (Tue)   -- SECONDARY (SVB-contaminated)

Universe: CRSP common shares (shrcd 10,11) on NYSE/AMEX/Nasdaq (exchcd 1,2,3)
with a valid NAICS, whose name record spans the ChatGPT window. We keep the name
record covering 2022-11-30 (else the latest), and map each firm to its 4-digit
NAICS to merge Felten-Raj-Seamans AIIE industry AI-exposure (step 00).

Returns window 2021-10-01 .. 2023-04-30 covers the [-252,-46] estimation window
for BOTH events plus event windows through GPT-4.

Controls (predetermined, measured before ChatGPT):
  * ln(ME)  : ln market cap at 2022-10-31 (|prc|*shrout, $000)   -- from CRSP
  * mom      : cumulative return 2022-05 .. 2022-10 (6-mo momentum) -- from CRSP
  * B/M      : Compustat ceq(FY2021) / ME(2022-10)                -- from Compustat
  * ln(emp)  : Compustat employees (FY2021)                        -- from Compustat

Everything raw & date-stamped to data/raw/. No fabrication.
"""
import os, datetime, time, warnings
warnings.filterwarnings('ignore')
import pandas as pd, numpy as np, wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_crsp_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

def connect(n=6):
    for i in range(n):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'wrds connect retry {i}: {e}'); time.sleep(5 * (i + 1))
    raise RuntimeError('cannot connect to WRDS')

db = connect(); log('connected to WRDS')

# ------------------------------------------------------------- (a) universe ---
uni = db.raw_sql("""
SELECT permno, permco, namedt, nameendt, shrcd, exchcd, siccd, naics, ticker, comnam
FROM crsp.dsenames
WHERE shrcd IN (10,11) AND exchcd IN (1,2,3)
  AND nameendt >= '2022-11-01' AND namedt <= '2023-03-31'
  AND naics IS NOT NULL AND naics <> ''
""")
uni['namedt'] = pd.to_datetime(uni['namedt']); uni['nameendt'] = pd.to_datetime(uni['nameendt'])
EV = pd.Timestamp('2022-11-30')
uni['covers'] = (uni.namedt <= EV) & (uni.nameendt >= EV)
uni = uni.sort_values(['permno', 'covers', 'nameendt'])  # covers=True and latest last
uni = uni.drop_duplicates('permno', keep='last')
uni['naics'] = uni['naics'].astype(str).str.strip()
uni['naics4'] = pd.to_numeric(uni['naics'].str[:4], errors='coerce')
uni = uni.dropna(subset=['naics4']); uni['naics4'] = uni['naics4'].astype(int)
uni.to_csv(os.path.join(RAW, 'crsp_universe.csv'), index=False)
log(f'(a) universe: {len(uni)} permnos, {uni.naics4.nunique()} distinct 4-digit NAICS')

# --------------------------------------------------------- (b) daily returns ---
dsf = db.raw_sql("""
SELECT d.permno, d.date, d.ret, d.prc, d.shrout, d.vol
FROM crsp.dsf d
WHERE d.date BETWEEN '2021-10-01' AND '2023-04-30'
  AND d.permno IN (
    SELECT DISTINCT permno FROM crsp.dsenames
    WHERE shrcd IN (10,11) AND exchcd IN (1,2,3)
      AND nameendt >= '2022-11-01' AND namedt <= '2023-03-31'
      AND naics IS NOT NULL AND naics <> '')
""")
dsf.to_csv(os.path.join(RAW, 'crsp_daily.csv'), index=False)
log(f'(b) crsp daily rows: {len(dsf)} for {dsf.permno.nunique()} permnos')

# --------------------------------------------------------------- (c) market ---
mkt = db.raw_sql("""SELECT date, vwretd, ewretd, sprtrn
                    FROM crsp.dsi WHERE date BETWEEN '2021-10-01' AND '2023-04-30'""")
mkt.to_csv(os.path.join(RAW, 'crsp_market.csv'), index=False)
log(f'(c) market index rows: {len(mkt)}')

# --------------------------------------------- (d) Compustat controls + CIK ----
# CRSP<->Compustat link, valid on the ChatGPT event date
link = db.raw_sql("""
SELECT gvkey, lpermno AS permno, linktype, linkprim, linkdt, linkenddt
FROM crsp.ccmxpf_lnkhist
WHERE linktype IN ('LC','LU','LS') AND linkprim IN ('P','C')
""")
link['linkdt'] = pd.to_datetime(link['linkdt'])
link['linkenddt'] = pd.to_datetime(link['linkenddt'].replace('E', pd.NaT)).fillna(pd.Timestamp('2100-01-01'))
link = link[(link.linkdt <= EV) & (link.linkenddt >= EV)]
link = link.sort_values('linkprim').drop_duplicates('permno')  # prefer P
link[['gvkey', 'permno']].to_csv(os.path.join(RAW, 'ccm_link.csv'), index=False)
log(f'(d) ccm links valid on event: {len(link)} permnos')

gvkeys = tuple(sorted(set(link.gvkey)))
funda = db.raw_sql(f"""
SELECT gvkey, datadate, fyear, at, ceq, emp, sale, cik
FROM comp.funda
WHERE fyear IN (2020,2021) AND indfmt='INDL' AND datafmt='STD'
  AND popsrc='D' AND consol='C' AND gvkey IN {gvkeys}
""")
funda['datadate'] = pd.to_datetime(funda['datadate'])
funda = funda.sort_values(['gvkey', 'datadate']).drop_duplicates('gvkey', keep='last')  # latest <=FY2021
funda.to_csv(os.path.join(RAW, 'compustat_funda.csv'), index=False)
log(f'(d) compustat funda rows (latest FY2020-21 per gvkey): {len(funda)} '
    f'(nonnull ceq={funda.ceq.notna().sum()}, emp={funda.emp.notna().sum()}, cik={funda.cik.notna().sum()})')

db.close(); log('DONE 05_pull_crsp — raw data written to data/raw/')
logf.close()
