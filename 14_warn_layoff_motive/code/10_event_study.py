#!/usr/bin/env python3
"""
Project 14 (WARN) - Step 10: market-model CARs around each WARN notice date.

For every firm-event (permno, event_date) we estimate a market model
    R_it = alpha_i + beta_i * R_mt + e_it
over the [-252,-46] trading-day window against the CRSP value-weighted index,
and cumulate abnormal returns over several event windows. Day 0 is the first
trading day on/after the WARN notice date. We also build the average abnormal
return PATH in event time [-10,+10] for the figure.

Uses the shared lib/event_study.py (market_model_cars). Events are grouped by
calendar date so each unique notice date calls the estimator once. Nothing is
fabricated; row counts logged.
"""
import os, sys, time, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from event_study import market_model_cars
import wrds

RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs')
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'eventstudy_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

def wrds_connect(n=5):
    for i in range(n):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'WRDS retry {i}: {e}'); time.sleep(5*(i+1))
    raise RuntimeError('WRDS connect failed')

ev = pd.read_csv(os.path.join(INT, 'warn_events.csv'), parse_dates=['event_date'])
permnos = tuple(int(p) for p in sorted(ev.permno.unique()))
log(f'events {len(ev)}; permnos {len(permnos)}')

# ---- CRSP daily returns + market index (cached) -----------------------
dsf_p = os.path.join(RAW, 'crsp_daily.csv'); mkt_p = os.path.join(RAW, 'crsp_market.csv')
if os.path.exists(dsf_p) and os.path.exists(mkt_p):
    dsf = pd.read_csv(dsf_p); mkt = pd.read_csv(mkt_p); log('loaded cached CRSP returns')
else:
    db = wrds_connect(); log('connected to WRDS (dsf)')
    dsf = db.raw_sql(f"""SELECT permno, date, ret, prc, vol, shrout FROM crsp.dsf
      WHERE permno IN {permnos} AND date BETWEEN '2021-01-01' AND '2026-06-30'""")
    dsf.to_csv(dsf_p, index=False)
    mkt = db.raw_sql("""SELECT date, vwretd, sprtrn FROM crsp.dsi
      WHERE date BETWEEN '2021-01-01' AND '2026-06-30'""")
    mkt.to_csv(mkt_p, index=False); db.close()
dsf['date'] = pd.to_datetime(dsf['date']); dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
dsf = dsf.dropna(subset=['ret'])
mkt['date'] = pd.to_datetime(mkt['date']); mkt['mktret'] = pd.to_numeric(mkt['vwretd'], errors='coerce')
mkt = mkt.dropna(subset=['mktret']).sort_values('date').reset_index(drop=True)
log(f'CRSP returns rows {len(dsf)} for {dsf.permno.nunique()} permnos; '
    f'market days {len(mkt)} ({mkt.date.min().date()}..{mkt.date.max().date()})')

WINDOWS = {'car_m1_1': (-1, 1), 'car_0_1': (0, 1), 'car_0_2': (0, 2),
           'car_0_5': (0, 5), 'car_m1_5': (-1, 5), 'car_pre': (-10, -2)}

# ---- CARs: one estimator call per unique event date -------------------
out = []
for d, g in ev.groupby('event_date'):
    pns = [int(p) for p in g.permno.unique()]
    sub = dsf[dsf.permno.isin(pns)]
    if sub.empty:
        continue
    try:
        c = market_model_cars(sub, mkt, pd.Timestamp(d), est_window=(-252, -46),
                              event_windows=WINDOWS, min_obs=60)
    except Exception as e:
        log(f'  skip {d.date()}: {e}'); continue
    c['event_date'] = pd.Timestamp(d)
    out.append(c)
cars = pd.concat(out, ignore_index=True)
cars.to_csv(os.path.join(INT, 'cars.csv'), index=False)
log(f'CARs computed for {len(cars)} firm-events (of {len(ev)})')
for w in WINDOWS:
    s = cars[w].dropna()
    t = s.mean() / (s.std() / np.sqrt(len(s))) if len(s) else float('nan')
    log(f'  mean {w} = {s.mean():+.4f}  median {s.median():+.4f}  t={t:+.2f}  n={len(s)}')

# ---- average AR path in event time [-10,+10] --------------------------
import bisect
cal = list(mkt['date']); cal_pos = {dd: i for i, dd in enumerate(cal)}
mret = mkt.set_index('date')['mktret']
ab = cars.set_index(['permno', 'event_date'])[['alpha', 'beta']].to_dict('index')
acc = {k: [0.0, 0] for k in range(-10, 11)}
for _, e in ev.iterrows():
    key = (int(e.permno), pd.Timestamp(e.event_date))
    if key not in ab:
        continue
    a = ab[key]['alpha']; b = ab[key]['beta']
    pos = bisect.bisect_left(cal, pd.Timestamp(e.event_date))
    if pos >= len(cal):
        continue
    g = dsf[dsf.permno == e.permno]
    g = g[g.date.isin(cal_pos)]
    rel = g.date.map(cal_pos) - pos
    win = g[(rel >= -10) & (rel <= 10)]
    for _, rr in win.iterrows():
        k = cal_pos[rr.date] - pos
        ar = rr.ret - (a + b * float(mret.loc[rr.date]))
        acc[k][0] += ar; acc[k][1] += 1
path = pd.DataFrame([{'rel_day': k, 'mean_ar': v[0]/v[1] if v[1] else np.nan, 'n': v[1]}
                     for k, v in sorted(acc.items())])
path['cum_ar'] = path['mean_ar'].cumsum()
path.to_csv(os.path.join(INT, 'ar_path.csv'), index=False)
log('AR path (event time) written; CAR[-10..+10] endpoint = %.4f' % path['cum_ar'].iloc[-1])
log('DONE - CARs -> data/interim/cars.csv, AR path -> data/interim/ar_path.csv')
logf.close()
