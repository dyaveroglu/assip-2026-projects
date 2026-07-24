#!/usr/bin/env python3
"""Project 13 - Step 35: render booktabs LaTeX tables from the output CSVs.
Every number in the paper is read from output/tables/*.csv here, so the paper can
never drift from the analysis."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

FOMC = {'26JUN': 'Jun 17, 2026', '26JUL': 'Jul 29, 2026',
        '26SEP': 'Sep 16, 2026', '26OCT': 'Oct 28, 2026'}
RESV = {'26JUN': 'resolved (hold)', '26JUL': 'open', '26SEP': 'open', '26OCT': 'open'}
OCL = {'no_change': 'Hold', 'cut25': 'Cut~25', 'cut50p': 'Cut~50+',
       'hike25': 'Hike~25', 'hike50p': 'Hike~50+'}
def lbl(pair):
    m, o = pair.split('_', 1); return f"{m[2:]}~{OCL.get(o, o)}"
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)
def stars(p):
    return '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else ''

# ---------- Table 1: sample ----------
s = pd.read_csv(os.path.join(OUT, 't1_sample.csv'))
rows = ''
for _, r in s.iterrows():
    m = r['meeting']
    rows += (f"{m} & {FOMC.get(m,'')} & {RESV.get(m,'')} & {int(r['pairs'])} & "
             f"{int(r['obs'])} & {r['mean_gap']*100:.1f} & {r['mean_corr']:.2f} \\\\\n")
tot = f"\\midrule\nTotal & & & {int(s['pairs'].sum())} & {int(s['obs'].sum())} & " \
      f"{ (pd.read_csv(os.path.join(OUT,'t2_sumstats.csv'))['mean_abs_gap'].mean()*100):.1f} & " \
      f"{pd.read_csv(os.path.join(OUT,'t2_sumstats.csv'))['corr_level'].mean():.2f} \\\\\n"
w('tab_sample.tex', r"""\begin{tabular}{lllcccc}
\toprule
Meeting & FOMC date & Status & Pairs & Hourly obs & Mean $|$gap$|$ (\textcent) & Mean corr \\
\midrule
""" + rows + tot + r"""\bottomrule
\end{tabular}""")

# ---------- Table 2: descriptive co-movement (summary) ----------
d = pd.read_csv(os.path.join(OUT, 't2_sumstats.csv'))
sm = pd.read_csv(os.path.join(OUT, 't6_summary.csv')).iloc[0]
def qrow(name, col, sc=1.0, dec=3):
    x = d[col]*sc
    return f"{name} & {x.mean():.{dec}f} & {x.std():.{dec}f} & {x.min():.{dec}f} & {x.median():.{dec}f} & {x.max():.{dec}f} \\\\\n"
body = (qrow('Level correlation', 'corr_level')
        + qrow('Hourly-return correlation', 'corr_return')
        + qrow('Mean abs.\\ price gap (\\textcent)', 'mean_abs_gap', 100, 2)
        + qrow('Kalshi hourly-return SD (\\textcent)', 'kalshi_ret_sd', 100, 2)
        + qrow('Polymarket hourly-return SD (\\textcent)', 'poly_ret_sd', 100, 2)
        + qrow('ADF $p$-value (spread)', 'adf_spread_p'))
w('tab_desc.tex', r"""\begin{tabular}{lccccc}
\toprule
 & Mean & SD & Min & Median & Max \\
\midrule
""" + body + r"""\midrule
\multicolumn{6}{l}{\footnotesize Spread stationary (ADF $p<0.05$) in """
   + f"{sm['frac_spread_stationary']*100:.0f}" + r"""\% of pairs.} \\
