#!/usr/bin/env python3
"""
Project 07 (BNPL) — Step 15: the honest analysis.

Finding: BNPL complaints surged sector-wide in 2025-26 across ALL products; the
credit-reporting rise is NOT specific to the firm (Affirm) that began furnishing
to the bureaus. We report this faithfully — a reversal of the naive
"furnishing floods the bureaus" hypothesis — and flag the identification problem
(near-simultaneous industry adoption => no clean control) that the student's
hand-collected furnishing dates are needed to solve.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed'); INT = os.path.join(HERE, 'data', 'interim')
OUT = os.path.join(HERE, 'output', 'tables'); os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'analysis_{STAMP}.log'), 'a')
def log(m):
    line=f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

df = pd.read_csv(os.path.join(PROC, 'bnpl_clean.csv'))
df['month'] = pd.PeriodIndex(df['month'], freq='M')
df['cr'] = df['product'].fillna('').str.contains('Credit reporting', case=False).astype(int)
EVENT = pd.Period('2025-04', 'M')
df['post'] = (df.month >= EVENT).astype(int)
PRE_N = df[df.post==0].month.nunique(); POST_N = df[df.post==1].month.nunique()

# T1: Affirm product composition, monthly-average pre vs post (all products surged)
aff = df[df.firm=='Affirm']
comp = aff.groupby(['product','post']).size().unstack(1).fillna(0)
comp.columns = ['pre','post']
comp['pre_permo'] = comp['pre']/PRE_N; comp['post_permo'] = comp['post']/POST_N
comp['growth_x'] = comp['post_permo']/comp['pre_permo'].replace(0,np.nan)
comp = comp.sort_values('post_permo', ascending=False)[['pre_permo','post_permo','growth_x']].head(6)
comp.to_csv(os.path.join(OUT, 't1_composition.csv'))
log('T1 Affirm composition (monthly avg):\n'+comp.round(1).to_string())

# T2: per-firm credit-reporting complaint growth (Affirm not exceptional)
cr = df[df.cr==1].groupby(['firm','month']).size().rename('n').reset_index()
rows=[]
for firm in ['Affirm','Klarna','Sezzle','Zip','Perpay']:
    s = cr[cr.firm==firm].set_index('month')['n']
    pre = s[s.index<EVENT].mean(); post = s[s.index>=EVENT].mean()
    rows.append({'firm':firm,'furnisher':'yes (Apr 2025)' if firm=='Affirm' else 'not confirmed',
                 'cr_pre_permo':pre,'cr_post_permo':post,'growth_x':post/pre if pre else np.nan})
t2 = pd.DataFrame(rows); t2.to_csv(os.path.join(OUT, 't2_firm_growth.csv'), index=False)
log('T2 per-firm CR growth:\n'+t2.round(2).to_string(index=False))

# T3: DiD estimates (report all three; honest)
# (A) within-Affirm, cr x month, log count
gA = aff.groupby(['month','cr']).size().rename('n').reset_index()
MONTHS = pd.period_range('2022-01','2026-06',freq='M')
full = pd.MultiIndex.from_product([MONTHS,[0,1]],names=['month','cr']).to_frame(index=False)
gA = full.merge(gA,on=['month','cr'],how='left').fillna({'n':0})
gA['post']=(gA.month>=EVENT).astype(int); gA['logn']=np.log1p(gA.n); gA['mstr']=gA.month.astype(str)
mA = smf.ols('logn ~ cr + cr:post + C(mstr)', data=gA).fit(cov_type='HC1')
# (B) cross-firm, log CR count, peers as counterfactual
panel=[]
for firm in ['Affirm','Klarna','Sezzle','Zip','Perpay']:
    s=cr[cr.firm==firm].set_index('month')['n']
    for m in pd.period_range('2022-06','2026-06',freq='M'):
        panel.append({'firm':firm,'month':m,'n':s.get(m,0)})
pB=pd.DataFrame(panel); pB['logn']=np.log1p(pB.n); pB['treat']=(pB.firm=='Affirm').astype(int)
pB['post']=(pB.month>=EVENT).astype(int); pB['mstr']=pB.month.astype(str)
pB.to_csv(os.path.join(INT,'panel_crossfirm_crcount.csv'),index=False)
mB = smf.ols('logn ~ treat:post + C(firm) + C(mstr)', data=pB).fit(cov_type='cluster',cov_kwds={'groups':pB.firm})
# (C) same, drop Klarna (tiny pre-base outlier) robustness
pB2=pB[pB.firm!='Klarna']
mB2 = smf.ols('logn ~ treat:post + C(firm) + C(mstr)', data=pB2).fit(cov_type='cluster',cov_kwds={'groups':pB2.firm})
t3 = pd.DataFrame([
    {'spec':'(A) within-Affirm: CR vs other, log count','key':'cr:post','coef':mA.params['cr:post'],'t':mA.tvalues['cr:post'],'N':int(mA.nobs)},
    {'spec':'(B) cross-firm: Affirm vs peers, log CR count','key':'treat:post','coef':mB.params['treat:post'],'t':mB.tvalues['treat:post'],'N':int(mB.nobs)},
    {'spec':'(C) (B) excl. Klarna (tiny base)','key':'treat:post','coef':mB2.params['treat:post'],'t':mB2.tvalues['treat:post'],'N':int(mB2.nobs)},
])
t3.to_csv(os.path.join(OUT,'t3_did.csv'),index=False)
log('T3 DiD (honest):\n'+t3.round(4).to_string(index=False))

# event-study series for the figure: Affirm vs peer-avg CR complaints, indexed to 2025-01
idxbase = pd.Period('2025-01','M')
ser = cr.pivot_table(index='month',columns='firm',values='n',aggfunc='sum').reindex(MONTHS).fillna(0)
ser['PeerAvg'] = ser[['Klarna','Sezzle','Zip','Perpay']].mean(axis=1)
out = ser[['Affirm','PeerAvg']].copy()
out = out[out.index>=pd.Period('2024-01','M')]
out.index = out.index.astype(str)
out.to_csv(os.path.join(INT,'eventstudy_series.csv'))
log('DONE — honest analysis tables written')
logf.close()
