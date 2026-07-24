#!/usr/bin/env python3
"""Project 11 (CHIPS awards) -- Step 30: figures.
Fig 1: CAR[-1,+1] vs award/market-cap, showing the cross-sectional relation is a
       single-leverage-point (Wolfspeed) artifact (fit with vs without WOLF).
Fig 2: mean CAR by event window with 95% CI whiskers -- every window straddles 0.
"""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(HERE, 'data', 'processed', 'analytical_panel.csv'))
FIG = os.path.join(HERE, 'output', 'figures'); os.makedirs(FIG, exist_ok=True)

# ---- Fig 1: CAR[-1,+1] vs award/market cap -------------------------------
d = df.dropna(subset=['award_pct_mktcap','car_m1_1']).copy()
fig, ax = plt.subplots(figsize=(6.4, 4.4))
ax.axhline(0, color='gray', lw=0.8, ls='--')
ax.scatter(d.award_pct_mktcap, d.car_m1_1*100, s=45, color='C0', zorder=4)
for _, r in d.iterrows():
    if r.ticker in ('WOLF','SKYT','AMKR','INTC','TSM','MU'):
        ax.annotate(r.ticker, (r.award_pct_mktcap, r.car_m1_1*100),
                    xytext=(4,4), textcoords='offset points', fontsize=8)
# fit with all points
m, c = np.polyfit(d.award_pct_mktcap, d.car_m1_1*100, 1)
xs = np.linspace(0, d.award_pct_mktcap.max(), 50)
ax.plot(xs, m*xs+c, color='C3', lw=2, label=f'OLS all firms (slope={m:.3f})')
# fit dropping Wolfspeed
dn = d[d.ticker != 'WOLF']
mn, cn = np.polyfit(dn.award_pct_mktcap, dn.car_m1_1*100, 1)
xs2 = np.linspace(0, dn.award_pct_mktcap.max(), 50)
ax.plot(xs2, mn*xs2+cn, color='C2', lw=2, ls='--', label=f'OLS excl. Wolfspeed (slope={mn:.3f})')
ax.set_xlabel('CHIPS award / market cap (%)')
ax.set_ylabel('CAR[-1,+1] (%)')
ax.set_title('Announcement return vs. relative award size')
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_car_vs_award.pdf'))

# ---- Fig 2: mean CAR by window with 95% CI -------------------------------
W = [('car_m1_1','[-1,+1]'), ('car_0_1','[0,+1]'), ('car_0_3','[0,+3]'),
     ('car_m1_5','[-1,+5]'), ('car_m5_5','[-5,+5]'), ('car_pre','[-10,-3]\nplacebo')]
means, cis, labs = [], [], []
for w, lbl in W:
    s = df[w].dropna(); n = len(s)
    se = s.std()/np.sqrt(n); tcrit = stats.t.ppf(0.975, n-1)
    means.append(s.mean()*100); cis.append(tcrit*se*100); labs.append(lbl)
fig2, ax2 = plt.subplots(figsize=(6.4, 4.2))
x = np.arange(len(labs))
ax2.axhline(0, color='gray', lw=0.8, ls='--')
ax2.errorbar(x, means, yerr=cis, fmt='o', color='C0', capsize=4, ms=7)
ax2.set_xticks(x); ax2.set_xticklabels(labs, fontsize=8)
ax2.set_ylabel('Mean CAR (%)'); ax2.set_xlabel('Event window (trading days)')
ax2.set_title('Mean CHIPS-award announcement CAR (95% CI), N=15')
ax2.grid(axis='y', alpha=0.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG, 'fig2_car_windows.pdf'))
print('figures written:', os.listdir(FIG))
