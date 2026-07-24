#!/usr/bin/env python3
"""Project 11 (CHIPS awards) -- Step 35: render booktabs LaTeX tables from the
CSV outputs so the paper cannot drift from the regression output."""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); TEX = os.path.join(HERE, 'paper', 'tables')
os.makedirs(TEX, exist_ok=True)

def stars(t):
    a = abs(t)
    return '***' if a >= 2.58 else '**' if a >= 1.96 else '*' if a >= 1.65 else ''
def w(name, s): open(os.path.join(TEX, name), 'w').write(s)
def esc(s):  # escape LaTeX-special chars in text labels
    return (str(s).replace('\\', r'\textbackslash ').replace('&', r'\&')
            .replace('%', r'\%').replace('$', r'\$').replace('_', r'\_'))

# ---- Table 1: summary statistics -----------------------------------------
t1 = pd.read_csv(os.path.join(OUT, 't1_sumstats.csv'), index_col=0)
t1.index = [esc(i) for i in t1.index]
rows = ''.join(f"{i} & {r['count']:.0f} & {r['mean']:.3f} & {r['std']:.3f} & "
               f"{r['min']:.3f} & {r['50%']:.3f} & {r['max']:.3f} \\\\\n"
               for i, r in t1.iterrows())
w('tab_sumstats.tex', r"""\begin{tabular}{lcccccc}
\toprule
Variable & N & Mean & SD & Min & Median & Max \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 2: CARs by window ---------------------------------------------
t2 = pd.read_csv(os.path.join(OUT, 't2_car_windows.csv'))
rows = ''.join(f"{{{r['window']}}} & {r['mean']*100:.2f} & {r['median']*100:.2f} & "
               f"{r['t_stat']:.2f}{stars(r['t_stat'])} & {r['n_pos']:.0f}/{r['n']:.0f} & {r['sign_p']:.2f} \\\\\n"
               for _, r in t2.iterrows())
w('tab_cars.tex', r"""\begin{tabular}{lccccc}
\toprule
Event window & Mean CAR (\%) & Median (\%) & $t$-stat & \# pos. & Sign $p$ \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 3: cross-sectional regressions --------------------------------
t3 = pd.read_csv(os.path.join(OUT, 't3_crosssec.csv'))
labels = [('award_pct_mktcap', 'Award / Market cap (\\%)'),
          ('ln_award', 'ln(Award \\$M)'),
          ('ln_mktcap', 'ln(Market cap \\$M)'),
          ('Intercept', 'Constant')]
ncol = len(t3)
# short numbered headers (full spec names live in the table note) to keep width in check
head = ' & '.join('\\multicolumn{1}{c}{(%d)}' % (i+1) for i in range(ncol))
body = ''
for key, lab in labels:
    coefs, ts = '', ''
    for _, r in t3.iterrows():
        if key in r and pd.notna(r[key]):
            coefs += f" & {r[key]:.4f}{stars(r[key+'_t'])}"
            ts += f" & ({r[key+'_t']:.2f})"
        else:
            coefs += ' & '; ts += ' & '
    body += f"{lab}{coefs} \\\\\n{ts} \\\\[3pt]\n"
nrow = ' & '.join(f"{int(r['N'])}" for _, r in t3.iterrows())
r2row = ' & '.join(f"{r['R2']:.3f}" for _, r in t3.iterrows())
w('tab_crosssec.tex', r"""\begin{tabular}{l""" + 'c'*ncol + r"""}
\toprule
& """ + head + r""" \\
\cmidrule(lr){2-""" + str(ncol+1) + r"""}
""" + body + r"""\midrule
Observations & """ + nrow + r""" \\
$R^2$ & """ + r2row + r""" \\
\bottomrule
\end{tabular}""")

# ---- Table 4: Spearman robustness ----------------------------------------
t4 = pd.read_csv(os.path.join(OUT, 't4_robust.csv'))
rows = ''.join(f"{r['dv']} & {r['x']} & {r['sample']} & {r['spearman_rho']:.3f} & {r['p']:.3f} \\\\\n"
               for _, r in t4.iterrows())
w('tab_robust.tex', r"""\begin{tabular}{lllcc}
\toprule
Dep.\ var. & Size measure & Sample & Spearman $\rho$ & $p$-value \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

# ---- Table 5: event-level listing ----------------------------------------
t5 = pd.read_csv(os.path.join(OUT, 't5_events.csv'))
rows = ''
for _, r in t5.iterrows():
    flag = '$^{\\dagger}$' if r['confound'] == 1 else ('$^{a}$' if r['adr'] == 1 else '')
    rows += (f"{r['ticker']}{flag} & {r['announce_date']} & {r['award_usd_m']:,.0f} & "
             f"{r['mktcap_m']:,.0f} & {r['award_pct_mktcap']:.2f} & {r['beta']:.2f} & "
             f"{r['car_m1_1']*100:+.1f} & {r['car_0_3']*100:+.1f} \\\\\n")
w('tab_events.tex', r"""\begin{tabular}{llrrrrrr}
\toprule
Ticker & Date & Award & Mkt cap & Award/cap & $\beta$ & CAR & CAR \\
       &      & (\$M) & (\$M)   & (\%)      &         & [-1,+1] & [0,+3] \\
\midrule
""" + rows + r"""\bottomrule
\end{tabular}""")

print('LaTeX tables written to', TEX, ':', sorted(os.listdir(TEX)))
