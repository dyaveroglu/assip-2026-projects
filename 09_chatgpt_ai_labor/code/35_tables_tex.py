#!/usr/bin/env python3
"""Project 09 (ChatGPT) — Step 35: render booktabs LaTeX tables from output/tables/*.csv.
Every number in the paper is read from a CSV so the paper cannot drift from the code."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)
def stars(t):
    a=abs(t); return '***' if a>=2.58 else '**' if a>=1.96 else '*' if a>=1.65 else ''
def w(name,s): open(os.path.join(TEX,name),'w').write(s)
def has(f): return os.path.exists(os.path.join(OUT,f))

# ---- Table 1: summary statistics ------------------------------------------
t1=pd.read_csv(os.path.join(OUT,'t1_sumstats.csv'),index_col=0)
rows=''.join(f"{i} & {r['count']:.0f} & {r['mean']:.4f} & {r['std']:.4f} & "
             f"{r['25%']:.4f} & {r['50%']:.4f} & {r['75%']:.4f} \\\\\n" for i,r in t1.iterrows())
w('tab_sumstats.tex', r"""\begin{tabular}{lcccccc}
\toprule
Variable & N & Mean & SD & P25 & Median & P75 \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- Table 2: AIIE-quintile long-short ------------------------------------
t2=pd.read_csv(os.path.join(OUT,'t2_longshort.csv'))
rows=''.join(f"{r['window']} & {r['Q1']*100:.2f} & {r['Q2']*100:.2f} & {r['Q3']*100:.2f} & "
             f"{r['Q4']*100:.2f} & {r['Q5']*100:.2f} & {r['LS_Q5_Q1']*100:.2f}{stars(r['t_LS'])} & "
             f"({r['t_LS']:.2f}) & {r['N']:.0f} \\\\\n" for _,r in t2.iterrows())
w('tab_longshort.tex', r"""\begin{tabular}{lccccccrc}
\toprule
& \multicolumn{5}{c}{Mean CAR by AIIE quintile (\%)} & \multicolumn{2}{c}{Long--short} & \\
\cmidrule(lr){2-6}\cmidrule(lr){7-8}
Event window & Q1 (low) & Q2 & Q3 & Q4 & Q5 (high) & Q5$-$Q1 & $t$ & N \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- Table 3: main cross-section (progressive specs) ----------------------
t3=pd.read_csv(os.path.join(OUT,'t3_crosssec.csv'))
labels=[('z_aiie','AI Industry Exposure (AIIE)'),('z_lnme','ln(ME)'),
        ('z_mom','6-mo momentum'),('z_bm','Book/Market'),('z_lnemp','ln(employees)')]
ncol=len(t3)
head=' & '.join('\\multicolumn{1}{c}{'+s.replace('&','\\&')+'}' for s in t3['spec'])
body=''
for key,lab in labels:
    coefs,ts='',''
    for _,r in t3.iterrows():
        if key in r and pd.notna(r[key]):
            coefs+=f" & {r[key]:.4f}{stars(r[key+'_t'])}"; ts+=f" & ({r[key+'_t']:.2f})"
        else:
            coefs+=' & '; ts+=' & '
    body+=f"{lab}{coefs} \\\\\n{ts} \\\\[3pt]\n"
dvrow=' & '.join(['[0,+10]']*(ncol-1)+['[0,+1]'])
samprow=' & '.join(['All','All','All','Non-fin.','All'][:ncol])
nrow=' & '.join(f"{int(r['N'])}" for _,r in t3.iterrows())
crow=' & '.join(f"{int(r['nclust'])}" for _,r in t3.iterrows())
r2row=' & '.join(f"{r['R2']:.3f}" for _,r in t3.iterrows())
w('tab_main.tex', r"""\begin{tabular}{l"""+'c'*ncol+r"""}
\toprule
& """+head+r""" \\
\cmidrule(lr){2-"""+str(ncol+1)+r"""}
"""+body+r"""\midrule
Event window & """+dvrow+r""" \\
Sample & """+samprow+r""" \\
Industry clusters & """+crow+r""" \\
Observations & """+nrow+r""" \\
$R^2$ & """+r2row+r""" \\
\bottomrule
\end{tabular}""")

# ---- Table 4a: mean CAR by sign bucket ------------------------------------
t4=pd.read_csv(os.path.join(OUT,'t4_buckets.csv'))
piv=t4.pivot(index='window',columns='bucket',values='mean_CAR')
pivt=t4.pivot(index='window',columns='bucket',values='t')
pivn=t4.pivot(index='window',columns='bucket',values='N')
order=['ChatGPT [0,+5]','ChatGPT [0,+10]','GPT-4 [0,+5]']
rows=''
for wn in order:
    rows+=f"{wn}"
    for b in ['supplier','user','substitution']:
        rows+=f" & {piv.loc[wn,b]*100:.2f}{stars(pivt.loc[wn,b])} & ({pivt.loc[wn,b]:.2f})"
    rows+=" \\\\\n"
w('tab_buckets.tex', r"""\begin{tabular}{lcccccc}
\toprule
& \multicolumn{2}{c}{AI supplier} & \multicolumn{2}{c}{AI user} & \multicolumn{2}{c}{Substitution} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}
Event window & CAR\% & $t$ & CAR\% & $t$ & CAR\% & $t$ \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- Table 4b: bucket-dummy sign regression -------------------------------
t4b=pd.read_csv(os.path.join(OUT,'t4_interaction.csv'))
lab={'supplier':'AI supplier (vs.\\ user)','substitution':'Substitution (vs.\\ user)',
     'z_lnme':'ln(ME)','z_mom':'6-mo momentum','Intercept':'Intercept',
     'supplier - substitution (diff)':'Supplier $-$ Substitution'}
