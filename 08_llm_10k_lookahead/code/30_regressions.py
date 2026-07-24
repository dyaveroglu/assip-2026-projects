#!/usr/bin/env python3
"""
Project 08 — Step 30: the placebo / look-ahead-contamination regressions.

Core idea. If gpt-4o predicts post-filing returns because it truly READS the risk
factors, then anonymizing firm identity should not change its return-predictive
power, and the power should be similar for pre- and post-cutoff filings. If
instead it REMEMBERS the stock (look-ahead), the RAW score should predict returns
much better than the ANONYMIZED score, and only for PRE-cutoff filings whose
subsequent returns were realized before the model's Oct-2023 knowledge cutoff.

DV: 12-month buy-and-hold abnormal return (BHAR), winsorized 1/99 (robustness:
6m, 3m, raw returns, unwinsorized). Scores z-standardized on the pooled {raw,anon}
distribution. Standard errors: HC1 for cross-sections; clustered by filing id for
the stacked long-form regressions (raw & anon rows of a filing are dependent).

Every table is written to output/tables/*.csv.
"""
import os, datetime, warnings, itertools
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
LOG = os.path.join(HERE, 'logs'); os.makedirs(OUT, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'reg_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

df = pd.read_csv(os.path.join(PROC, 'panel.csv'))
log(f'panel: {len(df)} filings (pre={(df.window=="pre").sum()}, post={(df.window=="post").sum()})')

# =====================================================================
# Table 1 — summary statistics
# =====================================================================
svars = {'score_raw':'gpt-4o risk score (raw text)',
         'score_anon':'gpt-4o risk score (anonymized)',
         'score_gap':'Score gap (raw - anon)',
         'bhar_12':'BHAR 12m', 'bhar_6':'BHAR 6m', 'bhar_3':'BHAR 3m',
         'n_redactions':'Redactions per filing'}
t1 = df[list(svars)].rename(columns=svars).describe(percentiles=[.25,.5,.75]).T
t1 = t1[['count','mean','std','25%','50%','75%']]
t1.to_csv(os.path.join(OUT, 't1_sumstats.csv'))
log('T1 summary:\n'+t1.round(3).to_string())

# =====================================================================
# Table 2 — do raw and anonymized scores agree? (by window)
# =====================================================================
rows = []
for tag, sub in [('Full', df), ('Pre-cutoff', df[df.post==0]), ('Post-cutoff', df[df.post==1])]:
    if len(sub) < 3: continue
    corr = sub['score_raw'].corr(sub['score_anon'])
    gap = (sub['score_raw']-sub['score_anon'])
    n = len(sub)
    t_gap = gap.mean()/(gap.std()/np.sqrt(n)) if gap.std()>0 else np.nan
    rows.append(dict(sample=tag, n=n, corr_raw_anon=corr,
                     mean_raw=sub.score_raw.mean(), mean_anon=sub.score_anon.mean(),
                     mean_gap=gap.mean(), mean_abs_gap=gap.abs().mean(), t_gap=t_gap))
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT, 't2_agreement.csv'), index=False)
log('T2 raw/anon agreement:\n'+t2.round(3).to_string(index=False))

# =====================================================================
# Table 3 — MAIN: return predictability, RAW vs ANON x PRE vs POST
#   4 cross-sectional regressions: bhar_12_w ~ z_score
# =====================================================================
def ols(formula, data):
    return smf.ols(formula, data=data).fit(cov_type='HC1')

cells = [('(1) RAW / pre',  'z_raw',  df[df.post==0]),
         ('(2) ANON / pre', 'z_anon', df[df.post==0]),
         ('(3) RAW / post', 'z_raw',  df[df.post==1]),
         ('(4) ANON / post','z_anon', df[df.post==1])]
rows = []
for name, key, data in cells:
    data = data.dropna(subset=['bhar_12_w', key])
    if len(data) < 3:
        rows.append(dict(spec=name, key=key, coef=np.nan, t=np.nan, N=len(data), r2=np.nan)); continue
    m = ols(f'bhar_12_w ~ {key}', data)
    rows.append(dict(spec=name, key=key, coef=m.params[key], t=m.tvalues[key],
                     se=m.bse[key], N=int(m.nobs), r2=m.rsquared))
t3 = pd.DataFrame(rows); t3.to_csv(os.path.join(OUT, 't3_main.csv'), index=False)
log('T3 MAIN (bhar_12_w ~ z_score; slope per 1-SD of score):\n'+t3.round(4).to_string(index=False))

# =====================================================================
# Table 4 — stacked long form: triple interaction test
#   bhar ~ z_score * raw_dummy * post_dummy  (cluster by filing id)
#   raw_dummy=1 for the RAW row, 0 for the ANON row.
# =====================================================================
long = []
for _, r in df.iterrows():
    long.append(dict(id=r.id, post=r.post, raw=1, z=r.z_raw, bhar=r.bhar_12_w))
    long.append(dict(id=r.id, post=r.post, raw=0, z=r.z_anon, bhar=r.bhar_12_w))
