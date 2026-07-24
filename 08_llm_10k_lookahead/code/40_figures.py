#!/usr/bin/env python3
"""Project 08 — Step 40: figures."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(HERE, 'data', 'processed', 'panel.csv'))
FIG = os.path.join(HERE, 'output', 'figures'); os.makedirs(FIG, exist_ok=True)

# ---- Fig 1: raw vs anon score agreement, by cutoff window ----
fig, ax = plt.subplots(figsize=(6.0, 5.4))
for tag, c, lab in [('pre','C0','Pre-cutoff (2019-21)'), ('post','C3','Post-cutoff (2024)')]:
    s = df[df.window==tag]
    ax.scatter(s.score_anon, s.score_raw, s=32, alpha=0.6, color=c, label=lab, edgecolor='none')
lim = [min(df.score_anon.min(), df.score_raw.min())-3, max(df.score_anon.max(), df.score_raw.max())+3]
ax.plot(lim, lim, 'k--', lw=1, alpha=0.6, label='45$^\\circ$ (raw = anon)')
ax.set_xlabel('Anonymized-text risk score'); ax.set_ylabel('Raw-text risk score')
ax.set_title('gpt-4o risk scores: raw vs. anonymized 10-K text')
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG,'fig1_score_agreement.pdf'))

# ---- Fig 2: return-predictability slopes, RAW vs ANON x PRE vs POST ----
import statsmodels.formula.api as smf
cells = [('RAW\npre','z_raw',df[df.post==0]), ('ANON\npre','z_anon',df[df.post==0]),
         ('RAW\npost','z_raw',df[df.post==1]), ('ANON\npost','z_anon',df[df.post==1])]
labs=[]; coefs=[]; ses=[]; cols=[]
for name,key,data in cells:
    data=data.dropna(subset=['bhar_12_w',key])
    if len(data)<5:
        labs.append(name); coefs.append(np.nan); ses.append(0); cols.append('gray'); continue
    m=smf.ols(f'bhar_12_w ~ {key}', data).fit(cov_type='HC1')
    labs.append(name); coefs.append(m.params[key]); ses.append(m.bse[key])
    cols.append('C0' if 'pre' in name else 'C3')
fig2, ax2 = plt.subplots(figsize=(6.2, 4.6))
x=np.arange(len(labs))
ax2.bar(x, coefs, yerr=1.96*np.array(ses), color=cols, alpha=0.85, capsize=4)
ax2.axhline(0, color='k', lw=0.8)
ax2.set_xticks(x); ax2.set_xticklabels(labs)
ax2.set_ylabel('Slope: 12m BHAR per 1-SD risk score')
ax2.set_title('Does the LLM risk score predict returns?\n(negative = higher score $\\to$ lower return)')
ax2.grid(axis='y', alpha=0.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG,'fig2_predictability_slopes.pdf'))

# ---- Fig 3: scatter bhar vs raw & anon score, pre-cutoff ----
pre = df[df.post==0]
fig3, axes = plt.subplots(1, 2, figsize=(9.4, 4.4), sharey=True)
for ax, key, ttl in [(axes[0],'score_raw','Raw text'), (axes[1],'score_anon','Anonymized text')]:
    d = pre.dropna(subset=['bhar_12_w',key])
    ax.scatter(d[key], d.bhar_12_w, s=28, alpha=0.55, color='C0', edgecolor='none')
    if len(d)>=5:
        m,c=np.polyfit(d[key], d.bhar_12_w,1)
        xs=np.linspace(d[key].min(), d[key].max(),40)
        ax.plot(xs, m*xs+c, 'C3', lw=2, label=f'slope={m:.4f}')
        ax.legend(fontsize=8, frameon=False)
    ax.axhline(0,color='k',lw=0.6,alpha=0.5)
    ax.set_xlabel(f'{ttl} risk score'); ax.set_title(f'Pre-cutoff: BHAR vs. {ttl.lower()} score')
    ax.grid(alpha=0.2)
axes[0].set_ylabel('12-month BHAR (winsorized)')
fig3.tight_layout(); fig3.savefig(os.path.join(FIG,'fig3_pre_scatter.pdf'))

print('figures written:', sorted(os.listdir(FIG)))
