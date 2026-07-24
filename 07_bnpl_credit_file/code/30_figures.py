#!/usr/bin/env python3
"""Project 07 (BNPL) — Step 30: figures for the honest 'no furnishing-specific effect' result."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(HERE, 'data', 'interim'); OUT = os.path.join(HERE, 'output', 'tables')
FIG = os.path.join(HERE, 'output', 'figures'); os.makedirs(FIG, exist_ok=True)

# Fig 1: Affirm vs peer-average credit-reporting complaints over time (they move together)
s = pd.read_csv(os.path.join(INT, 'eventstudy_series.csv'), index_col=0)
x = range(len(s))
fig, ax = plt.subplots(figsize=(7.2, 4.3))
ax.plot(x, s['Affirm'], marker='o', ms=3, lw=1.8, color='C3', label='Affirm (began furnishing ~Apr 2025)')
ax.plot(x, s['PeerAvg'], marker='s', ms=3, lw=1.8, color='C0', label='Peer BNPL average (furnishing dates not confirmed)')
# mark the event month
if '2025-04' in list(s.index):
    ev = list(s.index).index('2025-04')
    ax.axvline(ev, color='gray', ls='--', lw=1)
    ax.text(ev+0.2, ax.get_ylim()[1]*0.9, 'Affirm-Experian\nfurnishing', fontsize=7, color='gray')
step = max(1, len(s)//12)
ax.set_xticks(list(x)[::step]); ax.set_xticklabels(list(s.index)[::step], rotation=45, ha='right', fontsize=7)
ax.set_ylabel('Monthly credit-reporting complaints')
ax.set_title('No Affirm-specific jump: credit-reporting complaints rise sector-wide')
ax.legend(fontsize=8, frameon=False); ax.grid(alpha=0.2)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_affirm_vs_peers.pdf'))

# Fig 2: Affirm complaint composition — all products surged (CR not disproportionate)
c = pd.read_csv(os.path.join(OUT, 't1_composition.csv'), index_col=0)
short = {'Credit reporting or other personal consumer reports':'Credit reporting',
         'Payday loan, title loan, personal loan, or advance loan':'Personal loan',
         'Debt collection':'Debt collection','Credit card':'Credit card',
         'Checking or savings account':'Deposit acct',
         'Money transfer, virtual currency, or money service':'Money transfer'}
c.index = [short.get(i, i[:18]) for i in c.index]
fig2, ax2 = plt.subplots(figsize=(6.4, 4.0))
xx = np.arange(len(c)); wdt = 0.4
ax2.bar(xx-wdt/2, c['pre_permo'], wdt, label='Pre (avg/mo)', color='C0', alpha=0.8)
ax2.bar(xx+wdt/2, c['post_permo'], wdt, label='Post (avg/mo)', color='C3', alpha=0.85)
ax2.set_xticks(xx); ax2.set_xticklabels(c.index, rotation=35, ha='right', fontsize=8)
ax2.set_ylabel('Complaints per month (Affirm)')
ax2.set_title('Every product category surged, not just credit reporting')
ax2.legend(fontsize=8, frameon=False); ax2.grid(axis='y', alpha=0.2)
fig2.tight_layout(); fig2.savefig(os.path.join(FIG, 'fig2_composition.pdf'))
print('figures written:', [f for f in os.listdir(FIG) if f.endswith('.pdf')])
