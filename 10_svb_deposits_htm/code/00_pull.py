#!/usr/bin/env python3
"""
Project 10 (SVB) — Step 00: pull raw data from WRDS.

Pulls, for publicly-traded US banks:
  (a) the bank-stock universe (SIC 6020-6079, 6712) around the SVB window,
  (b) the CRSP permco -> regulatory RSSD link (bank.wrds_bank_crsp_link),
  (c) 2022Q4 Call Report cells for the two identifying variables:
        uninsured deposits  = RCON5597   (Schedule RC-O)
        HTM unrealized loss = amortized cost RCON1754 - fair value RCON1771  (RC-B)
        AFS unrealized loss = amortized cost RCON1772 - fair value RCON1773  (RC-B)
        total assets RCON2170, total equity RCON3210
  (d) CRSP daily returns (2022-01 .. 2023-04) + the CRSP value-weighted index,
      for the market-model event study around the March 2023 run.

Everything is written raw & date-stamped to data/raw/. Nothing is fabricated;
every figure traces to a WRDS query logged below.
"""
import os
import datetime
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw')
LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True)
os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()

logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(msg):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {msg}'
    print(line); logf.write(line + '\n'); logf.flush()

db = wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
log('connected to WRDS')

# --- (a) bank stock universe (names table = fast) --------------------------
uni = db.raw_sql("""
SELECT DISTINCT permno, permco, ticker, comnam, siccd
FROM crsp.dsenames
WHERE nameendt >= '2023-01-01' AND namedt <= '2023-04-30'
  AND shrcd IN (10,11) AND exchcd IN (1,2,3)
  AND (siccd BETWEEN 6020 AND 6079 OR siccd = 6712)
""")
# one row per permno (latest name)
uni = uni.sort_values('permno').drop_duplicates('permno')
uni.to_csv(os.path.join(RAW, 'bank_universe.csv'), index=False)
log(f'(a) bank universe: {len(uni)} permnos, {uni.permco.nunique()} permcos')

permcos = tuple(int(x) for x in uni.permco.dropna().unique())

# --- (b) permco -> RSSD link ----------------------------------------------
link = db.raw_sql(f"""
SELECT rssd9001, permco, name, inst_type, dt_start, dt_end
FROM bank.wrds_bank_crsp_link
WHERE permco IN {permcos}
""")
link.to_csv(os.path.join(RAW, 'bank_crsp_link_all.csv'), index=False)
log(f'(b) link rows: {len(link)}; inst_type values: {link.inst_type.value_counts().to_dict()}')
log(f'    dt_start sample: {sorted(link.dt_start.dropna().unique())[:3]} ... dtype={link.dt_start.dtype}')

# keep link valid on the event date 2023-03-08 (dates are ints YYYYMMDD or similar)
def _asint(s):
    try: return int(str(s).replace('-', '')[:8])
    except Exception: return None
link['s'] = link.dt_start.map(_asint)
link['e'] = link.dt_end.map(_asint)
EVENT = 20230308
lk = link[(link.s.fillna(0) <= EVENT) & (link.e.fillna(99999999) >= EVENT)].copy()
lk = lk.sort_values('inst_type').drop_duplicates('permco')  # one rssd per permco
lk.to_csv(os.path.join(RAW, 'bank_crsp_link_active.csv'), index=False)
log(f'    active-on-event links: {len(lk)} permcos matched to an RSSD')

rssds = tuple(int(x) for x in lk.rssd9001.dropna().unique())

# --- (c) 2022Q4 Call Report cells -----------------------------------------
c1 = db.raw_sql(f"""
SELECT rssd9001, wrdsreportdate, rcon5597, rcon1754, rcon1773
FROM bank.wrds_call_rcon_1
WHERE wrdsreportdate = '2022-12-31' AND rssd9001 IN {rssds}
""")
c2 = db.raw_sql(f"""
SELECT rssd9001, wrdsreportdate, rcon1771, rcon1772, rcon2170, rcon3210
FROM bank.wrds_call_rcon_2
WHERE wrdsreportdate = '2022-12-31' AND rssd9001 IN {rssds}
""")
call = c1.merge(c2, on=['rssd9001', 'wrdsreportdate'], how='outer')
call.to_csv(os.path.join(RAW, 'call_2022q4.csv'), index=False)
log(f'(c) call report rows: {len(call)} (rcon5597 nonnull={call.rcon5597.notna().sum()}, '
    f'rcon2170 nonnull={call.rcon2170.notna().sum()})')

# --- (d) CRSP daily returns + market index --------------------------------
permnos = tuple(int(x) for x in uni.permno.unique())
dsf = db.raw_sql(f"""
SELECT permno, date, ret, prc, shrout, vol
FROM crsp.dsf
WHERE permno IN {permnos} AND date BETWEEN '2022-01-01' AND '2023-04-30'
""")
dsf.to_csv(os.path.join(RAW, 'crsp_daily.csv'), index=False)
log(f'(d) crsp daily rows: {len(dsf)} for {dsf.permno.nunique()} permnos')

mkt = db.raw_sql("""
SELECT date, vwretd, ewretd, sprtrn
FROM crsp.dsi
WHERE date BETWEEN '2022-01-01' AND '2023-04-30'
""")
mkt.to_csv(os.path.join(RAW, 'crsp_market.csv'), index=False)
log(f'(d) market index rows: {len(mkt)}')

db.close()
log('DONE — raw data written to data/raw/')
logf.close()
