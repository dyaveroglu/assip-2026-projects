#!/usr/bin/env python3
"""
Project 08 — Step 35: render booktabs LaTeX tables from output/tables/*.csv.
Every number is read from a CSV so the paper cannot drift from the regressions.
"""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

def stars(t):
    if pd.isna(t): return ''
    a = abs(t)
    return '***' if a>=2.58 else '**' if a>=1.96 else '*' if a>=1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)
def f(x, d=3):
    return '' if pd.isna(x) else f'{x:.{d}f}'

def esc(s):  # escape LaTeX-special chars in row labels
    s = str(s)
    for a,b in [('\\','\\textbackslash '),('#','\\#'),('%','\\%'),('&','\\&'),('_','\\_')]:
        s = s.replace(a,b)
    return s

# ---- T1 summary stats ----
t1 = pd.read_csv(os.path.join(OUT,'t1_sumstats.csv'), index_col=0)
rows=''.join(f"{esc(i)} & {r['count']:.0f} & {f(r['mean'])} & {f(r['std'])} & "
             f"{f(r['25%'])} & {f(r['50%'])} & {f(r['75%'])} \\\\\n" for i,r in t1.iterrows())
w('tab_sumstats.tex', r"""\begin{tabular}{lcccccc}
\toprule
Variable & N & Mean & SD & P25 & Median & P75 \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- T2 agreement ----
t2 = pd.read_csv(os.path.join(OUT,'t2_agreement.csv'))
rows=''.join(f"{r['sample']} & {r['n']:.0f} & {f(r['corr_raw_anon'])} & {f(r['mean_raw'],1)} & "
             f"{f(r['mean_anon'],1)} & {f(r['mean_gap'],2)} & {f(r['mean_abs_gap'],2)} & "
             f"{f(r['t_gap'],2)} \\\\\n" for _,r in t2.iterrows())
w('tab_agreement.tex', r"""\begin{tabular}{lccccccc}
\toprule
Sample & N & Corr(raw,anon) & Mean raw & Mean anon & Mean gap & Mean $|$gap$|$ & $t$(gap) \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- T3 main 4-cell ----
t3 = pd.read_csv(os.path.join(OUT,'t3_main.csv'))
head=' & '.join('\\multicolumn{1}{c}{'+s.replace('/','/').replace('_','\\_')+'}' for s in t3['spec'])
coefs=' & '.join(f"{f(r['coef'],4)}{stars(r['t'])}" for _,r in t3.iterrows())
tsr =' & '.join(f"({f(r['t'],2)})" for _,r in t3.iterrows())
nrow=' & '.join(f"{int(r['N'])}" for _,r in t3.iterrows())
r2=' & '.join(f"{f(r['r2'],3)}" for _,r in t3.iterrows())
w('tab_main.tex', r"""\begin{tabular}{l"""+'c'*len(t3)+r"""}
\toprule
& """+head+r""" \\
\cmidrule(lr){2-"""+str(len(t3)+1)+r"""}
gpt-4o risk score ($z$) & """+coefs+r""" \\
 & """+tsr+r""" \\[3pt]
\midrule
Observations & """+nrow+r""" \\
$R^2$ & """+r2+r""" \\
\bottomrule
\end{tabular}""")

# ---- T4 interaction ----
t4 = pd.read_csv(os.path.join(OUT,'t4_interaction.csv'))
labels=[('z','Risk score ($z$)'),('z:raw','$z\\times$ Raw'),('z:post','$z\\times$ Post'),
        ('z:raw:post','$z\\times$ Raw $\\times$ Post')]
body=''
for key,lab in labels:
    cs=''; ts=''
    for _,r in t4.iterrows():
        if key in r and pd.notna(r.get(key)):
            cs+=f" & {f(r[key],4)}{stars(r.get(key+'_t'))}"; ts+=f" & ({f(r.get(key+'_t'),2)})"
        else: cs+=' & '; ts+=' & '
    body+=f"{lab}{cs} \\\\\n{ts} \\\\[2pt]\n"
nrow=' & '.join(f"{int(r['N'])}" for _,r in t4.iterrows())
r2=' & '.join(f"{f(r['r2'],3)}" for _,r in t4.iterrows())
hd=' & '.join('\\multicolumn{1}{c}{'+s+'}' for s in t4['spec'])
w('tab_interaction.tex', r"""\begin{tabular}{l"""+'c'*len(t4)+r"""}
\toprule
& """+hd+r""" \\
\cmidrule(lr){2-"""+str(len(t4)+1)+r"""}
"""+body+r"""\midrule
Observations & """+nrow+r""" \\
$R^2$ & """+r2+r""" \\
\bottomrule
\end{tabular}""")

# ---- T4b within ----
t4b = pd.read_csv(os.path.join(OUT,'t4b_within.csv'))
rows=''.join(f"{r['sample']} & {int(r['n_filings'])} & {f(r['slope_anon'],4)}{stars(r['t_anon'])} & "
             f"({f(r['t_anon'],2)}) & {f(r['extra_raw'],4)}{stars(r['t_extra_raw'])} & "
             f"({f(r['t_extra_raw'],2)}) \\\\\n" for _,r in t4b.iterrows())
w('tab_within.tex', r"""\begin{tabular}{lccccc}
\toprule
Sample & Filings & Anon slope & $t$ & Extra RAW slope & $t$ \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- T5 gap ----
t5 = pd.read_csv(os.path.join(OUT,'t5_gap.csv'))
rows=''.join(f"{r['sample']} & {int(r['N'])} & {f(r['coef'],4)}{stars(r['t'])} & ({f(r['t'],2)}) & "
             f"{f(r['r2'],3)} \\\\\n" for _,r in t5.iterrows())
w('tab_gap.tex', r"""\begin{tabular}{lcccc}
\toprule
Sample & N & Score-gap slope ($z$) & $t$ & $R^2$ \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- T6 robustness ----
t6 = pd.read_csv(os.path.join(OUT,'t6_robust.csv'))
rows=''.join(f"{r['dv']} & {int(r['N'])} & {f(r['raw_coef'],4)}{stars(r['raw_t'])} & ({f(r['raw_t'],2)}) & "
             f"{f(r['anon_coef'],4)}{stars(r['anon_t'])} & ({f(r['anon_t'],2)}) \\\\\n"
             for _,r in t6.iterrows())
w('tab_robust.tex', r"""\begin{tabular}{lccccc}
\toprule
Dependent variable & N & RAW slope & $t$ & ANON slope & $t$ \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

print('LaTeX tables written to', TEX, ':', sorted(os.listdir(TEX)))
