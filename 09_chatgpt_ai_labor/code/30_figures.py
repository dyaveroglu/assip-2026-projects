#!/usr/bin/env python3
"""Project 09 (ChatGPT) — Step 30: figures.
 fig1: binscatter CAR[0,+10] vs AIIE (continuous) with fit + decile means.
 fig2: mean CAR[0,+10] by sign bucket (supplier / user / substitution).
 fig3: cumulative average abnormal return (CAAR) path around ChatGPT for the
       top vs bottom AIIE tercile -- the signature event-study divergence plot.
"""
import os, sys, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed'); INT = os.path.join(HERE, 'data', 'interim')
RAW = os.path.join(HERE, 'data', 'raw'); FIG = os.path.join(HERE, 'output', 'figures')
os.makedirs(FIG, exist_ok=True)
df = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))

# ---- Fig 1: binscatter CAR[0,+10] vs AIIE ----------------------------------
d = df.dropna(subset=['aiie','car_0_10_cg']).copy()
d['car'] = d.car_0_10_cg.clip(-0.5,0.5)
d['dec'] = pd.qcut(d.aiie, 10, labels=False, duplicates='drop')
b = d.groupby('dec').agg(x=('aiie','mean'), y=('car_0_10_cg','mean')).reset_index()
fig, ax = plt.subplots(figsize=(6.4,4.3))
ax.scatter(d.aiie, d.car, s=7, alpha=0.15, color='gray', label='Firms')
ax.scatter(b.x, b.y, s=70, color='C3', zorder=5, label='Decile means')
m,c = np.polyfit(d.aiie, d.car_0_10_cg, 1)
xs = np.linspace(d.aiie.min(), d.aiie.max(), 50)
ax.plot(xs, m*xs+c, color='C0', lw=2, label=f'Fit (slope={m:+.3f})')
ax.axhline(0, color='k', lw=.6)
ax.set_xlabel('AI Industry Exposure (AIIE, 4-digit NAICS)')
ax.set_ylabel('CAR[0,+10] around ChatGPT')
ax.set_title('Higher AI exposure → higher abnormal return around ChatGPT')
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG,'fig1_aiie_binscatter.pdf'))

# ---- Fig 2: mean CAR[0,+10] by sign bucket ---------------------------------
order=['supplier','user','substitution']; lab=['AI supplier\n(builds AI)','AI user\n(complement)','Substitution\n(AI = product)']
g = df.groupby('bucket').car_0_10_cg.agg(['mean','sem']).reindex(order)
fig2, ax2 = plt.subplots(figsize=(5.8,4.1))
cols=['C2','C0','C3']
ax2.bar(range(3), g['mean'].values*100, yerr=g['sem'].values*100, capsize=4, color=cols, alpha=.85)
ax2.axhline(0, color='k', lw=.6)
ax2.set_xticks(range(3)); ax2.set_xticklabels(lab, fontsize=9)
ax2.set_ylabel('Mean CAR[0,+10] (%)')
ax2.set_title('The sign depends on core vs supplemental exposure')
ax2.grid(axis='y', alpha=.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG,'fig2_sign_buckets.pdf'))

# ---- Fig 3: CAAR path around ChatGPT, top vs bottom AIIE tercile -----------
cars = pd.read_csv(os.path.join(INT,'cars.csv'))[['permno','alpha_cg','beta_cg','n_est_cg']]
dsf = pd.read_csv(os.path.join(RAW,'crsp_daily.csv')); dsf['date']=pd.to_datetime(dsf['date'])
dsf['ret']=pd.to_numeric(dsf['ret'],errors='coerce')
mkt = pd.read_csv(os.path.join(RAW,'crsp_market.csv')); mkt['date']=pd.to_datetime(mkt['date'])
mkt['mktret']=pd.to_numeric(mkt['vwretd'],errors='coerce')
cal = mkt.dropna(subset=['mktret']).sort_values('date').reset_index(drop=True)
pos = cal.index[cal.date>=pd.Timestamp('2022-11-30')][0]
cal['rel']=cal.index-pos
mret = cal.set_index('date')['mktret']; rel_map = cal.set_index('date')['rel']
tinfo = df.dropna(subset=['aiie']).copy()
tinfo['ter']=pd.qcut(tinfo.aiie,3,labels=['low','mid','high'])
grp = tinfo[['permno','ter']].merge(cars,on='permno',how='inner')
r = dsf.merge(grp,on='permno',how='inner')
r['rel']=r.date.map(rel_map)
r=r.dropna(subset=['rel','ret']); r['rel']=r['rel'].astype(int)
r=r[(r.rel>=-10)&(r.rel<=15)]
r['mkt']=r.date.map(mret)
r['ar']=r.ret-(r.alpha_cg+r.beta_cg*r.mkt)
caar={}
for t in ['high','low']:
    s=r[r.ter==t].groupby('rel')['ar'].mean().sort_index()
    cs=s.reindex(range(-10,16)).fillna(0).cumsum()
    caar[t]=cs - cs.loc[-1]   # re-base to 0 at day -1 -> isolates the event-window divergence
fig3, ax3 = plt.subplots(figsize=(6.6,4.3))
ax3.plot(caar['high'].index, caar['high'].values*100, color='C0', lw=2, marker='o', ms=3, label='High-AIIE tercile')
ax3.plot(caar['low'].index, caar['low'].values*100, color='C3', lw=2, marker='s', ms=3, label='Low-AIIE tercile')
ax3.axvline(0, color='k', lw=.8, ls='--'); ax3.axhline(0, color='k', lw=.6)
ax3.set_xlabel('Trading days relative to ChatGPT release (day 0 = 2022-11-30)')
ax3.set_ylabel('Cumulative average abnormal return (%)')
ax3.set_title('CAAR diverges after ChatGPT: high- vs low-AI-exposure firms')
ax3.legend(fontsize=9, frameon=False); ax3.grid(alpha=.2)
fig3.tight_layout(); fig3.savefig(os.path.join(FIG,'fig3_caar_path.pdf'))
print('figures written:', sorted(os.listdir(FIG)))
