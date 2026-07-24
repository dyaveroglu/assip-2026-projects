#!/usr/bin/env python3
"""Project 13 - Step 30: figures (all from processed data / output CSVs)."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed')
OUT  = os.path.join(HERE, 'output', 'tables')
FIG  = os.path.join(HERE, 'output', 'figures')
os.makedirs(FIG, exist_ok=True)
KAL, POL = '#1f77b4', '#d62728'

# ---- Fig 1: matched price path, June-2026 'no change' ----
panel = pd.read_csv(os.path.join(PROC, 'matched_panel.csv'), parse_dates=['datetime'])
g = panel[panel.pair == '26JUN_no_change'].sort_values('datetime')
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.plot(g.datetime, g.kalshi_p, color=KAL, lw=1.1, label='Kalshi')
ax.plot(g.datetime, g.poly_p, color=POL, lw=1.1, alpha=0.8, label='Polymarket')
ax.set_ylabel("P(no change) — YES price"); ax.set_xlabel('Date (2026)')
ax.set_title("Matched contract: 'Fed holds at June 2026 meeting'")
ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.25)
fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_matched_series.pdf'))

# ---- Fig 2: pooled lead-lag cross-correlation ----
ccf = pd.read_csv(os.path.join(OUT, 'ccf_pooled.csv')).sort_values('lag')
fig2, ax2 = plt.subplots(figsize=(7.0, 4.2))
colors = [POL if l < 0 else (KAL if l > 0 else 'gray') for l in ccf.lag]
ax2.bar(ccf.lag, ccf.mean_ccf, color=colors, width=0.8)
ax2.axvline(0, color='k', lw=0.7)
ax2.set_xlabel('Lag $k$ (hours):  corr($\\Delta$Kalshi$_t$, $\\Delta$Polymarket$_{t+k}$)')
ax2.set_ylabel('Mean cross-correlation (15 pairs)')
ax2.set_title('Lead-lag: negative lags (red) = Polymarket leads Kalshi')
ax2.grid(alpha=0.25, axis='y')
fig2.tight_layout(); fig2.savefig(os.path.join(FIG, 'fig2_leadlag_ccf.pdf'))

# ---- Fig 3: Hasbrouck information share by pair ----
hb = pd.read_csv(os.path.join(OUT, 't5_hasbrouck.csv')).dropna(subset=['IS_kalshi_mid'])
hb = hb.sort_values('IS_kalshi_mid')
y = np.arange(len(hb))
fig3, ax3 = plt.subplots(figsize=(7.2, 5.0))
ax3.barh(y, hb.IS_kalshi_mid, color=KAL, label='Kalshi info share')
ax3.barh(y, 1 - hb.IS_kalshi_mid, left=hb.IS_kalshi_mid, color=POL, label='Polymarket info share')
# error bars for Kalshi bounds
ax3.errorbar(hb.IS_kalshi_mid, y, xerr=[hb.IS_kalshi_mid - hb.IS_kalshi_lo,
             hb.IS_kalshi_hi - hb.IS_kalshi_mid], fmt='none', ecolor='k', elinewidth=0.8, capsize=2)
ax3.axvline(0.5, color='k', ls='--', lw=0.9)
ax3.set_yticks(y); ax3.set_yticklabels(hb.pair, fontsize=8)
ax3.set_xlabel('Hasbrouck information share'); ax3.set_xlim(0, 1)
ax3.set_title('Who leads? Information share by matched FOMC contract')
ax3.legend(frameon=False, fontsize=8, loc='lower right')
fig3.tight_layout(); fig3.savefig(os.path.join(FIG, 'fig3_hasbrouck_is.pdf'))

# ---- Fig 4: event-study accuracy path (June 2026) ----
ep = pd.read_csv(os.path.join(OUT, 'eventpath_26jun.csv'))
ep = ep[ep.hours_to_statement >= -168]
fig4, ax4 = plt.subplots(figsize=(7.2, 4.2))
ax4.plot(ep.hours_to_statement, ep.kalshi_mae, color=KAL, lw=1.3, label='Kalshi')
ax4.plot(ep.hours_to_statement, ep.poly_mae, color=POL, lw=1.3, label='Polymarket')
ax4.set_xlabel('Hours to FOMC statement'); ax4.set_ylabel('Mean abs pricing error (5 outcomes)')
ax4.set_title('Convergence to the realized outcome (June 2026 FOMC)')
ax4.legend(frameon=False, fontsize=9); ax4.grid(alpha=0.25); ax4.invert_xaxis()
fig4.tight_layout(); fig4.savefig(os.path.join(FIG, 'fig4_eventstudy.pdf'))

print('figures written:', os.listdir(FIG))
