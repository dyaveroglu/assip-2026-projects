#!/usr/bin/env python3
"""
Project 05 - Step 10: market-model CARs for the paired April-2025 tariff events.

Two opposite-signed events:
  SHOCK  day0 = 2025-04-03  (reciprocal tariffs announced ~16:00 ET Apr 2, after
                             the close; first full trading reaction is Apr 3-4,
                             the ~11% two-day 'Liberation Day' crash).
  PAUSE  day0 = 2025-04-09  (90-day pause announced ~13:18 ET Apr 9, intraday;
                             S&P +9.5%, the largest one-day gain since 2008).
Benchmark = Fama-French market return (mktrf+rf). Estimation window [-252,-46],
so both models are fit on a clean pre-shock period.
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

# ---- returns & market ------------------------------------------------------
dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date'])
dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
dsf = dsf.dropna(subset=['ret'])
mkt = pd.read_csv(os.path.join(RAW, 'market_ff.csv'))
mkt['date'] = pd.to_datetime(mkt['date'])
mkt['mktret'] = pd.to_numeric(mkt['mktret'], errors='coerce')
log(f'returns rows {len(dsf)} for {dsf.permno.nunique()} permnos; market days {len(mkt)}')

# ---- SHOCK (Apr 3) ---------------------------------------------------------
shock_w = {'car_s0': (0, 0), 'car_s01': (0, 1), 'car_s03': (0, 3),
           'car_pre': (-5, -1)}                      # pre-trend / placebo
cs = market_model_cars(dsf, mkt, pd.Timestamp('2025-04-03'),
                       est_window=(-252, -46), event_windows=shock_w, min_obs=100)
log(f'SHOCK CARs computed for {len(cs)} firms; mean car_s01={cs.car_s01.mean():.4f}')

# ---- PAUSE (Apr 9) ---------------------------------------------------------
pause_w = {'car_p0': (0, 0), 'car_p01': (0, 1), 'car_p03': (0, 3)}
cp = market_model_cars(dsf, mkt, pd.Timestamp('2025-04-09'),
                       est_window=(-252, -46), event_windows=pause_w, min_obs=100)
cp = cp.rename(columns={'alpha': 'alpha_p', 'beta': 'beta_p', 'n_est': 'n_est_p'})
log(f'PAUSE CARs computed for {len(cp)} firms; mean car_p0={cp.car_p0.mean():.4f}')

# ---- merge -----------------------------------------------------------------
cars = cs.merge(cp, on='permno', how='inner')
# round-trip: does the pause rebound offset the shock drop?
cars['car_round'] = cars['car_p0'] + cars['car_s01']
cars.to_csv(os.path.join(INT, 'cars.csv'), index=False)
log(f'merged CARs: {len(cars)} firms. '
    f'means: shock[0,1]={cars.car_s01.mean():.4f}, pause[0]={cars.car_p0.mean():.4f}, '
    f'round={cars.car_round.mean():.4f}, beta(med)={cars.beta.median():.2f}')
log('DONE - cars.csv written')
logf.close()
