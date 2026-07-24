#!/usr/bin/env python3
"""Project 07 (BNPL) — Step 35: render booktabs LaTeX tables from CSV outputs."""
import os, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)
def stars(t):
    a=abs(t); return '***' if a>=2.58 else '**' if a>=1.96 else '*' if a>=1.65 else ''
def w(n,s): open(os.path.join(TEX,n),'w').write(s)

SHORT = {'Credit reporting or other personal consumer reports':'Credit reporting',
         'Payday loan, title loan, personal loan, or advance loan':'Personal loan',
         'Debt collection':'Debt collection','Credit card':'Credit card',
         'Checking or savings account':'Deposit account',
         'Money transfer, virtual currency, or money service':'Money transfer'}

# T1 composition
c = pd.read_csv(os.path.join(OUT,'t1_composition.csv'), index_col=0)
rows=''.join(f"{SHORT.get(i,i[:22])} & {r['pre_permo']:.1f} & {r['post_permo']:.1f} & {r['growth_x']:.1f}$\\times$ \\\\\n"
             for i,r in c.iterrows())
w('tab_composition.tex', r"""\begin{tabular}{lccc}
\toprule
Affirm complaint product & Pre (/mo) & Post (/mo) & Growth \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# T2 per-firm growth
g = pd.read_csv(os.path.join(OUT,'t2_firm_growth.csv'))
rows=''.join(f"{r['firm']} & {r['furnisher']} & {r['cr_pre_permo']:.1f} & {r['cr_post_permo']:.1f} & {r['growth_x']:.1f}$\\times$ \\\\\n"
             for _,r in g.iterrows())
w('tab_firm_growth.tex', r"""\begin{tabular}{llccc}
\toprule
BNPL firm & Furnishing? & CR pre (/mo) & CR post (/mo) & Growth \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# T3 DiD
d = pd.read_csv(os.path.join(OUT,'t3_did.csv'))
rows=''.join(f"{r['spec']} & {r['coef']:.4f}{stars(r['t'])} & ({r['t']:.2f}) & {int(r['N'])} \\\\\n"
             for _,r in d.iterrows())
w('tab_did.tex', r"""\begin{tabular}{lccc}
\toprule
Specification & DiD coef. & ($t$) & N \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")
print('BNPL tex tables:', os.listdir(TEX))
