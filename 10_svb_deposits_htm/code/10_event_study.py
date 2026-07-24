#!/usr/bin/env python3
"""
Project 10 (SVB) — Step 10: compute market-model CARs over the March-2023 window.

Event day 0 = 2023-03-08 (SVB announced its $21B AFS sale + capital raise after
the close). The run/collapse was 3/9-3/10; FDIC receivership 3/10; contagion 3/13.
Benchmark = CRSP value-weighted index. Estimation window [-252,-46].
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
logf = open(os.path.join(LOG, f'eventstudy_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

# returns
dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date'])
dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
dsf = dsf.dropna(subset=['ret'])
# market
mkt = pd.read_csv(os.path.join(RAW, 'crsp_market.csv'))
mkt['date'] = pd.to_datetime(mkt['date'])
mkt['mktret'] = pd.to_numeric(mkt['vwretd'], errors='coerce')
log(f'returns rows: {len(dsf)} for {dsf.permno.nunique()} permnos; market days: {len(mkt)}')

EVENT = pd.Timestamp('2023-03-08')
windows = {'car_0_1': (0, 1), 'car_0_3': (0, 3), 'car_0_5': (0, 5),
           'car_m1_3': (-1, 3), 'car_pre': (-6, -2)}  # car_pre = placebo
cars = market_model_cars(dsf, mkt, EVENT, est_window=(-252, -46),
                         event_windows=windows, min_obs=100)
cars.to_csv(os.path.join(INT, 'cars.csv'), index=False)
log(f'CARs computed for {len(cars)} banks')
for w in windows:
    log(f'  mean {w} = {cars[w].mean():+.4f}  (median {cars[w].median():+.4f}, '
        f'n={cars[w].notna().sum()})')
logf.close()
