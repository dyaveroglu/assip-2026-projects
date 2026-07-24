#!/usr/bin/env python3
"""
Project 15 -- Step 35: sample summary statistics from the cached firm x shock panel.

Reads data/interim/firm_cars_by_shock.csv (written by 30_extensions.py) and renders
a descriptive table of the observable firm characteristics used throughout the paper
(N firms per shock, market beta, log market cap, announcement CAR). Every number
traces to output/tables/t13_sumstats.csv. No shock-specific exposure is used.
"""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
fc = pd.read_csv(os.path.join(HERE, 'data', 'interim', 'firm_cars_by_shock.csv'))

order = ['2022-08-09','2022-08-16','2022-11-30','2023-03-09','2023-03-14',
         '2024-02-05','2025-04-03','2025-04-09','2025-07-18','2025-11-03']
fc['date'] = fc['date'].astype(str)
rows = []
for dt in order:
    g = fc[fc.date == dt]
    if g.empty: continue
    rows.append({'date':dt,'event':g.event.iloc[0],'n':len(g),
                 'beta_mean':g.beta.mean(),'beta_sd':g.beta.std(),
                 'logmc_mean':g.logmc.mean(),'ann_sd':g.ann_pct.std()})
t = pd.DataFrame(rows)
t.to_csv(os.path.join(OUT,'t13_sumstats.csv'), index=False)

body = ''.join(
    f"{r['event']} & {int(r['n']):,} & {r['beta_mean']:.2f} & {r['beta_sd']:.2f} & "
    f"{r['logmc_mean']:.2f} & {r['ann_sd']:.2f} \\\\\n" for _,r in t.iterrows())
allrow = (f"\\midrule \\emph{{All firm}}$\\times$\\emph{{shock}} & {len(fc):,} & "
          f"{fc.beta.mean():.2f} & {fc.beta.std():.2f} & {fc.logmc.mean():.2f} & "
          f"{fc.ann_pct.std():.2f} \\\\\n")
open(os.path.join(TEX,'tab_sumstats.tex'),'w').write(
    r"\begin{tabular}{lccccc}"+"\n\\toprule\n"
    r"Shock & $N$ firms & $\overline{\beta}$ & SD($\beta$) & $\overline{\ln\text{MC}}$ & SD CAR[0,+1] \\"
    "\n\\midrule\n"+body+allrow+"\\bottomrule\n\\end{tabular}")
print('t13 summary stats written:', len(t), 'shocks,', len(fc), 'firm x shock obs')
