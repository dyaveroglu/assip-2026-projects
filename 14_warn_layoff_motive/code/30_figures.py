#!/usr/bin/env python3
"""Project 14 (WARN) - Step 30: figures (event-time AR path; CAR by group)."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(HERE, 'data', 'interim'); OUT = os.path.join(HERE, 'output', 'tables')
FIG = os.path.join(HERE, 'output', 'figures'); os.makedirs(FIG, exist_ok=True)

# ---- Fig 1: cumulative average abnormal return in event time ----------
path = pd.read_csv(os.path.join(INT, 'ar_path.csv'))
fig, ax = plt.subplots(figsize=(6.4, 4.3))
ax.axhline(0, color='k', lw=0.6); ax.axvline(0, color='C3', lw=1, ls='--', alpha=0.7)
ax.plot(path.rel_day, path.cum_ar*100, marker='o', ms=4, color='C0', lw=1.8)
ax.set_xlabel('Trading day relative to WARN notice (day 0)')
ax.set_ylabel('Cumulative average abnormal return (%)')
ax.set_title('Market reaction around mass-layoff (WARN) notices')
ax.grid(alpha=0.25)
ax.annotate(f"CAAR[0,+5] = {(path.set_index('rel_day').loc[5,'cum_ar']-path.set_index('rel_day').loc[-1,'cum_ar'])*100:+.1f}%",
            xy=(5, path.set_index('rel_day').loc[5,'cum_ar']*100), fontsize=8,
            xytext=(6, path.set_index('rel_day').loc[5,'cum_ar']*100-0.4))
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_ar_path.pdf'))

# ---- Fig 2: mean CAR[0,+5] by group -----------------------------------
t3 = pd.read_csv(os.path.join(OUT, 't3_car_groups.csv'))
order = ['Large firm (above-median assets)', 'Small firm (below-median assets)',
         'Small rel. layoff (bottom half)', 'Large rel. layoff (top half)',
         'Closure', 'Ongoing-op layoff']
short = {'Large firm (above-median assets)': 'Large firm', 'Small firm (below-median assets)': 'Small firm',
         'Small rel. layoff (bottom half)': 'Small rel.\nlayoff', 'Large rel. layoff (top half)': 'Large rel.\nlayoff',
         'Closure': 'Closure', 'Ongoing-op layoff': 'Ongoing\nlayoff'}
t3 = t3.set_index('group').loc[order].reset_index()
colors = ['#4C72B0','#C44E52','#4C72B0','#C44E52','#8172B3','#8172B3']
fig2, ax2 = plt.subplots(figsize=(7.2, 4.3))
b = ax2.bar(range(len(t3)), t3.mean_car*100, color=colors, alpha=0.9)
ax2.axhline(0, color='k', lw=0.6)
ax2.set_xticks(range(len(t3))); ax2.set_xticklabels([short[g] for g in t3.group], fontsize=8)
ax2.set_ylabel('Mean CAR[0,+5] (%)')
ax2.set_title('Who gets punished? CAR by firm size, relative layoff size, and form')
for i, r in t3.iterrows():
    ax2.annotate(f"{r.mean_car*100:+.1f}\n(t={r.t_stat:.1f})", (i, r.mean_car*100),
                 ha='center', va='bottom' if r.mean_car >= 0 else 'top', fontsize=7)
ax2.axvline(1.5, color='gray', lw=0.5, ls=':'); ax2.axvline(3.5, color='gray', lw=0.5, ls=':')
ax2.grid(axis='y', alpha=0.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG, 'fig2_car_by_group.pdf'))
print('figures written:', os.listdir(FIG))
