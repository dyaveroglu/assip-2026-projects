#!/usr/bin/env python3
"""
Project 11 (CHIPS awards) -- Step 00: pull raw CRSP data from WRDS.

Inputs:
  data/raw/chips_awards_handcollected.csv  -- hand-collected CHIPS award
      first-announcement (Preliminary Memorandum of Terms) dates + amounts for
      publicly-traded awardees, compiled from Commerce/NIST press releases.

Pulls:
  (a) CRSP permno for each awardee ticker (crsp.stocknames),
  (b) CRSP daily returns (prc, shrout, ret, vol) for those permnos,
      2022-06-01 .. 2024-12-31 (covers the [-252,-46] estimation window of the
      earliest event and the event windows of the latest 2024 event),
  (c) the CRSP value-weighted market index (crsp.dsi) over the same span.

Everything is written raw + date-stamped to data/raw/. Nothing is fabricated;
returns are the actual CRSP daily record for each awardee.
"""
import os, datetime, warnings, time
warnings.filterwarnings('ignore')
import pandas as pd, wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

def connect(n=6):
    for i in range(n):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'WRDS connect retry {i}: {str(e)[:80]}'); time.sleep(5*(i+1))
    raise RuntimeError('cannot connect to WRDS')

awards = pd.read_csv(os.path.join(RAW, 'chips_awards_handcollected.csv'))
awards['announce_date'] = pd.to_datetime(awards['announce_date'])
awards = awards[awards.us_listed == 1].copy()
log(f'hand-collected US-listed awards: {len(awards)} (tickers: {sorted(awards.ticker)})')

db = connect(); log('connected to WRDS')

# --- (a) ticker -> permno (one permno per ticker, latest name row) ----------
tks = tuple(sorted(awards.ticker.unique()))
sn = db.raw_sql(f"""
SELECT permno, ticker, comnam, namedt, nameenddt, shrcd, exchcd, siccd
FROM crsp.stocknames
WHERE ticker IN {tks} AND nameenddt >= '2023-06-01'
""")
sn['nameenddt'] = pd.to_datetime(sn['nameenddt'])
sn = sn.sort_values('nameenddt').drop_duplicates('ticker', keep='last')
t2p = dict(zip(sn.ticker, sn.permno))
awards['permno'] = awards.ticker.map(t2p)
awards['shrcd'] = awards.ticker.map(dict(zip(sn.ticker, sn.shrcd)))
awards['siccd'] = awards.ticker.map(dict(zip(sn.ticker, sn.siccd)))
miss = awards[awards.permno.isna()]
if len(miss):
    log(f'WARNING unresolved tickers: {list(miss.ticker)}')
awards = awards.dropna(subset=['permno']).copy()
awards['permno'] = awards.permno.astype(int)
awards.to_csv(os.path.join(RAW, 'awards_with_permno.csv'), index=False)
log(f'(a) resolved {len(awards)} tickers to permnos; ADRs (shrcd 30-31): '
    f'{list(awards[awards.shrcd.between(30,31)].ticker)}')

permnos = tuple(int(x) for x in awards.permno.unique())

# --- (b) CRSP daily returns -----------------------------------------------
dsf = db.raw_sql(f"""
SELECT permno, date, ret, prc, shrout, vol
FROM crsp.dsf
WHERE permno IN {permnos} AND date BETWEEN '2022-06-01' AND '2024-12-31'
""")
dsf.to_csv(os.path.join(RAW, 'crsp_daily.csv'), index=False)
log(f'(b) crsp daily rows: {len(dsf)} for {dsf.permno.nunique()} permnos '
    f'(dates {dsf.date.min()}..{dsf.date.max()})')

# --- (c) market index ------------------------------------------------------
mkt = db.raw_sql("""
SELECT date, vwretd, ewretd, sprtrn
FROM crsp.dsi
WHERE date BETWEEN '2022-06-01' AND '2024-12-31'
""")
mkt.to_csv(os.path.join(RAW, 'crsp_market.csv'), index=False)
log(f'(c) market index rows: {len(mkt)} (dates {mkt.date.min()}..{mkt.date.max()})')

db.close(); log('DONE -- raw data written to data/raw/'); logf.close()
