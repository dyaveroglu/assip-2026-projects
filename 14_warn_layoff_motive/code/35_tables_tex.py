#!/usr/bin/env python3
"""Project 14 (WARN) - Step 35: render booktabs LaTeX tables from the CSV outputs.
Every number is read from output/tables/*.csv so the paper cannot drift."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

def stars(t):
    a = abs(t) if pd.notna(t) else 0
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)

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
t2 = pd.read_csv(os.path.join(OUT, 't2_car_windows.csv'))
rows = ''.join(f"{{{r['window']}}} & {r['mean']*100:.2f} & {r['median']*100:.2f} & "
               f"{r['t_stat']:.2f}{stars(r['t_stat'])} & {r['pct_pos']*100:.0f}\\% & {r['n']:.0f} \\\\\n"
               for _, r in t2.iterrows())
w('tab_cars.tex', r"""\begin{tabular}{lccccc}
\toprule
Event window & Mean CAR (\%) & Median (\%) & $t$-stat & \% $>0$ & N \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 3: CAR by group ----
t3 = pd.read_csv(os.path.join(OUT, 't3_car_groups.csv'))
rows = ''.join(f"{r['group']} & {r['mean_car']*100:.2f} & {r['median_car']*100:.2f} & "
               f"{r['t_stat']:.2f}{stars(r['t_stat'])} & {r['n']:.0f} \\\\\n"
               for _, r in t3.iterrows())
w('tab_groups.tex', r"""\begin{tabular}{lcccc}
\toprule
Subgroup & Mean CAR[0,+5] (\%) & Median (\%) & $t$-stat & N \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 4 (main): cross-section ----
t4 = pd.read_csv(os.path.join(OUT, 't4_crosssec.csv'))
labels = [('z_rel_layoff', 'Rel. layoff (head/emp), $z$'),
          ('z_ln_headcount', 'ln(Layoff headcount), $z$'),
          ('z_ln_at', 'ln(Assets), $z$'),
          ('is_closure', 'Closure (0/1)'),
          ('is_tech', 'Tech (0/1)')]
ncol = len(t4)
head = ' & '.join(t4['spec'])
body = ''
for key, lab in labels:
    coefs, ts = '', ''
    for _, r in t4.iterrows():
        if key in r and pd.notna(r[key]):
            coefs += f" & {r[key]:.4f}{stars(r[key+'_t'])}"; ts += f" & ({r[key+'_t']:.2f})"
        else:
            coefs += ' & '; ts += ' & '
    body += f"{lab}{coefs} \\\\\n{ts} \\\\[3pt]\n"
yfe = ' & '.join('Yes' if 'FE' in s else 'No' for s in t4['spec'])
nrow = ' & '.join(f"{int(r['N'])}" for _, r in t4.iterrows())
r2row = ' & '.join(f"{r['R2']:.3f}" for _, r in t4.iterrows())
w('tab_main.tex', r"""\begin{tabular}{l""" + 'c'*ncol + r"""}
\toprule
& """ + head + r""" \\
\cmidrule(lr){2-""" + str(ncol+1) + r"""}
""" + body + r"""\midrule
Year FE & """ + yfe + r""" \\
Observations & """ + nrow + r""" \\
$R^2$ & """ + r2row + r""" \\
\bottomrule
\end{tabular}""")

# ---- Table 5: heterogeneity (size interaction highlighted) ----
t5 = pd.read_csv(os.path.join(OUT, 't5_hetero.csv'))
def cell(r, k):
    return (f"{r[k]:.4f}{stars(r[k+'_t'])} ({r[k+'_t']:.2f})"
            if k in r and pd.notna(r[k]) else '--')
rows = ''
for _, r in t5.iterrows():
    # print the interaction term present in this spec
    inter = [c for c in t5.columns if ':' in c and not c.endswith('_t')]
    val = '--'
    for c in inter:
        if pd.notna(r.get(c)):
            val = f"{r[c]:.4f}{stars(r[c+'_t'])} ({r[c+'_t']:.2f})"
    rows += f"{r['spec']} & {cell(r,'z_rel_layoff')} & {val} & {cell(r,'z_ln_at')} & {int(r['N'])} & {r['R2']:.3f} \\\\\n"
w('tab_hetero.tex', r"""\begin{tabular}{lccccc}
\toprule
Specification & Rel. layoff ($z$) & Interaction & ln(Assets) ($z$) & N & $R^2$ \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 6: robustness ----
t6 = pd.read_csv(os.path.join(OUT, 't6_robust.csv'))
rows = ''.join(
    f"{r['spec']} & {r['b_size']:.4f}{stars(r['t_size'])} ({r['t_size']:.2f}) & "
    f"{r['b_rel']:.4f}{stars(r['t_rel'])} ({r['t_rel']:.2f}) & "
    f"{r['b_closure']:.4f}{stars(r['t_closure'])} ({r['t_closure']:.2f}) & "
    f"{int(r['N'])} & {r['R2']:.3f} \\\\\n" for _, r in t6.iterrows())
w('tab_robust.tex', r"""\begin{tabular}{lccccc}
\toprule
Specification & Firm size ($z$) & Rel. layoff ($z$) & Closure & N & $R^2$ \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")
print('LaTeX tables written to', TEX, ':', sorted(os.listdir(TEX)))
