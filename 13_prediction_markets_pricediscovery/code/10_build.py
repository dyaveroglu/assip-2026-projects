#!/usr/bin/env python3
"""
Project 13 - Step 10: build the aligned matched-pair panel.

For every (meeting, outcome) where BOTH venues have data, align the two YES-probability
series onto a common hourly grid (as-of / last-observation-carried-forward), restrict to
the overlapping window, and stack into one long panel. Also select the pairs that are
usable for cointegration / price-discovery analysis (enough overlapping hours AND real
price variation - a contract frozen at 0 carries no information to share).

Outputs:
  data/processed/matched_panel.csv   long: pair, meeting, outcome, ts, kalshi_p, poly_p
  data/processed/pairs_selected.csv  one row per pair with coverage + selection flag
  logs/10_build.log
"""
import os, glob, datetime as dt
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw')
PROC = os.path.join(HERE, 'data', 'processed')
LOG  = os.path.join(HERE, 'logs', '10_build.log')
os.makedirs(PROC, exist_ok=True)

MIN_OBS = 150      # minimum overlapping hourly observations
MIN_SD  = 0.02     # minimum SD of the (more variable) venue's price level
STEP    = 3600     # 1-hour grid

def log(m):
    print(m)
    open(LOG, 'a').write(m + '\n')

def load(path, pcol='price'):
    df = pd.read_csv(path)
    df = df[['ts', pcol]].dropna().sort_values('ts')
    df = df[(df[pcol] >= 0) & (df[pcol] <= 1)]
    return df.drop_duplicates('ts')

def asof_grid(df, grid, pcol):
    """last price at or before each grid ts."""
    t = df['ts'].values; p = df[pcol].values
    idx = np.searchsorted(t, grid, side='right') - 1
    out = np.where(idx >= 0, p[np.clip(idx, 0, len(p) - 1)], np.nan)
    return out

def main():
    open(LOG, 'w').close()
    manifest = pd.read_csv(os.path.join(RAW, 'manifest.csv'))
    rows, pairs = [], []
    kfiles = {os.path.basename(f)[:-4]: f for f in glob.glob(os.path.join(RAW, 'kalshi', '*.csv'))}
    pfiles = {os.path.basename(f)[:-4]: f for f in glob.glob(os.path.join(RAW, 'poly', '*.csv'))}
    keys = sorted(set(kfiles) & set(pfiles))
    log(f'candidate matched pairs (both venues present): {len(keys)}')
    for key in keys:
        meeting, outcome = key.split('_', 1)
        k = load(kfiles[key]); p = load(pfiles[key])
        if len(k) < 5 or len(p) < 5:
            continue
        lo = int(max(k.ts.min(), p.ts.min())); hi = int(min(k.ts.max(), p.ts.max()))
        if hi - lo < MIN_OBS * STEP:
            reason = 'short_overlap'
            pairs.append(dict(pair=key, meeting=meeting, outcome=outcome, n_obs=0,
                              overlap_days=(hi - lo) / 86400, kalshi_sd=np.nan,
                              poly_sd=np.nan, selected=False, reason=reason)); continue
        grid = np.arange(lo, hi + 1, STEP)
        kp = asof_grid(k, grid, 'price'); pp = asof_grid(p, grid, 'price')
        m = ~(np.isnan(kp) | np.isnan(pp))
        grid, kp, pp = grid[m], kp[m], pp[m]
        ksd, psd = float(np.std(kp)), float(np.std(pp))
        sel = (len(grid) >= MIN_OBS) and (max(ksd, psd) >= MIN_SD)
        reason = 'ok' if sel else ('few_obs' if len(grid) < MIN_OBS else 'flat')
        pairs.append(dict(pair=key, meeting=meeting, outcome=outcome, n_obs=len(grid),
                          overlap_days=(hi - lo) / 86400, kalshi_sd=round(ksd, 4),
                          poly_sd=round(psd, 4), selected=sel, reason=reason))
        if sel:
            for t, a, b in zip(grid, kp, pp):
                rows.append((key, meeting, outcome, int(t), a, b))
        log(f'  {key:18s} obs={len(grid):5d} ksd={ksd:.3f} psd={psd:.3f} -> {reason}')
    panel = pd.DataFrame(rows, columns=['pair', 'meeting', 'outcome', 'ts', 'kalshi_p', 'poly_p'])
    panel['datetime'] = pd.to_datetime(panel['ts'], unit='s')
    panel.to_csv(os.path.join(PROC, 'matched_panel.csv'), index=False)
    pd.DataFrame(pairs).to_csv(os.path.join(PROC, 'pairs_selected.csv'), index=False)
    nsel = sum(x['selected'] for x in pairs)
    log(f'DONE. selected pairs={nsel}/{len(pairs)}  panel rows={len(panel)}')

if __name__ == '__main__':
    main()
