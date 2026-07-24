#!/usr/bin/env python3
"""Project 01 — Figure: AI-adoption event study (employment + productivity)."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
t = pd.read_csv(os.path.join(HERE,'output','tables','t3_eventstudy.csv'))
t['se'] = (t.coef / t.t).abs()
FIG = os.path.join(HERE,'output','figures'); os.makedirs(FIG, exist_ok=True)

fig, ax = plt.subplots(figsize=(7,4.4))
for out,color,mk in [('ln(Employment)','C0','o'),('ln(Sales/Emp)','C3','s')]:
    d = t[t.outcome==out].sort_values('k')
    ax.errorbar(d.k, d.coef, yerr=1.96*d.se.fillna(0), marker=mk, ms=4, lw=1.6,
                capsize=2, color=color, label=out)
ax.axhline(0, color='gray', lw=0.8); ax.axvline(-0.5, color='gray', ls='--', lw=0.8)
ax.set_xlabel("Years relative to firm's first AI patent (k)")
ax.set_ylabel('Coefficient (relative to k=-1)')
ax.set_title('After adopting AI, firms grow employment and productivity')
ax.legend(fontsize=9, frameon=False); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG,'fig1_ai_eventstudy.pdf'))
print('figure written')
