#!/usr/bin/env python3
"""
Project 12 (Half-Cent Tick) - Step 10: build the analytical daily panel.

From the raw daily CLOSING NBBO we construct, per stock-day:
  dqs_c   dollar quoted spread in CENTS        = 100*(ask - bid)
  rqs_bps relative quoted spread in BASIS PTS  = 10000*(ask - bid)/midpoint
  espr_bps closing effective-spread PROXY (bps) = 10000*2*|close - mid|/mid
           (NOTE: a crude daily proxy; a true effective spread needs TAQ trades.
            Reported only as secondary/robustness, heavily caveated.)
  lprice  log midpoint ; ldvol log dollar volume ; lnumtrd log(#trades)

Treatment (tick-constrained) is fixed from the Sept screening window.
DiD analysis window = 4 weeks pre (Oct 6-31) and 4 weeks post (Nov 3-28) the
Nov 3 2025 compliance date. We also keep the full Sept-Dec panel for the
event-time figure and pre-trend tests.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
PROC = os.path.join(HERE, 'data', 'processed')
for d in (INT, PROC): os.makedirs(d, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'build_{STAMP}.log'), 'w')
def log(m):
    line=f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

EVENT = pd.Timestamp('2025-11-03')
PRE0, PRE1 = pd.Timestamp('2025-10-06'), pd.Timestamp('2025-10-31')
POST0, POST1 = pd.Timestamp('2025-11-03'), pd.Timestamp('2025-11-28')

sample = pd.read_csv(os.path.join(RAW, 'sample_stocks.csv'))[
    ['permno','ticker','treated','dqs','rqs','price','dvol','siccd']].rename(
    columns={'dqs':'scr_dqs','rqs':'scr_rqs','price':'scr_price','dvol':'scr_dvol'})

p = pd.read_csv(os.path.join(RAW, 'panel_daily.csv'))
p['date'] = pd.to_datetime(p['date'])
for c in ['bid','ask','close','shrvol','dvol','ret','numtrd']:
    p[c] = pd.to_numeric(p[c], errors='coerce')
n0 = len(p)

# --- valid closing quotes only --------------------------------------------
p['mid'] = (p.bid + p.ask)/2.0
p = p[(p.bid > 0) & (p.ask > p.bid) & (p.mid >= 1.0) & ((p.ask - p.bid) < p.mid)]
log(f'raw rows {n0} -> valid-quote rows {len(p)} ({n0-len(p)} dropped)')

p['dqs_c']   = 100.0 * (p.ask - p.bid)                       # dollar spread, cents
p['rqs_bps'] = 10000.0 * (p.ask - p.bid) / p.mid            # relative spread, bps
p['espr_bps']= 10000.0 * 2.0 * (p.close - p.mid).abs() / p.mid
p['lprice']  = np.log(p.mid)
p['ldvol']   = np.log(p.dvol.clip(lower=1))
p['lnumtrd'] = np.log(p.numtrd.clip(lower=1))

p = p.merge(sample[['permno','treated','siccd']], on='permno', how='inner')
p['post'] = (p.date >= EVENT).astype(int)
p['tp']   = p.treated * p.post

# winsorize the spread outcomes 1/99 (pooled) to tame quote glitches
for v in ['rqs_bps','espr_bps','dqs_c']:
    lo, hi = p[v].quantile(0.01), p[v].quantile(0.99)
    p[v+'_w'] = p[v].clip(lo, hi)

# event-time week index (0 = week containing the event)
p['evt_day']  = (p.date - EVENT).dt.days
p['evt_week'] = np.floor(p.evt_day/7.0).astype(int)

p = p.sort_values(['permno','date'])
p.to_csv(os.path.join(PROC, 'panel_full.csv'), index=False)
log(f'full panel: {len(p)} stock-days, {p.permno.nunique()} stocks, '
    f'{p.date.min().date()}..{p.date.max().date()}')

# --- DiD analysis window (4wk pre + 4wk post) ------------------------------
did = p[((p.date >= PRE0) & (p.date <= PRE1)) | ((p.date >= POST0) & (p.date <= POST1))].copy()
did.to_csv(os.path.join(PROC, 'panel_did.csv'), index=False)
log(f'DiD window rows: {len(did)} (pre {PRE0.date()}..{PRE1.date()}, post {POST0.date()}..{POST1.date()})')
log('  cell counts:\n' + did.groupby(['treated','post']).size().unstack().to_string())
log('  mean rqs_bps by cell:\n' +
    did.groupby(['treated','post'])['rqs_bps_w'].mean().unstack().round(3).to_string())
logf.close()
