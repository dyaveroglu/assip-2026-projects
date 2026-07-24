#!/usr/bin/env python3
"""Project 05 - Step 30: figures.
Fig 1: added-variable (partial-regression) plots of CAR vs imported-input
       intensity, conditional on size+beta+controls, for the SHOCK (negative
       slope) and the PAUSE (positive slope) - the paired opposite-signed result.
Fig 2: cumulative abnormal-return paths of high- vs low-import-intensity
       portfolios across the April-2025 window, with the two events marked.
"""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); PROC = os.path.join(HERE, 'data', 'processed')
FIG = os.path.join(HERE, 'output', 'figures'); os.makedirs(FIG, exist_ok=True)

df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))
CTRL = ['z_size', 'z_beta', 'z_cogs_int', 'z_lev', 'z_bm']

def resid(y, X):
    X = np.column_stack([np.ones(len(X)), X])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ b

def avplot(ax, dv, title, color):
    d = df.dropna(subset=[dv, 'z_imp_intensity'] + CTRL).copy()
    X = d[CTRL].values
    ry = resid(d[dv].values, X) * 100          # residual CAR, in pct pts
    rx = resid(d['z_imp_intensity'].values, X)
    # decile means of the residualized scatter
    q = pd.qcut(pd.Series(rx), 12, labels=False, duplicates='drop')
    b = pd.DataFrame({'rx': rx, 'ry': ry, 'q': q}).groupby('q').mean()
    ax.scatter(rx, ry, s=6, alpha=0.12, color='gray')
    ax.scatter(b.rx, b.ry, s=55, color=color, zorder=5, label='Bin means')
    m, c = np.polyfit(rx, ry, 1)
    xs = np.linspace(rx.min(), rx.max(), 50)
    ax.plot(xs, m*xs + c, color='black', lw=2, label=f'Slope={m:.2f} pp/SD')
    ax.axhline(0, color='k', lw=.5, alpha=.4); ax.axvline(0, color='k', lw=.5, alpha=.4)
    ax.set_xlabel('Imported-input intensity (residual, SD)')
    ax.set_ylabel(dv + ' residual (pp)')
    ax.set_title(title, fontsize=10); ax.legend(fontsize=8, frameon=False); ax.grid(alpha=.2)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
avplot(axes[0], 'car_s01', 'Tariff SHOCK  (CAR Apr 3-4)', 'C3')
avplot(axes[1], 'car_p0', 'Tariff PAUSE  (CAR Apr 9)', 'C2')
fig.suptitle('Conditional CAR vs imported-input intensity (net of size, beta, controls)',
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(os.path.join(FIG, 'fig1_avplot.pdf'))
print('wrote fig1_avplot.pdf')

# ---- Fig 2: CAR paths, high vs low intensity ------------------------------
dsf = pd.read_csv(os.path.join(RAW, 'crsp_daily.csv'))
dsf['date'] = pd.to_datetime(dsf['date']); dsf['ret'] = pd.to_numeric(dsf['ret'], errors='coerce')
mkt = pd.read_csv(os.path.join(RAW, 'market_ff.csv'))
mkt['date'] = pd.to_datetime(mkt['date'])
ab = df.dropna(subset=['imp_intensity', 'alpha', 'beta']).copy()
ab['grp'] = pd.qcut(ab.imp_intensity, 4, labels=False, duplicates='drop')
ab = ab[ab.grp.isin([0, 3])]                 # bottom & top quartile
win = pd.date_range('2025-03-26', '2025-04-15')
r = dsf[dsf.date.isin(win)].merge(ab[['permno', 'grp', 'alpha', 'beta']], on='permno', how='inner')
r = r.merge(mkt[['date', 'mktret']], on='date', how='left')
r['ar'] = r['ret'] - (r['alpha'] + r['beta']*r['mktret'])
path = r.groupby(['grp', 'date']).ar.mean().reset_index()
fig2, ax = plt.subplots(figsize=(7.2, 4.4))
for g, lab, col in [(3, 'Top quartile (high import exposure)', 'C3'),
                    (0, 'Bottom quartile (low import exposure)', 'C0')]:
    s = path[path.grp == g].sort_values('date')
    ax.plot(s.date, 100*s.ar.cumsum(), marker='o', ms=3, color=col, label=lab)
ax.axvline(pd.Timestamp('2025-04-02'), color='firebrick', ls='--', lw=1)
ax.axvline(pd.Timestamp('2025-04-09'), color='seagreen', ls='--', lw=1)
ax.text(pd.Timestamp('2025-04-02'), ax.get_ylim()[1]*0.92, ' Apr 2 tariffs', color='firebrick', fontsize=8)
ax.text(pd.Timestamp('2025-04-09'), ax.get_ylim()[0]*0.9, ' Apr 9 pause', color='seagreen', fontsize=8)
ax.axhline(0, color='k', lw=.5, alpha=.4)
ax.set_ylabel('Cumulative abnormal return (pp)'); ax.set_xlabel('2025')
ax.set_title('Cumulative abnormal returns: high- vs low-imported-input-intensity firms')
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=.2)
fig2.autofmt_xdate(); fig2.tight_layout()
fig2.savefig(os.path.join(FIG, 'fig2_carpath.pdf'))
print('wrote fig2_carpath.pdf')
