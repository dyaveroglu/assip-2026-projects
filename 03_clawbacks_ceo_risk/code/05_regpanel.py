#!/usr/bin/env python3
"""
Project 03 (Clawbacks) — Step 05: build the firm-year analytical panel.

Treatment (intent-to-treat), fixed at the pre-rule baseline 2022-06-30:
    SP600 (SmallCap)  -> treated = 1  (forced adopter: ex-ante voluntary
                                        clawback rare)
    SP500 (LargeCap)  -> treated = 0  (control: ex-ante voluntary clawback
                                        near-universal by ~2013)
    SP400 (MidCap)    -> kept as a separate robustness group.

Outcomes (CEO risk-taking): R&D/assets, capex/assets, acquisitions/assets,
total investment/assets, stock-return total & idiosyncratic volatility, book
leverage, cash/assets, and (Execucomp) ln(CEO total pay) & equity-pay share.

POST = 1 if fyear >= 2023 (rule adopted 2022-10; listing standards effective
2023-10; policies required by 2023-12-01, so FY2023 is the first treated year).
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
PROC = os.path.join(HERE, 'data', 'processed'); LOG = os.path.join(HERE, 'logs')
for d in (INT, PROC): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'regpanel_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

BASELINE = pd.Timestamp('2022-06-30')
CODE2GRP = {'000003': 'SP500', '024248': 'SP400', '030824': 'SP600'}

# --- treatment assignment from baseline index membership -------------------
idx = pd.read_csv(os.path.join(RAW, 'sp_index_members.csv'), dtype={'gvkey': str, 'gvkeyx': str})
idx['from_dt'] = pd.to_datetime(idx['from_dt'], errors='coerce')
idx['thru_dt'] = pd.to_datetime(idx['thru_dt'], errors='coerce')
active = idx[(idx.from_dt <= BASELINE) &
            (idx.thru_dt.isna() | (idx.thru_dt >= BASELINE))].copy()
active['grp'] = active.gvkeyx.map(CODE2GRP)
# a firm is in exactly one S&P 1500 sub-index at a time; if duplicates, prefer larger cap
order = {'SP500': 0, 'SP400': 1, 'SP600': 2}
active['o'] = active.grp.map(order)
grp = (active.sort_values('o').drop_duplicates('gvkey')[['gvkey', 'grp']])
log(f'baseline (2022-06-30) membership: ' + str(grp.grp.value_counts().to_dict()))

# --- funda -----------------------------------------------------------------
f = pd.read_csv(os.path.join(RAW, 'funda.csv'), dtype={'gvkey': str})
f['datadate'] = pd.to_datetime(f['datadate'])
f = f.sort_values(['gvkey', 'fyear']).drop_duplicates(['gvkey', 'fyear'])
f = f.merge(grp, on='gvkey', how='left')
log(f'funda rows: {len(f)}; with baseline group: {f.grp.notna().sum()}')

# clean numeric
for c in ['at','sale','revt','ni','oibdp','oiadp','capx','xrd','aqc','ppent','ppegt',
          'dltt','dlc','che','csho','prcc_f','ceq','dp','emp','act','lct']:
    f[c] = pd.to_numeric(f[c], errors='coerce')

f = f[f['at'] > 0].copy()
sale = f['sale'].where(f['sale'] > 0)

# --- outcome variables (risk-taking) --------------------------------------
f['rd_at']     = f['xrd'].fillna(0) / f['at']
f['capx_at']   = f['capx'].fillna(0) / f['at']
f['aqc_at']    = f['aqc'].fillna(0) / f['at']
f['invest_at'] = (f['capx'].fillna(0) + f['xrd'].fillna(0) + f['aqc'].fillna(0)) / f['at']
f['book_lev']  = (f['dltt'].fillna(0) + f['dlc'].fillna(0)) / f['at']
f['cash_at']   = f['che'] / f['at']
f['rd_sale']   = f['xrd'].fillna(0) / sale

# --- controls --------------------------------------------------------------
f['size']  = np.log(f['at'].clip(lower=1))
f['me']    = f['csho'] * f['prcc_f']
f['mtb']   = f['me'] / f['ceq'].where(f['ceq'] > 0)
f['roa']   = f['ni'] / f['at']
f['cflow'] = f['oibdp'] / f['at']
f['tang']  = f['ppent'] / f['at']
f = f.sort_values(['gvkey', 'fyear'])
f['sale_gr'] = f.groupby('gvkey')['sale'].pct_change()

# --- merge CRSP volatility (via ccm link, calendar-year match) -------------
ccm = pd.read_csv(os.path.join(RAW, 'ccm_link.csv'), dtype={'gvkey': str})
ccm['linkdt'] = pd.to_datetime(ccm['linkdt'], errors='coerce')
ccm['linkenddt'] = pd.to_datetime(ccm['linkenddt'], errors='coerce')
vol = pd.read_csv(os.path.join(RAW, 'crsp_annual_vol.csv'))
# attach gvkey to each permno-year using the link valid at mid-year
ccm2 = ccm.copy()
ccm2['linkenddt'] = ccm2['linkenddt'].fillna(pd.Timestamp('2099-12-31'))
def link_gvkey(row):
    mid = pd.Timestamp(f"{int(row['fyear'])}-06-30")
    m = ccm2[(ccm2.permno == row['permno']) & (ccm2.linkdt <= mid) & (ccm2.linkenddt >= mid)]
    if len(m): return m.iloc[0]['gvkey']
    return np.nan
vol['gvkey'] = vol.apply(link_gvkey, axis=1)
vol = vol.dropna(subset=['gvkey'])
vol = vol.sort_values('ndays').drop_duplicates(['gvkey', 'fyear'], keep='last')
vsub = vol[['gvkey', 'fyear', 'total_vol', 'idio_vol', 'mean_ret', 'ndays']]
f = f.merge(vsub, on=['gvkey', 'fyear'], how='left')
log(f'merged vol: {f.total_vol.notna().sum()} firm-years have volatility')

# --- merge Execucomp CEO pay ----------------------------------------------
exe = pd.read_csv(os.path.join(RAW, 'execucomp_ceo.csv'), dtype={'gvkey': str})
exe = exe.rename(columns={'year': 'fyear'})
for c in ['total_sec','stock_awards','option_awards','salary','bonus','noneq_incent']:
    exe[c] = pd.to_numeric(exe[c], errors='coerce')
exe = exe.sort_values('total_sec').drop_duplicates(['gvkey', 'fyear'], keep='last')
exe['ln_pay'] = np.log(exe['total_sec'].clip(lower=1) * 1000)  # Execucomp in $000s
exe['equity_share'] = ((exe['stock_awards'].fillna(0) + exe['option_awards'].fillna(0)) /
                       exe['total_sec'].where(exe['total_sec'] > 0))
f = f.merge(exe[['gvkey', 'fyear', 'ln_pay', 'equity_share', 'age']],
            on=['gvkey', 'fyear'], how='left')
log(f'merged CEO pay: {f.ln_pay.notna().sum()} firm-years have CEO pay')

# --- DiD variables ---------------------------------------------------------
f['treat'] = np.where(f.grp == 'SP600', 1, np.where(f.grp == 'SP500', 0, np.nan))
f['post']  = (f['fyear'] >= 2023).astype(int)
f['post24'] = (f['fyear'] >= 2024).astype(int)
f['did']   = f['post'] * f['treat']
f['gvkey_i'] = f['gvkey']
f['fyear_i'] = f['fyear'].astype(int)

# analytical window: 2015-2025 (balanced pre/post; drop sparse 2013-14 & 2026)
f = f[(f.fyear >= 2015) & (f.fyear <= 2025)].copy()

# --- winsorize continuous vars 1/99 ---------------------------------------
OUTC = ['rd_at','capx_at','aqc_at','invest_at','book_lev','cash_at','rd_sale',
        'total_vol','idio_vol','ln_pay','equity_share']
CTRL = ['size','mtb','roa','cflow','tang','sale_gr']
for c in OUTC + CTRL:
    lo, hi = f[c].quantile(0.01), f[c].quantile(0.99)
    f[c] = f[c].clip(lo, hi)

f.to_csv(os.path.join(PROC, 'analytical_panel.csv'), index=False)
log(f'FINAL panel: {len(f)} firm-years, {f.gvkey.nunique()} firms, '
    f'fyear {int(f.fyear.min())}-{int(f.fyear.max())}')
log('  group counts: ' + str(f.grp.value_counts(dropna=False).to_dict()))
main = f[f.treat.notna()]
log(f'  main DiD sample (SP500 vs SP600): {len(main)} firm-years, '
    f'{main.gvkey.nunique()} firms (treat={int(main.treat.sum())} obs)')
logf.close()
