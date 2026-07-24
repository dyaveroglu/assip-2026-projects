#!/usr/bin/env python3
"""Project 12 (Half-Cent Tick) - Step 30: figures (all from processed panel / CSVs)."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE,'data','processed'); OUT=os.path.join(HERE,'output','tables')
FIG = os.path.join(HERE,'output','figures'); os.makedirs(FIG, exist_ok=True)

full = pd.read_csv(os.path.join(PROC,'panel_full.csv'), parse_dates=['date'])
full = full[(full.evt_week>=-6)&(full.evt_week<=6)]

# ---- Fig 1: event-time mean relative quoted spread, treated vs control ----
g = full.groupby(['evt_week','treated']).rqs_bps_w.mean().unstack()
fig,ax = plt.subplots(figsize=(6.6,4.3))
ax.plot(g.index, g[1], '-o', color='C3', lw=2, ms=4, label='Treated (tick-constrained, $\\leq$1.5c)')
ax.plot(g.index, g[0], '-s', color='C0', lw=2, ms=4, label='Control (wide-spread)')
ax.axvline(0, color='k', ls='--', lw=1)
ax.text(0.15, ax.get_ylim()[1]*0.98, 'Nov 3 2025\ncompliance', fontsize=8, va='top')
ax.set_xlabel('Event week (0 = week of Nov 3, 2025)')
ax.set_ylabel('Mean relative quoted spread (bps)')
ax.set_title('Daily closing quoted spreads: treated vs control')
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(FIG,'fig1_eventtime_spreads.pdf'))

# ---- Fig 2: event-study DiD coefficients (weekly), 95% CI ----
es = pd.read_csv(os.path.join(OUT,'t5_eventstudy.csv'))
fig2,ax2 = plt.subplots(figsize=(6.6,4.3))
ax2.errorbar(es.evt_week, es.coef, yerr=1.96*es.se, fmt='o', color='C3',
             ecolor='gray', capsize=3, ms=5)
ax2.axhline(0, color='k', lw=1); ax2.axvline(-0.5, color='k', ls='--', lw=1)
ax2.text(0.1, ax2.get_ylim()[1]*0.9, 'Nov 3 2025', fontsize=8)
ax2.set_xlabel('Event week (base = week $-1$)')
ax2.set_ylabel('Treated$\\times$week coef. on rel. spread (bps)')
ax2.set_title('Event-study: non-parallel pre-trends, no clean post-event drop')
ax2.grid(alpha=0.25)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG,'fig2_eventstudy_coefs.pdf'))

# ---- Fig 3: mechanism -- penny-grid censoring of the treated close ----
cen = pd.read_csv(os.path.join(OUT,'t8_censoring.csv'))
tr = cen[cen.group.str.startswith('Treated')]
x = np.arange(2); w=0.35
fig3,ax3 = plt.subplots(figsize=(6.2,4.3))
ax3.bar(x-w/2, tr.share_at_1c.values*100, w, color='C3', label='Closing spread = exactly 1.0c')
ax3.bar(x+w/2, tr.share_subpenny.values*100, w, color='C1', label='Closing spread $<$ 1.0c (sub-penny)')
ax3.set_xticks(x); ax3.set_xticklabels(['Pre (Oct)','Post (Nov)'])
ax3.set_ylabel('Share of treated stock-days (%)')
ax3.set_title('The half-cent margin is invisible in daily closing quotes')
for i,v in enumerate(tr.share_subpenny.values*100):
    ax3.text(x[i]+w/2, v+1, f'{v:.1f}%', ha='center', fontsize=8)
ax3.legend(fontsize=8, frameon=False, loc='center right'); ax3.grid(axis='y', alpha=0.25)
ax3.set_ylim(0,100)
fig3.tight_layout(); fig3.savefig(os.path.join(FIG,'fig3_censoring.pdf'))
print('figures written:', sorted(os.listdir(FIG)))
