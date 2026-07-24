#!/usr/bin/env python3
"""Project 06 — Step 35: render booktabs LaTeX tables from output/tables/*.csv."""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)
def stars(t):
    a = abs(t); return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(n, s): open(os.path.join(TEX, n), 'w').write(s)
def fnum(x, d=3):
    return '' if pd.isna(x) else f'{x:.{d}f}'

# ---------------- T1 balance
t1 = pd.read_csv(os.path.join(OUT, 't1_balance.csv'))
rows = ''
for _, r in t1.iterrows():
    if r['var'].startswith('N ('):
        rows += (f"{r['var']} & {int(r['treated'])} & {int(r['control'])} & & \\\\\n")
    else:
        st = stars(r['t']) if not pd.isna(r['t']) else ''
        rows += (f"{r['var']} & {fnum(r['treated'])} & {fnum(r['control'])} & "
                 f"{fnum(r['diff'])}{st} & {fnum(r['t'],2)} \\\\\n")
w('tab_balance.tex', r"""\begin{tabular}{p{6.2cm}cccc}
\toprule
& Treated & Control & Diff. & ($t$) \\
& (hard-hit) & & & \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---------------- T2 baseline DiD
t2 = pd.read_csv(os.path.join(OUT, 't2_did.csv'))
rows = ''.join(f"{r['spec']} & {r['coef']:.4f}{stars(r['t'])} & ({r['t']:.2f}) & "
               f"{r['se']:.4f} & {int(r['N'])} \\\\\n" for _, r in t2.iterrows())
w('tab_did.tex', r"""\begin{tabular}{lcccc}
\toprule
Specification & Treat$\times$Post & ($t$) & SE & N \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---------------- T3 belief moderation
t3 = pd.read_csv(os.path.join(OUT, 't3_belief.csv'))
rows = ''.join(f"{r['spec']} & {r['base']:.4f}{stars(r['base_t'])} & ({r['base_t']:.2f}) & "
               f"{r['inter']:.4f}{stars(r['inter_t'])} & ({r['inter_t']:.2f}) & {int(r['N'])} \\\\\n"
               for _, r in t3.iterrows())
w('tab_belief.tex', r"""\begin{tabular}{lccccc}
\toprule
Moderator specification & Treat$\times$Post & ($t$) & $\times$Moderator & ($t$) & N \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---------------- T6 pre-trend
t6 = pd.read_csv(os.path.join(OUT, 't6_pretrend.csv'))
rows = ''.join(f"{r['group']} & {r['pretrend_slope']:.5f}{stars(r['t'])} & ({r['t']:.2f}) & "
               f"{r['se']:.5f} & {int(r['N'])} \\\\\n" for _, r in t6.iterrows())
w('tab_pretrend.tex', r"""\begin{tabular}{lcccc}
\toprule
Sample & Pre-trend slope/mo & ($t$) & SE & N \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")
print('tex tables:', sorted(os.listdir(TEX)))
