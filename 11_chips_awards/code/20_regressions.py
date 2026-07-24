#!/usr/bin/env python3
"""
Project 11 (CHIPS awards) -- Step 20: event-time tests + cross-sectional
"scaling with size" regressions, with tables written to output/tables/*.csv.

Q1 (event time):  Do awardee stocks earn a significant abnormal return when the
     CHIPS award is first announced?  -> mean/median CAR by window, t-test,
     sign test, a pre-announcement placebo window.
Q2 (cross-section): Does the announcement return scale with the award's size
     RELATIVE to the firm (award/market cap) and its absolute size (ln award)?
     OLS with HC1-robust SE + Spearman rank correlation (robust to outliers).
     Because N is small (15) and two distressed micro-caps (WOLF, SKYT) are
     large-award/small-cap leverage points, we report drop-one robustness and
     a rank-based test as the conservative headline.

SE = heteroskedasticity-robust (HC1). Nothing winsorized on the DV (the large
WOLF/SKYT reactions are real returns, not errors); instead we show that dropping
them removes the cross-sectional relation -- reported honestly.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(HERE, 'data', 'interim'); PROC = os.path.join(HERE, 'data', 'processed')
OUT = os.path.join(HERE, 'output', 'tables')
os.makedirs(OUT, exist_ok=True); os.makedirs(PROC, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'reg_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

df = pd.read_csv(os.path.join(INT, 'cars.csv'))
# earnings-window confound flag (hand-checked): Amkor reported Q2 earnings on the
# Monday inside its [0,+3] window (announce 2024-07-26 Fri; earnings 2024-07-29).
df['confound'] = df.ticker.isin(['AMKR']).astype(int)
df.to_csv(os.path.join(PROC, 'analytical_panel.csv'), index=False)
log(f'analytical panel: {len(df)} events (adr={df.adr.sum()}, confound-flagged={df.confound.sum()})')

CARW = [('car_m1_1','CAR[-1,+1]'), ('car_0_1','CAR[0,+1]'), ('car_0_3','CAR[0,+3]'),
        ('car_m1_5','CAR[-1,+5]'), ('car_m5_5','CAR[-5,+5]'), ('car_pre','CAR[-10,-3] placebo')]

# ---- Table 1: summary statistics -----------------------------------------
svars = {'car_m1_1':'CAR[-1,+1]', 'car_0_3':'CAR[0,+3]', 'award_usd_m':'Award ($M)',
         'award_pct_mktcap':'Award/Mkt cap (%)', 'mktcap_m':'Mkt cap ($M)',
         'ln_award':'ln(Award $M)', 'ln_mktcap':'ln(Mkt cap $M)', 'beta':'Market beta'}
t1 = df[list(svars)].rename(columns=svars).describe(percentiles=[.25,.5,.75]).T
t1 = t1[['count','mean','std','min','25%','50%','75%','max']]
t1.to_csv(os.path.join(OUT, 't1_sumstats.csv'))
log('Table 1 (summary stats):\n' + t1.round(3).to_string())

# ---- Table 2: mean/median CAR by window, t-test + sign test --------------
rows = []
for w, lbl in CARW:
    s = df[w].dropna(); n = len(s)
    t = s.mean()/(s.std()/np.sqrt(n)) if n > 1 else np.nan
    npos = int((s > 0).sum())
    # exact binomial sign test (two-sided) vs p=0.5
    sign_p = stats.binomtest(npos, n, 0.5).pvalue if n else np.nan
    rows.append({'window':lbl, 'mean':s.mean(), 'median':s.median(), 't_stat':t,
                 'n_pos':npos, 'n':n, 'sign_p':sign_p})
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT, 't2_car_windows.csv'), index=False)
log('Table 2 (CARs by window; t-test of mean=0 and sign test):\n' + t2.round(4).to_string(index=False))

# ---- Table 3: cross-sectional "scaling with size" regressions ------------
def run(formula, data):
    return smf.ols(formula, data=data).fit(cov_type='HC1')

specs = [
    ('(1) ln(Award)',            'car_m1_1 ~ ln_award',                 df),
    ('(2) Award/Mktcap',         'car_m1_1 ~ award_pct_mktcap',         df),
    ('(3) +ln(Mktcap)',          'car_m1_1 ~ award_pct_mktcap + ln_mktcap', df),
    ('(4) Drop Wolfspeed',       'car_m1_1 ~ award_pct_mktcap',         df[df.ticker != 'WOLF']),
    ('(5) Drop ADR (TSM)',       'car_m1_1 ~ award_pct_mktcap',         df[df.adr == 0]),
]
terms = ['award_pct_mktcap','ln_award','ln_mktcap','Intercept']
tbl = []
for name, f, data in specs:
    m = run(f, data.dropna(subset=[f.split('~')[0].strip()]))
    col = {'spec': name, 'N': int(m.nobs), 'R2': m.rsquared}
    for t in terms:
        if t in m.params:
            col[t] = m.params[t]; col[t+'_t'] = m.tvalues[t]
    tbl.append(col)
    log(f'  {name}: '+', '.join(f'{t}={m.params[t]:+.4f}(t={m.tvalues[t]:+.2f})'
        for t in terms if t in m.params))
t3 = pd.DataFrame(tbl); t3.to_csv(os.path.join(OUT, 't3_crosssec.csv'), index=False)
log('Table 3 (cross-section, DV=CAR[-1,+1], HC1):\n' + t3.round(4).to_string(index=False))

# ---- Table 4: robustness -- Spearman rank corr + alt DV + drop confound --
rob = []
for w, lbl in [('car_m1_1','CAR[-1,+1]'), ('car_0_3','CAR[0,+3]')]:
    for xlab, xcol in [('Award/Mktcap','award_pct_mktcap'), ('ln(Award)','ln_award')]:
        d = df.dropna(subset=[w, xcol])
        rho, p = stats.spearmanr(d[xcol], d[w])
        rob.append({'dv':lbl,'x':xlab,'sample':'all (N=%d)'%len(d),'spearman_rho':rho,'p':p})
        d2 = d[d.confound == 0]  # drop Amkor earnings-confounded event
        rho2, p2 = stats.spearmanr(d2[xcol], d2[w])
        rob.append({'dv':lbl,'x':xlab,'sample':'drop confound (N=%d)'%len(d2),'spearman_rho':rho2,'p':p2})
        d3 = d[d.ticker != 'WOLF']  # drop the leverage point
        rho3, p3 = stats.spearmanr(d3[xcol], d3[w])
        rob.append({'dv':lbl,'x':xlab,'sample':'drop Wolfspeed (N=%d)'%len(d3),'spearman_rho':rho3,'p':p3})
t4 = pd.DataFrame(rob); t4.to_csv(os.path.join(OUT, 't4_robust.csv'), index=False)
log('Table 4 (Spearman rank correlation, robustness):\n' + t4.round(4).to_string(index=False))

# ---- Table 5: the event-level CARs (transparency listing) ----------------
t5 = df[['ticker','company','announce_date','award_usd_m','mktcap_m','award_pct_mktcap',
         'beta','car_m1_1','car_0_3','confound','adr']].sort_values('award_pct_mktcap', ascending=False)
t5.to_csv(os.path.join(OUT, 't5_events.csv'), index=False)
log('Table 5 (event-level listing):\n' + t5.round(4).to_string(index=False))
log('DONE -- tables written to output/tables/')
logf.close()
