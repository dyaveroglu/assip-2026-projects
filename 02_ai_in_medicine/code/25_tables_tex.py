#!/usr/bin/env python3
"""Project 02 — LaTeX tables from CSVs."""
import os, pandas as pd
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(HERE,'output','tables'); TEX=os.path.join(HERE,'paper','tables'); os.makedirs(TEX,exist_ok=True)
def star(t):
    a=abs(t); return '***' if a>=2.58 else '**' if a>=1.96 else '*' if a>=1.65 else ''
def w(n,s): open(os.path.join(TEX,n),'w').write(s)

s=pd.read_csv(os.path.join(OUT,'t2_sector.csv'))
rows=''.join(f"{r['sector']} & {int(r['firms'])} & {int(r['aimed_patents'])} & {r['share_patents']*100:.1f}\\% \\\\\n" for _,r in s.iterrows())
w('tab_sector.tex', r"\begin{tabular}{lccc}"+"\n\\toprule\nSector & Firms & Medical-AI patents & Share \\\\\n\\midrule\n"+rows+"\\bottomrule\n\\end{tabular}")

v=pd.read_csv(os.path.join(OUT,'t3_value.csv'))
body=''
for _,r in v.iterrows():
    aimed=f"{r['ln_aimed']:.3f}{star(r['ln_aimed_t'])} ({r['ln_aimed_t']:.2f})"
    inter='' if pd.isna(r.get('ln_aimed_x_ent')) else f"{r['ln_aimed_x_ent']:.3f}{star(r['ln_aimed_x_ent_t'])} ({r['ln_aimed_x_ent_t']:.2f})"
    body+=f"{r['spec']} & {aimed} & {inter} & {int(r['N'])} & {r['r2']:.3f} \\\\\n"
w('tab_value.tex', r"\begin{tabular}{lcccc}"+"\n\\toprule\nSpecification & Medical-AI stock & $\\times$ Entrant & N & Within $R^2$ \\\\\n\\midrule\n"+body+"\\bottomrule\n\\end{tabular}")
print('tex:',os.listdir(TEX))
