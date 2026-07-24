#!/usr/bin/env python3
"""Project 15 — LaTeX tables from CSVs."""
import os, pandas as pd
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(HERE,'output','tables'); TEX=os.path.join(HERE,'paper','tables'); os.makedirs(TEX,exist_ok=True)
def w(n,s): open(os.path.join(TEX,n),'w').write(s)

a=pd.read_csv(os.path.join(OUT,'t1_atlas.csv')).sort_values('date')
rows=''.join(
    f"{r['event']} & {r['type']} & {r['mkt_ann_pct']:+.2f} & {r['mean_ann']:+.2f} & {r['sd_ann']:.2f} & "
    f"{r['mean_pre']:+.2f} & {r['mean_drift']:+.2f} & {r['reversal_corr']:+.2f} \\\\\n"
    for _,r in a.iterrows())
w('tab_atlas.tex', r"\begin{tabular}{llccccccc}"+"\n\\toprule\n"
  r"Shock & Type & Mkt & \multicolumn{1}{c}{$\overline{CAR}$} & SD & Pre & Drift & Rev. \\"
  "\n & & {\\scriptsize[0,1]} & {\\scriptsize[0,1]} & {\\scriptsize[0,1]} & {\\scriptsize[-5,-1]} & {\\scriptsize[2,10]} & {\\scriptsize corr} \\\\\n\\midrule\n"
  +rows+"\\bottomrule\n\\end{tabular}")

def esc(s):  # LaTeX-safe: escape % and & , wrap | in math
    return str(s).replace('%', r'\%').replace('&', r'\&').replace('|', r'$|$')
m=pd.read_csv(os.path.join(OUT,'t2_meta.csv'))
rows=''.join(f"{esc(r['metric'])} & {r['value']:.3f} \\\\\n" for _,r in m.iterrows())
w('tab_meta.tex', r"\begin{tabular}{lc}"+"\n\\toprule\nMeta-statistic (across shocks) & Value \\\\\n\\midrule\n"+rows+"\\bottomrule\n\\end{tabular}")
print('tex:',os.listdir(TEX))
