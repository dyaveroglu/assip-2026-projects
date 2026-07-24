#!/usr/bin/env python3
"""
Project 07 (BNPL) — Step 10: DiD around the 2025 credit-bureau furnishing go-live.

Two clean designs that difference out the mechanical growth in BNPL complaints:
  (A) WITHIN-AFFIRM: credit-reporting complaints (treated) vs other-product
      complaints (control), monthly, around Affirm's ~Apr-2025 furnishing start.
  (B) CROSS-FIRM: Affirm (treated; began furnishing to Experian) vs peer BNPL
      firms (control), DV = credit-reporting share of monthly complaints.

Event month = 2025-04 (Affirm-Experian furnishing; exact per-firm dates are the
student's hand-collection task). Robustness: 2025-02 (TransUnion).
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
for d in (INT, PROC, OUT): os.makedirs(d, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'did_{STAMP}.log'), 'a')
def log(m):
    line=f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

# --- clean: keep pure-play BNPL, drop false positives ---------------------
df = pd.read_csv(os.path.join(RAW, 'cfpb_bnpl.csv'))
NAME = {'Affirm Holdings, Inc':'Affirm','Klarna AB':'Klarna','Sezzle Inc.':'Sezzle',
        'Zip Co US Inc.':'Zip','Perpay, Inc.':'Perpay'}
df = df[df.company.isin(NAME)].copy()
df['firm'] = df.company.map(NAME)
df['dt'] = pd.to_datetime(df.date_received, errors='coerce', utc=True)
df = df.dropna(subset=['dt'])
df['month'] = df.dt.dt.to_period('M')
df['cr'] = df['product'].fillna('').str.contains('Credit reporting', case=False).astype(int)
df.to_csv(os.path.join(PROC, 'bnpl_clean.csv'), index=False)
log(f'clean sample: {len(df)} complaints, firms={sorted(df.firm.unique())}, '
    f'CR share overall={df.cr.mean():.3f}')

EVENT = pd.Period('2025-04', 'M')
MONTHS = pd.period_range('2022-01', '2026-06', freq='M')

# --- (A) within-Affirm: cr x month panel of counts ------------------------
aff = df[df.firm == 'Affirm']
gA = (aff.groupby(['month','cr']).size().rename('n').reset_index())
full = pd.MultiIndex.from_product([MONTHS, [0,1]], names=['month','cr']).to_frame(index=False)
gA = full.merge(gA, on=['month','cr'], how='left').fillna({'n':0})
gA['post'] = (gA.month >= EVENT).astype(int)
gA['logn'] = np.log1p(gA.n)
gA['mstr'] = gA.month.astype(str)
gA.to_csv(os.path.join(INT, 'panelA_affirm.csv'), index=False)
mA = smf.ols('logn ~ cr + cr:post + C(mstr)', data=gA).fit(cov_type='HC1')
mA_p = smf.poisson('n ~ cr + cr:post + C(mstr)', data=gA).fit(disp=0)
log(f'(A) within-Affirm DiD  cr:post  OLS coef={mA.params["cr:post"]:+.4f} (t={mA.tvalues["cr:post"]:.2f}); '
    f'Poisson coef={mA_p.params["cr:post"]:+.4f} (z={mA_p.tvalues["cr:post"]:.2f})')

# --- (B) cross-firm: firm x month, DV = cr share --------------------------
gB = df.groupby(['firm','month']).agg(n=('cr','size'), cr=('cr','sum')).reset_index()
gB = gB[gB.n >= 5]                                   # need a stable denominator
gB['cr_share'] = gB.cr / gB.n
gB['treat'] = (gB.firm == 'Affirm').astype(int)
gB['post'] = (gB.month >= EVENT).astype(int)
gB['mstr'] = gB.month.astype(str)
gB.to_csv(os.path.join(INT, 'panelB_crossfirm.csv'), index=False)
mB = smf.ols('cr_share ~ treat:post + C(firm) + C(mstr)', data=gB).fit(cov_type='cluster',
              cov_kwds={'groups': gB.firm})
log(f'(B) cross-firm DiD  treat:post coef={mB.params["treat:post"]:+.4f} '
    f'(t={mB.tvalues["treat:post"]:.2f}), N={int(mB.nobs)}')

# --- tables ---------------------------------------------------------------
# T1: pre/post 2x2 means (within-Affirm counts)
piv = gA.pivot_table(index='post', columns='cr', values='n', aggfunc='mean')
piv.index = ['Pre (before 2025-04)','Post']; piv.columns = ['Other complaints','Credit-reporting']
piv['DiD row diff'] = piv['Credit-reporting'] - piv['Other complaints']
piv.to_csv(os.path.join(OUT, 't1_affirm_2x2.csv'))
log('T1 within-Affirm mean monthly counts:\n' + piv.round(1).to_string())

# T2: DiD coefficient table
def row(name, m, key):
    return {'model':name, 'coef':m.params[key], 't':m.tvalues[key], 'N':int(m.nobs),
            'r2': getattr(m,'rsquared', np.nan)}
t2 = pd.DataFrame([
    row('(A) within-Affirm, log count (OLS)', mA, 'cr:post'),
    row('(A) within-Affirm, count (Poisson)', mA_p, 'cr:post'),
    row('(B) cross-firm, CR share (OLS)', mB, 'treat:post'),
])
t2.to_csv(os.path.join(OUT, 't2_did.csv'), index=False)
log('T2 DiD estimates:\n' + t2.round(4).to_string(index=False))

# robustness: event = 2025-02
for ev in [pd.Period('2025-02','M')]:
    gA2 = gA.copy(); gA2['post'] = (gA2.month >= ev).astype(int)
    m2 = smf.ols('logn ~ cr + cr:post + C(mstr)', data=gA2).fit(cov_type='HC1')
    log(f'robustness event={ev}: within-Affirm cr:post={m2.params["cr:post"]:+.4f} (t={m2.tvalues["cr:post"]:.2f})')
log('DONE')
logf.close()
