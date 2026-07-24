#!/usr/bin/env python3
"""Project 10 (SVB) — Step 35: render booktabs LaTeX tables from the CSV outputs.
Every number is read from output/tables/*.csv so the paper cannot drift from the
regression output."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

def stars(t):
    a = abs(t)
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s):
    open(os.path.join(TEX, name), 'w').write(s)

# ---- Table 1: summary stats ----
t1 = pd.read_csv(os.path.join(OUT, 't1_sumstats.csv'), index_col=0)
rows = ''.join(f"{i} & {r['count']:.0f} & {r['mean']:.4f} & {r['std']:.4f} & "
               f"{r['25%']:.4f} & {r['50%']:.4f} & {r['75%']:.4f} \\\\\n"
               for i, r in t1.iterrows())
w('tab_sumstats.tex', r"""\begin{tabular}{lcccccc}
\toprule
Variable & N & Mean & SD & P25 & Median & P75 \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 2: CARs by window ----
t3 = pd.read_csv(os.path.join(OUT, 't3_car_windows.csv'))
rows = ''.join(f"{{{r['window']}}} & {r['mean']:.4f} & {r['median']:.4f} & {r['t_stat']:.2f} & {r['n']:.0f} \\\\\n"
               for _, r in t3.iterrows())
w('tab_cars.tex', r"""\begin{tabular}{lcccc}
\toprule
Event window & Mean CAR & Median CAR & $t$-stat & N \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 3 (main): cross-sectional horse race ----
t4 = pd.read_csv(os.path.join(OUT, 't4_crosssec.csv'))
labels = [('z_uninsured_ratio', 'Uninsured deposits / Assets'),
          ('z_sec_loss_eq', 'Securities unreal.\\ loss / Equity'),
          ('z_size', 'ln(Assets)')]
ncol = len(t4)
head = ' & '.join(['\\multicolumn{1}{c}{'+s+'}' for s in t4['spec']])
body = ''
for key, lab in labels:
    coefs, ts = '', ''
    for _, r in t4.iterrows():
        if key in r and pd.notna(r[key]):
            coefs += f" & {r[key]:.4f}{stars(r[key+'_t'])}"
            ts += f" & ({r[key+'_t']:.2f})"
        else:
            coefs += ' & '; ts += ' & '
    body += f"{lab}{coefs} \\\\\n{ts} \\\\[3pt]\n"
nrow = ' & '.join(f"{int(r['N'])}" for _, r in t4.iterrows())
r2row = ' & '.join(f"{r['R2']:.3f}" for _, r in t4.iterrows())
w('tab_main.tex', r"""\begin{tabular}{l""" + 'c'*ncol + r"""}
\toprule
& """ + head + r""" \\
\cmidrule(lr){2-""" + str(ncol+1) + r"""}
""" + body + r"""\midrule
Observations & """ + nrow + r""" \\
$R^2$ & """ + r2row + r""" \\
\bottomrule
\end{tabular}""")
print('LaTeX tables written to', TEX, ':', os.listdir(TEX))
