#!/usr/bin/env python3
"""
Project 13 - Step 25: resolving-news event study (June 2026 FOMC).

The June-2026 meeting is the one matched meeting that has already RESOLVED and that
Kalshi still retains, so we can study convergence to the truth. The FOMC held rates
('no change'). For each venue we track the mean absolute pricing error across all five
outcome contracts, E(t) = mean_o |price_o(t) - 1{o realized}|, as the statement (t*)
approaches. The venue whose error falls sooner is discovering the resolution first.

Outputs output/tables/t7_eventstudy.csv and t8_convergence.csv.
"""
import os, glob, datetime as dt
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw')
OUT  = os.path.join(HERE, 'output', 'tables')
MEETING = '26JUN'
FOMC = dt.datetime(2026, 6, 17, 18)            # statement release (UTC)
REALIZED = {'no_change': 1, 'cut25': 0, 'cut50p': 0, 'hike25': 0, 'hike50p': 0}
STEP = 3600

def load(sub, oc, pcol):
    f = os.path.join(RAW, sub, f'{MEETING}_{oc}.csv')
    if not os.path.exists(f): return None
    d = pd.read_csv(f)[['ts', pcol]].dropna().sort_values('ts').drop_duplicates('ts')
    return d

def asof(d, grid, pcol):
    t = d['ts'].values; p = d[pcol].values
    idx = np.searchsorted(t, grid, side='right') - 1
    return np.where(idx >= 0, p[np.clip(idx, 0, len(p) - 1)], np.nan)

def main():
    t_star = int(FOMC.timestamp())
    grid = np.arange(t_star - 30 * 86400, t_star + 1, STEP)
    kerr = np.zeros((len(REALIZED), len(grid))); perr = np.zeros_like(kerr)
    knc = pnc = None
    for i, (oc, real) in enumerate(REALIZED.items()):
        k = load('kalshi', oc, 'price'); p = load('poly', oc, 'price')
        kp = asof(k, grid, 'price') if k is not None else np.full(len(grid), np.nan)
        pp = asof(p, grid, 'price') if p is not None else np.full(len(grid), np.nan)
        kerr[i] = np.abs(kp - real); perr[i] = np.abs(pp - real)
        if oc == 'no_change':
            knc, pnc = kp, pp
    kmae = np.nanmean(kerr, axis=0); pmae = np.nanmean(perr, axis=0)
    hrs = (grid - t_star) / 3600.0
    # snapshot windows before the statement
    snaps = [('T-7d', -168), ('T-3d', -72), ('T-24h', -24), ('T-12h', -12),
             ('T-6h', -6), ('T-3h', -3), ('T-1h', -1)]
    rows = []
    for name, h in snaps:
        j = int(np.argmin(np.abs(hrs - h)))
        rows.append(dict(window=name, hours_to_statement=h,
                         kalshi_mae=round(float(kmae[j]), 4), poly_mae=round(float(pmae[j]), 4),
                         poly_minus_kalshi=round(float(pmae[j] - kmae[j]), 4),
                         kalshi_nochange=round(float(knc[j]), 3), poly_nochange=round(float(pnc[j]), 3)))
    es = pd.DataFrame(rows); es.to_csv(os.path.join(OUT, 't7_eventstudy.csv'), index=False)
    # trailing-window accuracy (lower mean abs error = better price discovery)
    pre = hrs <= 0
    def win(mask):
        return mask & pre
    m7 = (hrs >= -168) & pre; m1 = (hrs >= -24) & pre
    j1 = int(np.argmin(np.abs(hrs + 1)))
    conv = pd.DataFrame([
        dict(venue='Kalshi', mae_last7d=round(float(np.nanmean(kmae[m7])), 4),
             mae_last24h=round(float(np.nanmean(kmae[m1])), 4),
             nochange_T1h=round(float(knc[j1]), 3)),
        dict(venue='Polymarket', mae_last7d=round(float(np.nanmean(pmae[m7])), 4),
             mae_last24h=round(float(np.nanmean(pmae[m1])), 4),
             nochange_T1h=round(float(pnc[j1]), 3)),
    ])
    conv.to_csv(os.path.join(OUT, 't8_convergence.csv'), index=False)
    # save the full path for the figure
    pd.DataFrame({'hours_to_statement': hrs, 'kalshi_mae': kmae, 'poly_mae': pmae,
                  'kalshi_nochange': knc, 'poly_nochange': pnc}).to_csv(
        os.path.join(OUT, 'eventpath_26jun.csv'), index=False)
    print('EVENT STUDY (26JUN):')
    print(es.to_string(index=False))
    print(conv.to_string(index=False))

if __name__ == '__main__':
    main()