rows=''
for _,r in t4b.iterrows():
    nm=lab.get(r['term'],r['term'])
    if pd.notna(r['t']):
        rows+=f"{nm} & {r['coef']*100:.2f}{stars(r['t'])} & ({r['t']:.2f}) \\\\\n"
    else:
        rows+=f"{nm} & {r['coef']*100:.2f} & \\\\\n"
N=int(t4b['N'].iloc[0]); R2=t4b['R2'].iloc[0]; nc=int(t4b['nclust'].iloc[0])
w('tab_sign.tex', r"""\begin{tabular}{lcc}
\toprule
DV = CAR[0,+10] ChatGPT (\%) & Coef.\ (\%) & $t$ \\
\midrule
"""+rows+r"""\midrule
Industry clusters & """+str(nc)+r""" & \\
Observations & """+str(N)+r""" & \\
$R^2$ & """+f"{R2:.3f}"+r""" & \\
\bottomrule
\end{tabular}""")

# ---- Table 5: robustness ---------------------------------------------------
t5=pd.read_csv(os.path.join(OUT,'t5_robust.csv'))
rows=''.join(f"{r['spec']} & {r['coef_aiie']*100:.2f}{stars(r['t_aiie'])} & ({r['t_aiie']:.2f}) & "
             f"{int(r['N'])} & {r['R2']:.3f} \\\\\n" for _,r in t5.iterrows())
w('tab_robust.tex', r"""\begin{tabular}{lcccc}
\toprule
Specification & AIIE coef.\ (\%) & $t$ & N & $R^2$ \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")

# ---- Table 6: EDGAR firm-level 10-K AI-intensity (if present) -------------
if has('t6_edgar.csv') and has('t6_edgar_meta.csv'):
    t6=pd.read_csv(os.path.join(OUT,'t6_edgar.csv'))
    meta=pd.read_csv(os.path.join(OUT,'t6_edgar_meta.csv')).set_index('metric')['value']
    rows=''.join(f"{r['DV']} & {r['coef_ai']*100:.2f}{stars(r['t_ai'])} & ({r['t_ai']:.2f}) & "
                 f"{int(r['N'])} & {r['R2']:.3f} \\\\\n" for _,r in t6.iterrows())
    w('tab_edgar.tex', r"""\begin{tabular}{lcccc}
\toprule
Dependent variable & 10-K AI-intensity coef.\ (\%) & $t$ & N & $R^2$ \\
\midrule
"""+rows+r"""\bottomrule
\end{tabular}""")
    # stash scalars for the text
    with open(os.path.join(TEX,'edgar_scalars.tex'),'w') as f:
        f.write(f"\\newcommand{{\\edgarnfirms}}{{{int(meta['n_firms'])}}}\n")
        f.write(f"\\newcommand{{\\edgarcorr}}{{{meta['corr_aiie_lnai']:.2f}}}\n")
        f.write(f"\\newcommand{{\\edgarshare}}{{{100*meta['share_mention_ai']:.0f}}}\n")
    print('  wrote tab_edgar.tex + edgar_scalars.tex')

print('LaTeX tables written to',TEX,':',sorted(os.listdir(TEX)))
