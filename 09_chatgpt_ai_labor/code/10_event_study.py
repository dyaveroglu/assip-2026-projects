#!/usr/bin/env python3
"""
Project 09 (ChatGPT) — Step 10: market-model CARs around the two AI releases.

Uses the shared event-study module lib/event_study.py. For each firm we estimate
R_it = alpha_i + beta_i*R_mt + e_it over [-252,-46] against the CRSP value-weighted
index, then cumulate abnormal returns over event windows.

Two events (day 0 = first trading day on/after the release):
  * ChatGPT : 2022-11-30  -> columns suffixed _cg
  * GPT-4   : 2023-03-14  -> columns suffixed _g4

Windows: [0,+1], [0,+5], [0,+10], [-1,+1]; placebo [-10,-2] (pre-event).
Diffuse-adoption note: ChatGPT went viral over the days AFTER release (1M users
in 5 days), so the [0,+5]/[0,+10] windows are the economically relevant ones.
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
    print(line); logf.write(line + '\n'); logf.flush()

dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date'])
dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
dsf = dsf.dropna(subset=['ret'])
mkt = pd.read_csv(os.path.join(RAW, 'crsp_market.csv'))
mkt['date'] = pd.to_datetime(mkt['date'])
mkt['mktret'] = pd.to_numeric(mkt['vwretd'], errors='coerce')
log(f'returns rows: {len(dsf)} for {dsf.permno.nunique()} permnos; market days: {len(mkt)}')

WINDOWS = {'car_0_1': (0, 1), 'car_0_5': (0, 5), 'car_0_10': (0, 10),
           'car_m1_1': (-1, 1), 'car_pre': (-10, -2)}
EVENTS = {'cg': pd.Timestamp('2022-11-30'), 'g4': pd.Timestamp('2023-03-14')}

merged = None
for tag, ev in EVENTS.items():
    cars = market_model_cars(dsf, mkt, ev, est_window=(-252, -46),
                             event_windows=WINDOWS, min_obs=100)
    cars = cars.rename(columns={w: f'{w}_{tag}' for w in WINDOWS} |
                              {'alpha': f'alpha_{tag}', 'beta': f'beta_{tag}', 'n_est': f'n_est_{tag}'})
    log(f'[{tag}] event {ev.date()} — CARs for {len(cars)} firms')
    for w in WINDOWS:
        s = cars[f'{w}_{tag}']
        log(f'    mean {w}_{tag} = {s.mean():+.4f} (median {s.median():+.4f}, n={s.notna().sum()})')
    merged = cars if merged is None else merged.merge(cars, on='permno', how='outer')

merged.to_csv(os.path.join(INT, 'cars.csv'), index=False)
log(f'wrote cars.csv: {len(merged)} firms, {merged.shape[1]} cols')
logf.close()
print('DONE 10_event_study')
