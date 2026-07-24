#!/usr/bin/env python3
"""Project 06 — Step 30: figures.
 fig1: pooled dynamic DiD event study (treated vs control, +/- landfall) with 95% CI.
 fig2: belief-split event study (high vs low climate belief) -- the pre-trend diagnostic.
 fig3: raw home-value index (=100 at landfall), treated vs control, by storm.
"""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); FIG = os.path.join(HERE, 'output', 'figures')
PROC = os.path.join(HERE, 'data', 'processed'); os.makedirs(FIG, exist_ok=True)

# ---------------- fig1: pooled event study
es = pd.read_csv(os.path.join(OUT, 't4_eventstudy.csv')).sort_values('rel_month')
fig, ax = plt.subplots(figsize=(7.4, 4.4))
ax.axhline(0, color='k', lw=0.7); ax.axvline(0, color='gray', ls='--', lw=1)
ax.fill_between(es.rel_month, 100*(es.coef-1.96*es.se), 100*(es.coef+1.96*es.se),
                color='C0', alpha=0.18)
ax.plot(es.rel_month, 100*es.coef, marker='o', ms=3, lw=1.6, color='C0')
ax.text(0.6, ax.get_ylim()[1]*0.86, 'landfall', fontsize=8, color='gray')
ax.set_xlabel('Months since landfall'); ax.set_ylabel('Treated $-$ control ln ZHVI ($\\times$100)')
ax.set_title('Dynamic DiD: hard-hit vs control home values around landfall\n'
             '(note the upward pre-trend $\\Rightarrow$ parallel-trends is not clean)', fontsize=10)
ax.grid(alpha=0.2); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_eventstudy.pdf'))

# ---------------- fig2: belief-split event study
s = pd.read_csv(os.path.join(OUT, 't5_eventstudy_beliefsplit.csv'))
fig2, ax2 = plt.subplots(figsize=(7.4, 4.4))
ax2.axhline(0, color='k', lw=0.7); ax2.axvline(0, color='gray', ls='--', lw=1)
for grp, col in [('High belief', 'C3'), ('Low belief', 'C0')]:
    g = s[s.group == grp].sort_values('rel_month')
    ax2.plot(g.rel_month, 100*g.coef, marker='o', ms=3, lw=1.6, color=col, label=grp)
    ax2.fill_between(g.rel_month, 100*(g.coef-1.96*g.se), 100*(g.coef+1.96*g.se), color=col, alpha=0.12)
ax2.set_xlabel('Months since landfall'); ax2.set_ylabel('Treated $-$ control ln ZHVI ($\\times$100)')
ax2.set_title('Belief split: the high-belief pre-trend is steep (Florida/Ian coast),\n'
              'the low-belief group is flat pre-storm then declines', fontsize=10)
ax2.legend(fontsize=9, frameon=False); ax2.grid(alpha=0.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG, 'fig2_belief_split.pdf'))

# ---------------- fig3: raw index by storm
p = pd.read_csv(os.path.join(PROC, 'panel.csv'), dtype={'fips': str})
fig3, axes = plt.subplots(1, 2, figsize=(9.2, 4.2), sharey=True)
for ax3, ev in zip(axes, ['Ian', 'Helene']):
    sub = p[p.event == ev]
    for tr, lab, col in [(1, 'Hard-hit (IHP)', 'C3'), (0, 'Control', 'C0')]:
        m = sub[sub.treat == tr].groupby('rel_month').ln_zhvi.mean()
        base = m.loc[0]
        ax3.plot(m.index, 100*np.exp(m - base), lw=1.8, color=col, label=lab)
    ax3.axvline(0, color='gray', ls='--', lw=1)
    ax3.set_title(f'Hurricane {ev} ({"2022-09" if ev=="Ian" else "2024-09"})', fontsize=10)
    ax3.set_xlabel('Months since landfall'); ax3.grid(alpha=0.2)
axes[0].set_ylabel('Home-value index (=100 at landfall)')
axes[0].legend(fontsize=9, frameon=False)
fig3.suptitle('Typical home value, hard-hit vs control counties (raw)', fontsize=11)
fig3.tight_layout(); fig3.savefig(os.path.join(FIG, 'fig3_raw_by_event.pdf'))
print('figures written:', sorted(f for f in os.listdir(FIG) if f.endswith('.pdf')))
