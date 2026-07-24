#!/usr/bin/env python3
"""Project 10 (SVB) — Step 30: figures."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(HERE, 'data', 'processed', 'analytical_panel.csv'))
FIG = os.path.join(HERE, 'output', 'figures'); os.makedirs(FIG, exist_ok=True)

# Fig 1: binscatter CAR[0,+3] vs uninsured ratio
d = df.dropna(subset=['uninsured_ratio', 'car_0_3']).copy()
d['q'] = pd.qcut(d.uninsured_ratio, 10, labels=False, duplicates='drop')
b = d.groupby('q').agg(x=('uninsured_ratio', 'mean'), y=('car_0_3', 'mean')).reset_index()
fig, ax = plt.subplots(figsize=(6.2, 4.3))
ax.scatter(d.uninsured_ratio, d.car_0_3, s=10, alpha=0.25, color='gray', label='Banks')
ax.scatter(b.x, b.y, s=70, color='C3', zorder=5, label='Decile means')
m, c = np.polyfit(d.uninsured_ratio, d.car_0_3, 1)
xs = np.linspace(d.uninsured_ratio.min(), d.uninsured_ratio.max(), 50)
ax.plot(xs, m*xs + c, color='C0', lw=2, label=f'Fit (slope={m:.2f})')
ax.set_xlabel('Uninsured deposits / Assets (2022Q4)')
ax.set_ylabel('CAR[0,+3] over SVB window')
ax.set_title('Bank stock collapse vs. uninsured-deposit exposure')
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_uninsured_binscatter.pdf'))

# Fig 2: mean CAR by uninsured quartile
d['qt'] = pd.qcut(d.uninsured_ratio, 4, labels=['Q1 (low)','Q2','Q3','Q4 (high)'])
g = d.groupby('qt').car_0_3.mean()
fig2, ax2 = plt.subplots(figsize=(5.6, 4.0))
ax2.bar(range(len(g)), g.values, color='C3', alpha=0.85)
ax2.set_xticks(range(len(g))); ax2.set_xticklabels(g.index)
ax2.set_ylabel('Mean CAR[0,+3]'); ax2.set_xlabel('Uninsured-deposit quartile')
ax2.set_title('Higher uninsured exposure -> larger equity loss')
ax2.grid(axis='y', alpha=0.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG, 'fig2_uninsured_quartiles.pdf'))
print('figures written:', os.listdir(FIG))
