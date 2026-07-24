#!/usr/bin/env python3
"""Project 15 — atlas figures."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a=pd.read_csv(os.path.join(HERE,'output','tables','t1_atlas_full.csv'))
FIG=os.path.join(HERE,'output','figures'); os.makedirs(FIG,exist_ok=True)
a=a.sort_values('date').reset_index(drop=True)

# Fig 1: announcement CAR[0,+1] per shock, with cross-sectional SD as spread
fig,ax=plt.subplots(figsize=(7.6,5))
y=np.arange(len(a))
ax.errorbar(a.mean_ann, y, xerr=a.sd_ann, fmt='o', ms=6, color='C0', ecolor='C7',
            capsize=3, lw=1.5, label='Mean firm CAR[0,+1] ± cross-sectional SD')
ax.scatter(a.mkt_ann_pct, y, marker='|', s=200, color='C3', label='Raw market move [0,+1]')
ax.axvline(0,color='gray',lw=0.8)
ax.set_yticks(y); ax.set_yticklabels([f"{r.event} ({r.owner})" for _,r in a.iterrows()], fontsize=7.5)
ax.set_xlabel('Return over [0,+1] (%)'); ax.set_title('The 2022–2025 policy-shock atlas: announcement reactions')
ax.legend(fontsize=8, frameon=False, loc='lower right'); ax.grid(axis='x', alpha=0.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG,'fig1_atlas.pdf'))

# Fig 2: anticipation (pre-window) vs announcement per shock
fig2,ax2=plt.subplots(figsize=(6.6,4.4))
ax2.bar(y-0.2, a.mean_pre, 0.4, label='Anticipation CAR[-5,-1]', color='C1', alpha=0.85)
ax2.bar(y+0.2, a.mean_ann, 0.4, label='Announcement CAR[0,+1]', color='C0', alpha=0.85)
ax2.set_xticks(y); ax2.set_xticklabels([r.event for _,r in a.iterrows()], rotation=40, ha='right', fontsize=7)
ax2.set_ylabel('Mean firm CAR (%)'); ax2.axhline(0,color='gray',lw=0.8)
ax2.set_title('Leakage before the news vs. reaction on the news')
ax2.legend(fontsize=8, frameon=False); ax2.grid(axis='y', alpha=0.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG,'fig2_anticipation.pdf'))
print('figures written')
