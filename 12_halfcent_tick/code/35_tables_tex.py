#!/usr/bin/env python3
"""Project 12 (Half-Cent Tick) - Step 35: render booktabs LaTeX tables from CSVs.
Every number is read from output/tables/*.csv so the paper cannot drift."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE,'output','tables'); TEX=os.path.join(HERE,'paper','tables')
os.makedirs(TEX, exist_ok=True)
def w(n,s): open(os.path.join(TEX,n),'w').write(s)
def stars(t):
    a=abs(t); return '***' if a>=2.58 else '**' if a>=1.96 else '*' if a>=1.65 else ''
def esc(s):
    return str(s).replace('$','\\$').replace('#','\\#').replace('%','\\%').replace('&','\\&')

# ---- T1 balance ----
t1=pd.read_csv(os.path.join(OUT,'t1_balance.csv'))
rows=''.join(f"{esc(r['var'])} & {r.treated_mean:.3f} & {r.control_mean:.3f} & {r['diff']:.3f} & {r.t:.2f} \\\\\n"
             for _,r in t1.iterrows())
w('tab_balance.tex', r"""\begin{tabular}{lcccc}
\toprule
 & Treated & Control & Diff. & $t$ \\
Variable (pre-period mean) & (tick-constr.) & (wide) & (T$-$C) & \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- T2 2x2 ----
t2=pd.read_csv(os.path.join(OUT,'t2_did2x2.csv'))
def cell(x): return '' if pd.isna(x) else f"{x:.3f}"
rows=''.join(f"{esc(r.group)} & {cell(r.rqs_pre)} & {cell(r.rqs_post)} & {cell(r.rqs_chg)} & "
             f"{cell(r.dqs_pre)} & {cell(r.dqs_post)} & {cell(r.dqs_chg)} \\\\\n"
             for _,r in t2.iterrows())
w('tab_did2x2.tex', r"""\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{3}{c}{Relative spread (bps)} & \multicolumn{3}{c}{Dollar spread (cents)} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
 & Pre & Post & $\Delta$ & Pre & Post & $\Delta$ \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- T3 main DiD ----
t3=pd.read_csv(os.path.join(OUT,'t3_did_main.csv'))
body=''
for _,r in t3.iterrows():
    body+=f"{esc(r.spec)} & {r.coef:.3f}{stars(r.t)} & ({r.t:.2f}) & {r.se:.3f} & {int(r.N)} & {r.r2:.3f} \\\\\n"
w('tab_did_main.tex', r"""\begin{tabular}{lccccc}
\toprule
Specification & Treated$\times$Post & $t$ & SE & N & $R^2$ \\
\midrule
"""+body+r"""\bottomrule
\end{tabular}""")

# ---- T4 alt outcomes ----
t4=pd.read_csv(os.path.join(OUT,'t4_altoutcomes.csv'))
body=''.join(f"{esc(r.spec)} & {r.coef:.3f}{stars(r.t)} & ({r.t:.2f}) & {r.se:.3f} & {int(r.N)} & {r.r2:.3f} \\\\\n"
             for _,r in t4.iterrows())
w('tab_altoutcomes.tex', r"""\begin{tabular}{lccccc}
\toprule
Outcome / specification & Treated$\times$Post & $t$ & SE & N & $R^2$ \\
\midrule
"""+body+r"""\bottomrule
\end{tabular}""")

# ---- T5 event study ----
t5=pd.read_csv(os.path.join(OUT,'t5_eventstudy.csv'))
body=''
for _,r in t5.iterrows():
    ts = '' if pd.isna(r.t) else f"({r.t:.2f})"
    st = '' if pd.isna(r.t) else stars(r.t)
    coef = '0.000 (base)' if r.evt_week==-1 else f"{r.coef:.3f}{st}"
    body+=f"{int(r.evt_week)} & {coef} & {ts} \\\\\n"
w('tab_eventstudy.tex', r"""\begin{tabular}{lcc}
\toprule
Event week & Treated$\times$week coef. (bps) & $t$ \\
\midrule
"""+body+r"""\bottomrule
\end{tabular}""")

# ---- T6 placebo ----
t6=pd.read_csv(os.path.join(OUT,'t6_placebo.csv'))
body=''.join(f"{esc(r.test)} & {r.coef:.3f}{stars(r.t)} & ({r.t:.2f}) & {r.se:.3f} & {int(r.N)} \\\\\n"
             for _,r in t6.iterrows())
w('tab_placebo.tex', r"""\begin{tabular}{lcccc}
\toprule
Test & Treated$\times$Post$_{\text{fake}}$ & $t$ & SE & N \\
\midrule
"""+body+r"""\bottomrule
\end{tabular}""")

# ---- T7 within-group ----
t7=pd.read_csv(os.path.join(OUT,'t7_withingroup.csv'))
body=''
for _,r in t7.iterrows():
    body+=(f"{esc(r.group)} & {esc(r.measure)} & {r.pre:.3f} & {r.post:.3f} & {r.chg:.3f} & "
           f"{r.pct:.1f}\\% & {r.t:.2f}{stars(r.t)} \\\\\n")
w('tab_withingroup.tex', r"""\begin{tabular}{llccccc}
\toprule
Group & Measure & Pre & Post & $\Delta$ & \%$\Delta$ & paired $t$ \\
\midrule
"""+body+r"""\bottomrule
\end{tabular}""")

# ---- T8 censoring ----
t8=pd.read_csv(os.path.join(OUT,'t8_censoring.csv'))
body=''
for _,r in t8.iterrows():
    body+=(f"{esc(r.group)} & {r.period} & {int(r.n)} & {100*r.share_at_1c:.1f}\\% & "
           f"{100*r.share_subpenny:.1f}\\% & {r.mean_dqs_c:.3f} \\\\\n")
w('tab_censoring.tex', r"""\begin{tabular}{llcccc}
\toprule
Group & Period & Stock-days & Share $=$1.0c & Share $<$1.0c & Mean \$ spread (c) \\
\midrule
"""+body+r"""\bottomrule
\end{tabular}""")

print('LaTeX tables written to', TEX, ':', sorted(os.listdir(TEX)))