L = pd.DataFrame(long).dropna(subset=['bhar','z'])
L.to_csv(os.path.join(HERE,'data','processed','panel_long.csv'), index=False)

def cl(formula, data):
    return smf.ols(formula, data=data).fit(cov_type='cluster',
                   cov_kwds={'groups': data['id']})
specs4 = {
 '(1) pooled':      'bhar ~ z',
 '(2) x raw':       'bhar ~ z * raw',
 '(3) x post':      'bhar ~ z * post',
 '(4) triple':      'bhar ~ z * raw * post',
}
res4 = {name: cl(f, L) for name, f in specs4.items()}
terms4 = ['z','z:raw','z:post','z:raw:post','raw','post','raw:post','Intercept']
tbl = []
for name, m in res4.items():
    d = {'spec': name, 'N': int(m.nobs), 'r2': m.rsquared}
    for t in terms4:
        if t in m.params.index:
            d[t] = m.params[t]; d[t+'_t'] = m.tvalues[t]
    tbl.append(d)
t4 = pd.DataFrame(tbl); t4.to_csv(os.path.join(OUT, 't4_interaction.csv'), index=False)
log('T4 stacked interactions (cluster by filing):\n'+t4.round(4).to_string(index=False))

# also: within-pre and within-post raw-vs-anon slope difference (z:raw coefficient)
rows = []
for tag, sub in [('Pre-cutoff', L[L.post==0]), ('Post-cutoff', L[L.post==1])]:
    if sub.id.nunique() < 4: continue
    m = cl('bhar ~ z * raw', sub)
    rows.append(dict(sample=tag, N=int(m.nobs), n_filings=sub.id.nunique(),
                     slope_anon=m.params.get('z',np.nan), t_anon=m.tvalues.get('z',np.nan),
                     extra_raw=m.params.get('z:raw',np.nan), t_extra_raw=m.tvalues.get('z:raw',np.nan)))
t4b = pd.DataFrame(rows, columns=['sample','N','n_filings','slope_anon','t_anon','extra_raw','t_extra_raw'])
t4b.to_csv(os.path.join(OUT, 't4b_within.csv'), index=False)
log('T4b within-window raw-vs-anon slope gap (z=anon slope, z:raw=extra raw slope):\n'
    +t4b.round(4).to_string(index=False))

# =====================================================================
# Table 5 — does the raw-anon SCORE GAP predict returns? (pre vs post)
# =====================================================================
rows = []
for tag, sub in [('Pre-cutoff', df[df.post==0]), ('Post-cutoff', df[df.post==1]), ('Full', df)]:
    sub = sub.dropna(subset=['bhar_12_w','z_gap'])
    if len(sub) < 3: continue
    m = ols('bhar_12_w ~ z_gap', sub)
    rows.append(dict(sample=tag, coef=m.params['z_gap'], t=m.tvalues['z_gap'],
                     N=int(m.nobs), r2=m.rsquared))
t5 = pd.DataFrame(rows, columns=['sample','coef','t','N','r2'])
t5.to_csv(os.path.join(OUT, 't5_gap.csv'), index=False)
log('T5 gap predictability (bhar_12_w ~ z_gap):\n'+t5.round(4).to_string(index=False))

# =====================================================================
# Table 6 — robustness: alternate DVs for the key RAW/pre vs ANON/pre slope
# =====================================================================
dvs = [('bhar_12_w','BHAR 12m (w)'), ('bhar_6_w','BHAR 6m (w)'),
       ('bhar_3_w','BHAR 3m (w)'), ('firm_cum_12_w','Raw ret 12m (w)'),
       ('bhar_12','BHAR 12m (raw)')]
rows = []
for dv, lbl in dvs:
    pre = df[df.post==0].dropna(subset=[dv,'z_raw','z_anon'])
    if len(pre) < 4: continue
    mr = ols(f'{dv} ~ z_raw', pre); ma = ols(f'{dv} ~ z_anon', pre)
    rows.append(dict(dv=lbl, N=int(mr.nobs),
                     raw_coef=mr.params['z_raw'], raw_t=mr.tvalues['z_raw'],
                     anon_coef=ma.params['z_anon'], anon_t=ma.tvalues['z_anon']))
t6 = pd.DataFrame(rows, columns=['dv','N','raw_coef','raw_t','anon_coef','anon_t'])
t6.to_csv(os.path.join(OUT, 't6_robust.csv'), index=False)
log('T6 robustness (pre-cutoff, RAW vs ANON slope across DVs):\n'+t6.round(4).to_string(index=False))
log('DONE — tables written to output/tables/')
logf.close()
