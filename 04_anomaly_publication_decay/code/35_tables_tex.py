#!/usr/bin/env python3
"""Project 04 -- Step 35: render booktabs LaTeX tables from the CSV outputs.
Numbers cannot drift: every table body is generated straight from output/tables/*.csv."""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

def stars(t):
    a = abs(t); return '$^{***}$' if a >= 2.58 else '$^{**}$' if a >= 1.96 else '$^{*}$' if a >= 1.65 else ''
def w(n, s): open(os.path.join(TEX, n), 'w').write(s)
def f(x, d=3):
    return '' if (x is None or (isinstance(x, float) and np.isnan(x))) else f'{x:.{d}f}'

# ---------------- Table 1: sample / regime summary -----------------------
t1 = pd.read_csv(os.path.join(OUT, 't1_sumstats.csv'))
facts = pd.read_csv(os.path.join(OUT, 't1_facts.csv')).set_index('stat')['value']
lab = {'insample': 'In-sample', 'postsample': 'Post-sample (pre-pub.)', 'postpub': 'Post-publication'}
rows = ''.join(
    f"{lab[r['regime']]} & {int(r['n_obs']):,} & {int(r['n_anom'])} & {r['mean']:.3f} & "
    f"{r['med']:.3f} & {r['sd']:.2f} & {r['pct_of_insample']:.1f} \\\\\n"
    for _, r in t1.iterrows())
w('tab_sumstats.tex', r"""\begin{tabular}{lcccccc}
\toprule
Regime & Anomaly-months & Anomalies & Mean & Median & SD & \% of in-samp. \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---------------- Table 2: regime means + paired declines ----------------
t2 = pd.read_csv(os.path.join(OUT, 't2_regime_means.csv'))
t2b = pd.read_csv(os.path.join(OUT, 't2_declines.csv'))
r2 = ''.join(
    f"{lab[r['regime']]} & {r['ew_mean']:.3f} & ({r['ew_t']:.1f}) & {r['pooled_mean']:.3f} & "
    f"{r['ew_pct_of_insample']:.1f} \\\\\n" for _, r in t2.iterrows())
dl = ''.join(
    f"{'Post-sample $-$ In-sample' if 'postsample' in r['contrast'] else 'Post-pub. $-$ In-sample'}"
    f" & {r['mean_diff']:.3f}{stars(r['t'])} & ({r['t']:.1f}) & & {r['pct_decline']:.1f}\\% \\\\\n"
    for _, r in t2b.iterrows())
w('tab_regime.tex', r"""\begin{tabular}{lcccc}
\toprule
 & \multicolumn{2}{c}{Equal-weighted} & Pooled & \% of \\
Regime & Mean & ($t$) & Mean & in-samp. \\
\midrule
""" + r2 + r"""\midrule
\multicolumn{5}{l}{\textit{Paired within-anomaly declines}}\\
""" + dl + r"""\bottomrule
\end{tabular}""")

# ---------------- Table 3: progressive panel regressions -----------------
t3 = pd.read_csv(os.path.join(OUT, 't3_panel.csv'))
def col(r):
    return (f"{r['postsample']:.3f}{stars(r['postsample_t'])} & "
            f"{r['postpub']:.3f}{stars(r['postpub_t'])} & "
            f"{f(r['pub_extra'])}{stars(r['pub_extra_t'])}")
body = ''
for _, r in t3.iterrows():
    body += (f"{r['spec']} & {r['postsample']:.3f}{stars(r['postsample_t'])} & "
             f"{r['postpub']:.3f}{stars(r['postpub_t'])} & "
             f"{f(r['pub_extra'])}{stars(r['pub_extra_t'])} & "
             f"{int(r['N']):,} \\\\\n"
             f" & ({r['postsample_t']:.2f}) & ({r['postpub_t']:.2f}) & "
             f"({r['pub_extra_t']:.2f}) & \\\\\n")
w('tab_panel.tex', r"""\begin{tabular}{lcccc}
\toprule
 & Post-sample & Post-pub. & Pub.\ (extra) & N \\
Specification & $b_1$ & $b_2$ & $g_2$ & \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# ---------------- Table 4: heterogeneity (risk vs mispricing) ------------
t4 = pd.read_csv(os.path.join(OUT, 't4_hetero.csv'))
body = ''
for _, r in t4.iterrows():
    body += (f"{r['split']} & {r['postpub']:.3f}{stars(r['postpub_t'])} & "
             f"{r['postpub_x_risk']:.3f}{stars(r['postpub_x_risk_t'])} & "
             f"{r['decay_mispricing']:.3f} & {r['decay_risk']:.3f} & {int(r['N']):,} \\\\\n"
             f" & ({r['postpub_t']:.2f}) & ({r['postpub_x_risk_t']:.2f}) & & & \\\\\n")
w('tab_hetero.tex', r"""\begin{tabular}{lccccc}
\toprule
 & Post-pub. & Post-pub. & \multicolumn{2}{c}{Implied decay} & \\
\cmidrule(lr){4-5}
Risk proxy & (mispr.) & $\times$Risk & Mispr. & Risk & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# ---------------- Table 5: robustness ------------------------------------
t5 = pd.read_csv(os.path.join(OUT, 't5_robust.csv'))
body = ''
for _, r in t5.iterrows():
    ps = f"{r['postsample']:.3f}{stars(r['postsample_t'])}" if not np.isnan(r['postsample_t']) else '--'
    pst = f"({r['postsample_t']:.2f})" if not np.isnan(r['postsample_t']) else ''
    body += (f"{r['spec']} & {ps} & {r['postpub']:.3f}{stars(r['postpub_t'])} & {int(r['N']):,} \\\\\n"
             f" & {pst} & ({r['postpub_t']:.2f}) & \\\\\n")
w('tab_robust.tex', r"""\begin{tabular}{lccc}
\toprule
Specification & Post-sample & Post-pub. & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

print('tex tables written:', sorted(os.listdir(TEX)))
