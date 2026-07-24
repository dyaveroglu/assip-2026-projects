#!/usr/bin/env python3
"""Project 03 (Clawbacks) — Step 35: render booktabs LaTeX tables from CSVs.
Every number is read from output/tables/*.csv so the paper cannot drift."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

LAB = {'invest_at':'Investment/Assets','capx_at':'Capex/Assets','rd_at':'R\\&D/Assets',
       'aqc_at':'Acquisitions/Assets','total_vol':'Total return volatility',
       'idio_vol':'Idiosyncratic volatility','book_lev':'Book leverage',
       'cash_at':'Cash/Assets','ln_pay':'ln(CEO total pay)','equity_share':'CEO equity-pay share',
       'size':'Size = ln(Assets)','mtb':'Market-to-book','roa':'ROA','cflow':'Cash flow/Assets',
       'tang':'Tangibility'}

# ---- Table 1: summary statistics by group -------------------------------
t1 = pd.read_csv(os.path.join(OUT, 't1_sumstats.csv'))
rows = ''
for _, r in t1.iterrows():
    rows += (f"{LAB.get(r['var'], r['var'])} & {r['n']:.0f} & {r['mean']:.4f} & {r['sd']:.4f} & "
             f"{r['mean_ctrl']:.4f} & {r['mean_treat']:.4f} & {r['diff']:+.4f} \\\\\n")
w('tab_sumstats.tex', r"""\begin{tabular}{lcccccc}
\toprule
 & N & Mean & SD & \shortstack{Control\\(S\&P 500)} & \shortstack{Treated\\(S\&P 600)} & Diff. \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 2: main DiD across outcomes (preferred spec) -----------------
t2 = pd.read_csv(os.path.join(OUT, 't2_did_main.csv'))
body = ''
for _, r in t2.iterrows():
    body += (f"{LAB.get(r['outcome'], r['outcome'])} & {r['coef']:+.4f}{stars(r['t'])} "
             f"& ({r['t']:+.2f}) & {r['N']:.0f} & {r['r2w']:.3f} \\\\\n")
w('tab_did_main.tex', r"""\begin{tabular}{lcccc}
\toprule
Outcome (DV) & DiD (post$\times$treat) & $t$-stat & N & Within-$R^2$ \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

# ---- Table 3: progressive specifications for headline -------------------
t3 = pd.read_csv(os.path.join(OUT, 't3_progressive.csv'))
meta = pd.read_csv(os.path.join(OUT, 't0_meta.csv'))
hlab = LAB.get(meta.headline_outcome.iloc[0], meta.headline_outcome.iloc[0])
head = ' & '.join('\\multicolumn{1}{c}{'+s+'}' for s in t3['spec'])
coefs = ' & '.join(f"{r['coef']:+.4f}{stars(r['t'])}" for _, r in t3.iterrows())
tsr   = ' & '.join(f"({r['t']:+.2f})" for _, r in t3.iterrows())
nrow  = ' & '.join(f"{int(r['N'])}" for _, r in t3.iterrows())
r2row = ' & '.join(f"{r['r2w']:.3f}" for _, r in t3.iterrows())
firmfe= ' & '.join(['No','Yes','Yes','Yes','Yes'])
ctrl  = ' & '.join(['No','No','Yes','Yes','Yes'])
w('tab_progressive.tex', r"""\begin{tabular}{l""" + 'c'*len(t3) + r"""}
\toprule
& """ + head + r""" \\
\cmidrule(lr){2-""" + str(len(t3)+1) + r"""}
DiD (post$\times$treat) & """ + coefs + r""" \\
 & """ + tsr + r""" \\[2pt]
\midrule
Firm FE & """ + firmfe + r""" \\
Year FE & Yes & Yes & Yes & Yes & Yes \\
Controls & """ + ctrl + r""" \\
Observations & """ + nrow + r""" \\
Within-$R^2$ & """ + r2row + r""" \\
\bottomrule
\end{tabular}""")

# ---- Table 4: robustness ------------------------------------------------
t5 = pd.read_csv(os.path.join(OUT, 't5_robust.csv'))
body = ''
for _, r in t5.iterrows():
    body += f"{r['spec']} & {r['coef']:+.4f}{stars(r['t'])} & ({r['t']:+.2f}) & {r['N']:.0f} \\\\\n"
w('tab_robust.tex', r"""\begin{tabular}{lccc}
\toprule
Specification & DiD coef. & $t$-stat & N \\
\midrule
""" + body + r"""\bottomrule
\end{tabular}""")

print('LaTeX tables written to', TEX, ':', sorted(os.listdir(TEX)))
