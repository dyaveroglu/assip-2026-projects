#!/usr/bin/env python3
"""
Project 03 (Clawbacks) — Step 30: figures.
  fig1_eventstudy.pdf  dynamic DiD for the headline outcome (idiosyncratic vol):
                       shows the parallel-trends violation + no clean 2023 break.
  fig2_groupmeans.pdf  raw group means over time: volatility (COVID divergence)
                       vs investment/assets (no clawback break).
All numbers read from output/tables/*.csv and data/processed/*.csv.
"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); FIG = os.path.join(HERE, 'output', 'figures')
PROC = os.path.join(HERE, 'data', 'processed'); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({'font.size': 11, 'axes.splines.top' if False else 'axes.grid': False})

meta = pd.read_csv(os.path.join(OUT, 't0_meta.csv'))
HEAD = meta.headline_outcome.iloc[0]; HLAB = meta.headline_label.iloc[0].replace('\\&','&')

# ---- fig1: event study --------------------------------------------------
es = pd.read_csv(os.path.join(OUT, 't4_eventstudy.csv'))
es['lo'] = es.coef - 1.96 * es.se; es['hi'] = es.coef + 1.96 * es.se
fig, ax = plt.subplots(figsize=(7.2, 4.4))
ax.axhline(0, color='0.6', lw=0.8)
ax.axvline(2022.5, color='crimson', ls='--', lw=1.2)
ax.text(2022.6, ax.get_ylim()[1], '  SEC 10D-1 effective', color='crimson',
        va='top', ha='left', fontsize=9)
ax.errorbar(es.fyear, es.coef, yerr=1.96 * es.se, fmt='o-', color='#1f4e79',
            ecolor='#9fb8d6', capsize=3, lw=1.5, ms=5)
ax.set_xlabel('Fiscal year'); ax.set_ylabel(f'DiD coefficient: {HLAB}\n(relative to 2022)')
ax.set_title('Dynamic DiD: treated (S&P 600) vs control (S&P 500)', fontsize=11)
ax.set_xticks(range(int(es.fyear.min()), int(es.fyear.max()) + 1))
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_eventstudy.pdf')); plt.close(fig)

# ---- fig2: raw group means ----------------------------------------------
df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))
m = df[df.treat.notna()].copy()
def gm(v):
    g = m.groupby(['fyear', 'treat'])[v].mean().unstack()
    return g
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
for ax, v, ttl in [(axes[0], HEAD, HLAB),
                   (axes[1], 'invest_at', 'Investment/Assets')]:
    g = gm(v)
    ax.plot(g.index, g[0.0], 'o-', color='#1f4e79', label='Control (S&P 500)')
    ax.plot(g.index, g[1.0], 's--', color='#c0504d', label='Treated (S&P 600)')
    ax.axvline(2022.5, color='0.5', ls=':', lw=1)
    ax.set_title(ttl, fontsize=11); ax.set_xlabel('Fiscal year')
    ax.set_xticks(range(int(g.index.min()), int(g.index.max()) + 1, 2))
axes[0].set_ylabel('Group mean')
axes[0].legend(frameon=False, fontsize=9, loc='upper left')
fig.suptitle('Treated vs control group means (vertical line = rule effective)', fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig2_groupmeans.pdf')); plt.close(fig)

print('figures written:', os.listdir(FIG))
