#!/usr/bin/env python3
"""
Project 12 (Half-Cent Tick) - Step 00: pull the daily NBBO sample from WRDS CRSP.

DATA SOURCE DECISION (stated plainly, per the brief):
  WRDS TAQ (millisecond/second) intraday NBBO is NOT subscribed on this account:
  only the TAQ *sample* libraries (taqsamp/taqmsamp) are available, and they
  cover only a handful of 2008/2009/2021 sample days -- there is NO 2025 TAQ.
  We therefore use the brief's explicitly-sanctioned fallback: the CRSP daily
  stock file (crsp.dsf_v2, CIZ format), which records each security's CLOSING
  consolidated NBBO (dlybid, dlyask) and covers 2025 through 2025-12-31.
  The quoted spread proxy is  spread = ask - bid  (dollar) and
  relative spread = (ask - bid) / midpoint  (the standard Chung-Zhang-style
  daily liquidity proxy). We state throughout that this is a daily CLOSING-quote
  proxy, not a time-weighted intraday measure.

SAMPLE (small, ~150 names, per the brief):
  Universe  = NMS common stocks (sharetype NS, EQTY/COM, CORP/REIT),
              primary exchange NYSE/Nasdaq/NYSE American, price >= $1.
  Screening = Sept 2025 (2025-09-02 .. 2025-09-30), a window SEPARATED from the
              event so treatment assignment does not mechanically overlap the
              outcome window.
  Treated (tick-constrained) = Sept mean dollar quoted spread <= $0.015
              (the SEC's own Time-Weighted-Average-Quoted-Spread cutoff for the
              $0.005 increment). Control = Sept mean dollar spread >= $0.02
              (clearly not penny-pinned). We take the top-75 most-active names in
              each arm by dollar volume -> ~150 stocks.

  Panel     = daily obs for the selected names, 2025-08-25 .. 2025-12-19
              (baseline + screening + 4wk pre + 4wk post + tail).

Event: Nov 3 2025 = the SEC's stated first compliance date for the amended
Rule 612 minimum pricing increment ($0.005) and Rule 610 access-fee cap ($0.0010).
Exact per-tranche phase-in dates and per-stock eligibility are the STUDENT's
hand-verification task (see STUDENT_TASKS.md) -- we do not hand-verify them here.
"""
import os, datetime, warnings, time
warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
import wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

def connect():
    for a in range(5):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'WRDS connect retry {a}: {e}'); time.sleep(5*(a+1))
    raise RuntimeError('cannot connect to WRDS')

db = connect(); log('connected to WRDS')

EVENT = '2025-11-03'
SCR0, SCR1 = '2025-09-02', '2025-09-30'      # screening / treatment-assignment window
PANEL0, PANEL1 = '2025-08-25', '2025-12-19'  # full daily panel

# ---- (a) screening-window per-stock stats -> treatment assignment ---------
scr = db.raw_sql(f"""
SELECT permno, MAX(ticker) ticker, MAX(primaryexch) exch, MAX(siccd) siccd,
       AVG(dlyask-dlybid)                                   AS dqs,
       AVG((dlyask-dlybid)/((dlyask+dlybid)/2.0))           AS rqs,
       AVG((dlybid+dlyask)/2.0)                             AS price,
       AVG(dlyprcvol)                                       AS dvol,
       AVG(dlyvol)                                          AS shrvol,
       COUNT(*)                                             AS ndays
FROM crsp.dsf_v2
WHERE dlycaldt BETWEEN '{SCR0}' AND '{SCR1}'
  AND sharetype='NS' AND securitytype='EQTY' AND securitysubtype='COM'
  AND issuertype IN ('CORP','REIT')
  AND primaryexch IN ('N','Q','A')
  AND dlybid > 0 AND dlyask > dlybid AND (dlyask-dlybid) < (dlybid+dlyask)/2.0
GROUP BY permno
HAVING COUNT(*) >= 15 AND AVG((dlybid+dlyask)/2.0) >= 1.0
""")
log(f'(a) screening universe: {len(scr)} stocks (Sept 2025, liquid NMS common)')
scr.to_csv(os.path.join(RAW, 'screening_universe.csv'), index=False)

scr['treated'] = (scr.dqs <= 0.015).astype(int)
treated = scr[scr.dqs <= 0.015].sort_values('dvol', ascending=False).head(75).copy()
control = scr[scr.dqs >= 0.020].sort_values('dvol', ascending=False).head(75).copy()
sample = pd.concat([treated, control], ignore_index=True)
sample.to_csv(os.path.join(RAW, 'sample_stocks.csv'), index=False)
log(f'(a) SELECTED sample: {len(sample)} stocks '
    f'({sample.treated.sum()} treated tick-constrained, {(1-sample.treated).sum()} control)')
log('    treated  median dollar spread = %.4f, median price = %.2f, median $vol = %.2e'
    % (treated.dqs.median(), treated.price.median(), treated.dvol.median()))
log('    control  median dollar spread = %.4f, median price = %.2f, median $vol = %.2e'
    % (control.dqs.median(), control.price.median(), control.dvol.median()))

permnos = tuple(int(x) for x in sample.permno.unique())

# ---- (b) daily panel for the selected names -------------------------------
panel = db.raw_sql(f"""
SELECT permno, ticker, primaryexch AS exch, dlycaldt AS date,
       dlybid AS bid, dlyask AS ask, dlyclose AS close,
       dlyvol AS shrvol, dlyprcvol AS dvol, dlyret AS ret, dlynumtrd AS numtrd
FROM crsp.dsf_v2
WHERE permno IN {permnos}
  AND dlycaldt BETWEEN '{PANEL0}' AND '{PANEL1}'
ORDER BY permno, dlycaldt
""")
panel.to_csv(os.path.join(RAW, 'panel_daily.csv'), index=False)
log(f'(b) daily panel rows: {len(panel)} for {panel.permno.nunique()} permnos, '
    f'{panel.date.min()} .. {panel.date.max()}')

db.close()
log('DONE - raw data written to data/raw/')
logf.close()
