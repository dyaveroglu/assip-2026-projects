#!/usr/bin/env python3
"""
Project 04 -- Step 30: figures (PDF, vector) for the paper.

fig1_eventtime_decay.pdf : average anomaly LS return by event-year relative to
    publication (year 0 = publication), expressed as % of the pooled in-sample
    mean. Shows the level sitting near 100% before publication and dropping to
    ~55-60% afterward.
fig2_regime_by_frame.pdf : equal-weighted mean LS return by regime, split by the
    (proxy) risk- vs mispricing-framed groups -- the visual of the H2 null.
"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed')
OUT  = os.path.join(HERE, 'output', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures'); os.makedirs(FIG, exist_ok=True)

d = pd.read_csv(os.path.join(PROC, 'anomaly_panel.csv'))
INS = d.loc[d.insample == 1, 'ret'].mean()

# ------------------------------------------------------------ Figure 1
et = pd.read_csv(os.path.join(OUT, 't6_eventtime.csv'))
et = et[et['n'] >= 300]                    # drop thin extreme bins
fig, ax = plt.subplots(figsize=(7.2, 4.4))
ax.axhline(100, color='0.6', lw=0.8, ls=':')
ax.axvline(0, color='crimson', lw=1.3, ls='--')
ax.plot(et['evt_bin'], et['pct_of_insample'], '-o', color='#12507b', ms=4, lw=1.5)
ax.text(0.4, ax.get_ylim()[1]*0.98, 'publication\nyear', color='crimson',
        fontsize=9, va='top')
ax.set_xlabel('Years relative to publication (0 = publication year)')
ax.set_ylabel('Mean LS return, % of pooled in-sample mean')
ax.set_title('Anomaly long-short returns collapse after publication', fontsize=11)
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_eventtime_decay.pdf'))
plt.close(fig)

# ------------------------------------------------------------ Figure 2
pa = d.groupby(['signal', 'regime', 'risk_framed'])['ret'].mean().reset_index()
order = ['insample', 'postsample', 'postpub']
labels = ['In-sample', 'Post-sample\n(pre-pub)', 'Post-\npublication']
groups = {0: ('Mispricing-framed', '#12507b'), 1: ('Risk-framed', '#c1666b')}
fig, ax = plt.subplots(figsize=(7.2, 4.4))
x = np.arange(len(order)); w = 0.38
for k, (lbl, col) in groups.items():
    means = [pa[(pa.regime == r) & (pa.risk_framed == k)]['ret'].mean() for r in order]
    ses = [pa[(pa.regime == r) & (pa.risk_framed == k)]['ret'].sem() for r in order]
    ax.bar(x + (k - 0.5) * w, means, w, yerr=ses, capsize=3, label=lbl, color=col)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel('Mean monthly LS return (%), equal-weighted')
ax.set_title('Both framings decay similarly (risk vs mispricing proxy)', fontsize=11)
ax.legend(frameon=False)
ax.grid(axis='y', alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig2_regime_by_frame.pdf'))
plt.close(fig)

print('figures written:', os.listdir(FIG))