\bottomrule
\end{tabular}""")

# ---------- Table 3 (MAIN): Hasbrouck information shares ----------
hb = pd.read_csv(os.path.join(OUT, 't5_hasbrouck.csv'))
rows = ''
for _, r in hb.iterrows():
    gg = '' if pd.isna(r['GG_kalshi']) else f"{r['GG_kalshi']:.2f}"
    rows += (f"{lbl(r['pair'])} & {int(r['n'])} & {r['k']} & "
             f"[{r['IS_kalshi_lo']:.2f},\\,{r['IS_kalshi_hi']:.2f}] & {r['IS_kalshi_mid']:.2f} & "
             f"{r['IS_poly_mid']:.2f} & {gg} \\\\\n")
hv = hb.dropna(subset=['IS_kalshi_mid'])
mrow = (f"\\midrule\n\\textit{{Mean}} & {int(hv['n'].mean())} & & & "
        f"\\textbf{{{hv['IS_kalshi_mid'].mean():.2f}}} & \\textbf{{{1-hv['IS_kalshi_mid'].mean():.2f}}} & "
        f"{hb['GG_kalshi'].dropna().mean():.2f} \\\\\n")
wmean = np.average(hv['IS_kalshi_mid'], weights=hv['n'])
mrow += (f"\\textit{{Obs-weighted mean}} & & & & \\textbf{{{wmean:.2f}}} & "
         f"\\textbf{{{1-wmean:.2f}}} & \\\\\n")
w('tab_main.tex', r"""\begin{tabular}{lccccccc}
\toprule
Contract & N & $k$ & IS$_{K}$ [lo,\,hi] & IS$_{K}$ mid & IS$_{P}$ mid & GG$_{K}$ \\
\midrule
""" + rows + mrow + r"""\bottomrule
\end{tabular}""")

# ---------- Table 4: lead-lag + Granger ----------
ll = pd.read_csv(os.path.join(OUT, 't3_leadlag.csv'))
gr = pd.read_csv(os.path.join(OUT, 't4_granger.csv'))
mrg = ll.merge(gr, on=['pair', 'meeting', 'outcome'])
rows = ''
for _, r in mrg.iterrows():
    rows += (f"{lbl(r['pair'])} & {int(r['peak_lag'])} & {r['ccf_0']:.2f} & {r['leads']} & "
             f"{r['F_kalshi_to_poly']:.1f}{stars(r['p_kalshi_to_poly'])} & "
             f"{r['F_poly_to_kalshi']:.1f}{stars(r['p_poly_to_kalshi'])} \\\\\n")
nK = int((mrg['leads'] == 'Polymarket').sum()); tot = len(mrg)
w('tab_leadlag.tex', r"""\begin{tabular}{lccccc}
\toprule
Contract & Peak lag (h) & CCF(0) & Leader & $F_{K\to P}$ & $F_{P\to K}$ \\
\midrule
""" + rows + r"""\midrule
\multicolumn{6}{l}{\footnotesize Polymarket is the peak-lag leader in """ + f"{nK}/{tot}"
    + r""" pairs. Peak lag $<0$: Polymarket leads. $^{*}p<.10,^{**}p<.05,^{***}p<.01$.} \\
\bottomrule
\end{tabular}""")

# ---------- Table 5: event study (June 2026) ----------
es = pd.read_csv(os.path.join(OUT, 't7_eventstudy.csv'))
cv = pd.read_csv(os.path.join(OUT, 't8_convergence.csv'))
rows = ''
for _, r in es.iterrows():
    rows += (f"{r['window']} & {r['kalshi_mae']*100:.2f} & {r['poly_mae']*100:.2f} & "
             f"{r['poly_minus_kalshi']*100:+.2f} & {r['kalshi_nochange']:.2f} & {r['poly_nochange']:.2f} \\\\\n")
w('tab_event.tex', r"""\begin{tabular}{lccccc}
\toprule
Window & Kalshi MAE (\textcent) & Poly MAE (\textcent) & $\Delta$ (\textcent) & Kalshi P(hold) & Poly P(hold) \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

print('LaTeX tables written to', TEX, ':', sorted(os.listdir(TEX)))
