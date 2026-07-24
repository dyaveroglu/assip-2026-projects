#!/usr/bin/env python3
"""
Project 11 (CHIPS awards) -- Step 10: market-model CARs around each award's
FIRST-announcement (Preliminary Memorandum of Terms) date.

Unlike a single-event study (SVB), every awardee has its OWN event date, so we
call the shared market_model_cars() once per event on that firm's returns.

Day 0 = first trading day on/after the announcement date. Benchmark = CRSP
value-weighted index. Estimation window [-252,-46]. Events whose windows fall
past the CRSP daily cutoff (2024-12-31) are skipped and logged (ADI, MTSI,
announced Jan-2025, await the next CRSP annual update).

Also attaches, for the cross-section: pre-announcement market cap (last CRSP
prc*shrout strictly before day 0), so award size can be scaled by firm size.
"""
import os, sys, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from event_study import market_model_cars

RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs'); os.makedirs(INT, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'eventstudy_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

# --- returns + market ------------------------------------------------------
dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date'])
dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
dsf['prc'] = pd.to_numeric(dsf['prc'], errors='coerce').abs()   # prc<0 = bid/ask avg
dsf['shrout'] = pd.to_numeric(dsf['shrout'], errors='coerce')
dsf = dsf.dropna(subset=['ret'])

mkt = pd.read_csv(os.path.join(RAW, 'crsp_market.csv'))
mkt['date'] = pd.to_datetime(mkt['date'])
mkt['mktret'] = pd.to_numeric(mkt['vwretd'], errors='coerce')
cal_max = mkt.date.max()

awards = pd.read_csv(os.path.join(RAW, 'awards_with_permno.csv'))
awards['announce_date'] = pd.to_datetime(awards['announce_date'])
log(f'returns rows: {len(dsf)} for {dsf.permno.nunique()} permnos; '
    f'market days: {len(mkt)} (max {cal_max.date()}); events: {len(awards)}')

windows = {'car_m1_1': (-1, 1), 'car_0_1': (0, 1), 'car_0_3': (0, 3),
           'car_m1_5': (-1, 5), 'car_m5_5': (-5, 5), 'car_pre': (-10, -3)}

rows = []
for _, a in awards.iterrows():
    ev = a['announce_date']
    sub = dsf[dsf.permno == a['permno']].copy()
    if ev > cal_max or sub.empty:
        log(f'  SKIP {a.ticker}: event {ev.date()} past CRSP cutoff or no returns')
        continue
    try:
        c = market_model_cars(sub, mkt, ev, est_window=(-252, -46),
                              event_windows=windows, min_obs=100)
    except ValueError as e:
        log(f'  SKIP {a.ticker}: {e}'); continue
    if c.empty:
        log(f'  SKIP {a.ticker}: insufficient estimation obs'); continue
    r = c.iloc[0].to_dict()
    # pre-announcement market cap ($M): last prc*shrout strictly before day 0
    pre = sub[sub.date < ev].sort_values('date')
    mcap = np.nan
    if len(pre):
        last = pre.iloc[-1]
        if pd.notna(last.prc) and pd.notna(last.shrout) and last.shrout > 0:
            mcap = last.prc * last.shrout * 1e3 / 1e6   # shrout in 000s -> $M
    r.update(dict(ticker=a.ticker, company=a.company, announce_date=ev,
                  award_usd_m=a.award_usd_m, award_type=a.award_type,
                  adr=int(a.adr), shrcd=a.shrcd, mktcap_m=mcap))
    rows.append(r)
    log(f'  {a.ticker:5s} day0={ev.date()} beta={r["beta"]:.2f} n_est={r["n_est"]:.0f} '
        f'CAR[-1,+1]={r["car_m1_1"]:+.4f} CAR[0,+3]={r["car_0_3"]:+.4f} mcap=${mcap:,.0f}M')

cars = pd.DataFrame(rows)
cars['award_pct_mktcap'] = cars.award_usd_m / cars.mktcap_m * 100.0
cars['ln_award'] = np.log(cars.award_usd_m)
cars['ln_mktcap'] = np.log(cars.mktcap_m)
cars.to_csv(os.path.join(INT, 'cars.csv'), index=False)
log(f'\nCARs computed for {len(cars)} events')
for w in windows:
    s = cars[w].dropna()
    t = s.mean()/(s.std()/np.sqrt(len(s))) if len(s) > 1 else np.nan
    log(f'  mean {w:9s} = {s.mean():+.4f}  median {s.median():+.4f}  t={t:+.2f}  n={len(s)}')
log('award/mktcap (%) summary:\n' + cars[['ticker','award_usd_m','mktcap_m','award_pct_mktcap']]
    .sort_values('award_pct_mktcap', ascending=False).to_string(index=False))
logf.close()
