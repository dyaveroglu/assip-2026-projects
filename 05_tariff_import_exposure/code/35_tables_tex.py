#!/usr/bin/env python3
"""Project 05 - Step 35: render booktabs LaTeX tables from the CSV outputs.
Every number is read from output/tables/*.csv so the paper cannot drift."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

def stars(t):
    a = abs(t)
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
rows = ''.join(f"{{{r['window']}}} & {r['mean']:.4f} & {r['median']:.4f} & {r['t_stat']:.2f} & {r['n']:.0f} \\\\\n"
               for _, r in t2.iterrows())
w('tab_cars.tex', r"""\begin{tabular}{lcccc}
\toprule
Event window & Mean CAR & Median CAR & $t$-stat & N \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- regression coefficient table (shock or pause) ----
def reg_table(csv, fname):
    t = pd.read_csv(os.path.join(OUT, csv))
    labels = [('z_imp_intensity', 'Imported-input intensity'),
              ('z_size', 'ln(Assets)'), ('z_beta', 'Market beta'),
              ('z_cogs_int', 'COGS/Sales'), ('z_lev', 'Leverage'),
              ('z_bm', 'Book/Market'), ('manuf', 'Manufacturing (0/1)')]
    ncol = len(t)
    head = ' & '.join('\\multicolumn{1}{c}{'+s+'}' for s in t['spec'])
    body = ''
    for key, lab in labels:
        if key not in t.columns:
            continue
        coefs, ts = '', ''
        for _, r in t.iterrows():
            if key in r and pd.notna(r[key]):
                coefs += f" & {r[key]:.4f}{stars(r[key+'_t'])}"
                ts += f" & ({r[key+'_t']:.2f})"
            else:
                coefs += ' & '; ts += ' & '
        body += f"{lab}{coefs} \\\\\n{ts} \\\\[3pt]\n"
    nrow = ' & '.join(f"{int(r['N'])}" for _, r in t.iterrows())
    clrow = ' & '.join(f"{int(r['nclust'])}" for _, r in t.iterrows())
    r2row = ' & '.join(f"{r['R2']:.3f}" for _, r in t.iterrows())
    w(fname, r"""\begin{tabular}{l""" + 'c'*ncol + r"""}
\toprule
& """ + head + r""" \\
\cmidrule(lr){2-""" + str(ncol+1) + r"""}
""" + body + r"""\midrule
Observations & """ + nrow + r""" \\
NAICS-3 clusters & """ + clrow + r""" \\
$R^2$ & """ + r2row + r""" \\
\bottomrule
\end{tabular}""")

reg_table('t3_shock.csv', 'tab_shock.tex')
reg_table('t4_pause.csv', 'tab_pause.tex')

# ---- Table 5: robustness ----
t5 = pd.read_csv(os.path.join(OUT, 't5_robust.csv'))
DVMAP = {'car_pre': 'CAR[Mar27,Apr2]', 'car_s0': 'CAR[Apr3]', 'car_s01': 'CAR[Apr3,4]',
         'car_s03': 'CAR[Apr3-8]', 'car_p0': 'CAR[Apr9]', 'car_p01': 'CAR[Apr9,10]',
         'car_round': 'CAR round-trip'}
t5['dv'] = t5['dv'].map(lambda x: DVMAP.get(x, x))
rows = ''.join(f"{r['test']} & {r['dv']} & {r['coef_imp']:.4f}{stars(r['t_imp'])} & "
               f"({r['t_imp']:.2f}) & {int(r['N'])} & {r['R2']:.3f} & {r['cov']} \\\\\n"
               for _, r in t5.iterrows())
w('tab_robust.tex', r"""\begin{tabular}{llccccc}
\toprule
Test & DV & Imp.-intensity coef. & ($t$) & N & $R^2$ & SE \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 6: quartiles ----
t6 = pd.read_csv(os.path.join(OUT, 't6_quartiles.csv'))
rows = ''.join(f"{r['q']} & {int(r['n'])} & {r['intensity']:.4f} & {r['shock']:.4f} & "
               f"{r['pause']:.4f} & {r['round']:.4f} \\\\\n" for _, r in t6.iterrows())
w('tab_quartiles.tex', r"""\begin{tabular}{lccccc}
\toprule
Intensity quartile & N & Mean intensity & Shock CAR & Pause CAR & Round-trip \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

print('LaTeX tables written to', TEX, ':', sorted(os.listdir(TEX)))
