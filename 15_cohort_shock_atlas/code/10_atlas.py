#!/usr/bin/env python3
"""
Project 15 (Cohort capstone) — Step 10: build the policy-shock event-study atlas.

For each dated 2022-2025 shock, apply the shared market-model CAR module across the
~2,000-firm sample and summarize:
  - announcement reaction  mean CAR[0,+1] and its cross-sectional SD (differentiation)
  - anticipation           mean CAR[-5,-1] (pre-window leakage)
  - drift                  mean CAR[+2,+10]
  - reversal               cross-firm corr(CAR[0,+1], CAR[+2,+10])   (<0 = over-reaction)
Then three meta-tests across shocks: anticipation share, completeness by +1, reversal.
"""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from event_study import market_model_cars
OUT = os.path.join(HERE, 'output', 'tables'); os.makedirs(OUT, exist_ok=True)
def log(m): print(m, flush=True)

dsf = pd.read_csv(os.path.join(HERE, 'data', 'raw', 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date']); dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
mkt = pd.read_csv(os.path.join(HERE, 'data', 'raw', 'ff_market.csv'))
mkt['date'] = pd.to_datetime(mkt['date']); mkt['mktret'] = pd.to_numeric(mkt['mktret'], errors='coerce')

# (date, name, type, student-owner)
EVENTS = [
    ('2022-08-09','CHIPS Act signed','Industrial policy','A. Tang (#11)'),
    ('2022-08-16','IRA / buyback excise tax','Tax','cohort'),
    ('2022-11-30','ChatGPT release','Technology','N. Ngo (#09)'),
    ('2023-03-09','SVB collapse','Banking','A. Zhang (#10)'),
    ('2023-03-14','GPT-4 release','Technology','N. Ngo (#09)'),
    ('2024-02-05','SEC 5-day 13D rule','Disclosure','cohort'),
    ('2025-04-03','Reciprocal tariff shock','Trade','D. Yaveroglu (#05)'),
    ('2025-04-09','Tariff pause','Trade (reversal)','D. Yaveroglu (#05)'),
    ('2025-07-18','GENIUS Act signed','Crypto/regulatory','D. Jo\'rabekova (#13)'),
    ('2025-11-03','Reg NMS half-cent tick','Microstructure','K. Borra (#12)'),
]
WIN = {'pre':(-5,-1), 'ann':(0,1), 'wk':(0,5), 'drift':(2,10)}

rows = []
for date, name, typ, owner in EVENTS:
    ev = pd.Timestamp(date)
    cars = market_model_cars(dsf, mkt, ev, est_window=(-252,-46), event_windows=WIN, min_obs=120)
    # raw market cumulative move over [0,+1]
    cal = mkt.sort_values('date').reset_index(drop=True)
    i0 = cal.date.searchsorted(ev)
    mkt_ann = cal.mktret.iloc[i0:i0+2].sum() if i0+2 <= len(cal) else np.nan
    rev = cars[['ann','drift']].dropna().corr().iloc[0,1] if len(cars) > 30 else np.nan
    rows.append({'date':date,'event':name,'type':typ,'owner':owner,'n':len(cars),
                 'mkt_ann_pct':100*mkt_ann,
                 'mean_ann':100*cars.ann.mean(),'sd_ann':100*cars.ann.std(),
                 'mean_pre':100*cars.pre.mean(),'mean_drift':100*cars.drift.mean(),
                 'reversal_corr':rev})
atlas = pd.DataFrame(rows)
atlas.to_csv(os.path.join(OUT, 't1_atlas.csv'), index=False)
log('T1 ATLAS (%):\n'+atlas.round(3).to_string(index=False))

# ---- meta-tests across shocks ----
a = atlas.copy()
a['antic_share'] = a.mean_pre.abs() / (a.mean_pre.abs() + a.mean_ann.abs())
a['complete_by1'] = a.mean_ann.abs() / (a.mean_ann.abs() + a.mean_drift.abs())
meta = pd.DataFrame([
    {'metric':'Mean |announcement CAR[0,+1]| (%)','value':a.mean_ann.abs().mean()},
    {'metric':'Mean cross-sectional SD of CAR[0,+1] (%)','value':a.sd_ann.mean()},
    {'metric':'Mean anticipation share |pre|/(|pre|+|ann|)','value':a.antic_share.mean()},
    {'metric':'Mean completeness |ann|/(|ann|+|drift|)','value':a.complete_by1.mean()},
    {'metric':'Mean reversal corr(ann,drift)','value':a.reversal_corr.mean()},
    {'metric':'Share of shocks with negative reversal corr','value':(a.reversal_corr<0).mean()},
    {'metric':'Corr(|market move|, cross-sectional SD)','value':a.mkt_ann_pct.abs().corr(a.sd_ann)},
])
meta.to_csv(os.path.join(OUT, 't2_meta.csv'), index=False)
log('\nT2 META-TESTS:\n'+meta.round(3).to_string(index=False))
a.to_csv(os.path.join(OUT, 't1_atlas_full.csv'), index=False)
log('DONE')
