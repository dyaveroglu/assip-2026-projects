#!/usr/bin/env python3
"""Project 02 — Figure: the rise of medical-AI patents (AIPD ends 2023)."""
import os, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tr=pd.read_csv(os.path.join(HERE,'output','tables','t1_trend.csv'),index_col=0)
tr=tr[(tr.index>=2005)&(tr.index<=2023)]
FIG=os.path.join(HERE,'output','figures'); os.makedirs(FIG,exist_ok=True)
fig,ax=plt.subplots(figsize=(7,4.3))
ax.plot(tr.index,tr['aimed'],marker='o',ms=4,lw=1.8,color='C3',label='AI $\\cap$ medical (A61) patents')
ax.plot(tr.index,tr['visai'],marker='s',ms=3,lw=1.4,color='C0',label='Vision-AI patents (all)')
ax.set_xlabel('Grant year'); ax.set_ylabel('Firm-matched patents')
ax.set_title('The diffusion of AI into medicine (firm-matched patents)')
ax.legend(fontsize=8,frameon=False); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG,'fig1_medai_trend.pdf'))
print('figure written')
