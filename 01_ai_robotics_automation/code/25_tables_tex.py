#!/usr/bin/env python3
"""Project 01 — render LaTeX tables from CSVs."""
import os, pandas as pd
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(HERE,'output','tables'); TEX=os.path.join(HERE,'paper','tables'); os.makedirs(TEX,exist_ok=True)
def star(t):
    a=abs(t); return '***' if a>=2.58 else '**' if a>=1.96 else '*' if a>=1.65 else ''
def w(n,s): open(os.path.join(TEX,n),'w').write(s)

# sumstats
t1=pd.read_csv(os.path.join(OUT,'t1_sumstats.csv'),index_col=0)
LAB={'ln_emp':'ln(Employment)','ln_prod':'ln(Sales/Emp)','roa':'ROA','tobinq':"Tobin's Q",
     'ln_ai':'ln(1+AI patent stock)','ln_rob':'ln(1+Robotics stock)','ai_share':'AI patent share',
     'rob_share':'Robotics patent share','size':'ln(Assets)'}
rows=''.join(f"{LAB.get(i,i)} & {r['count']:.0f} & {r['mean']:.3f} & {r['std']:.3f} & {r['25%']:.3f} & {r['50%']:.3f} & {r['75%']:.3f} \\\\\n" for i,r in t1.iterrows())
w('tab_sumstats.tex', r"\begin{tabular}{lcccccc}"+"\n\\toprule\nVariable & N & Mean & SD & P25 & Median & P75 \\\\\n\\midrule\n"+rows+"\\bottomrule\n\\end{tabular}")

# panel FE
t2=pd.read_csv(os.path.join(OUT,'t2_panelfe.csv'))
outs=list(t2['outcome']); ncol=len(outs)
head=' & '.join(outs)
body=''
for key,lab in [('ln_ai','ln(1+AI patent stock)'),('ln_rob','ln(1+Robotics stock)'),('size','ln(Assets)')]:
    c=' & '.join(f"{r[key]:.4f}{star(r[key+'_t'])}" for _,r in t2.iterrows())
    ts=' & '.join(f"({r[key+'_t']:.2f})" for _,r in t2.iterrows())
    body+=f"{lab} & {c} \\\\\n & {ts} \\\\[3pt]\n"
nrow=' & '.join(f"{int(r['N'])}" for _,r in t2.iterrows())
r2=' & '.join(f"{r['r2']:.3f}" for _,r in t2.iterrows())
w('tab_panelfe.tex', r"\begin{tabular}{l"+"c"*ncol+"}\n\\toprule\n & "+head+r" \\"+"\n\\cmidrule(lr){2-"+str(ncol+1)+"}\n"+body+r"\midrule"+f"\nFirm \\& Year FE & {' & '.join(['Yes']*ncol)} \\\\\nObservations & {nrow} \\\\\nWithin $R^2$ & {r2} \\\\\n"+r"\bottomrule"+"\n\\end{tabular}")
# broadened robotics robustness (B25J + autonomous vehicles + legged robots)
t4=pd.read_csv(os.path.join(OUT,'t4_robbroad.csv'))
outs=list(t4['outcome']); ncol=len(outs); head=' & '.join(outs); body=''
for key,lab in [('ln_ai','ln(1+AI patent stock)'),('ln_robbroad','ln(1+Robotics-broad stock)'),('size','ln(Assets)')]:
    c=' & '.join(f"{r[key]:.4f}{star(r[key+'_t'])}" for _,r in t4.iterrows())
    ts=' & '.join(f"({r[key+'_t']:.2f})" for _,r in t4.iterrows())
    body+=f"{lab} & {c} \\\\\n & {ts} \\\\[3pt]\n"
nrow=' & '.join(f"{int(r['N'])}" for _,r in t4.iterrows())
r2=' & '.join(f"{r['r2']:.3f}" for _,r in t4.iterrows())
w('tab_robbroad.tex', r"\begin{tabular}{l"+"c"*ncol+"}\n\\toprule\n & "+head+r" \\"+"\n\\cmidrule(lr){2-"+str(ncol+1)+"}\n"+body+r"\midrule"+f"\nFirm \\& Year FE & {' & '.join(['Yes']*ncol)} \\\\\nObservations & {nrow} \\\\\nWithin $R^2$ & {r2} \\\\\n"+r"\bottomrule"+"\n\\end{tabular}")
print('tex tables:', os.listdir(TEX))
