#!/usr/bin/env python3
"""
Project 03 (Clawbacks) — Step 00: pull raw data from WRDS.

Design: DiD around SEC Rule 10D-1 (adopted 2022-10-26; NYSE/Nasdaq listing
standards effective 2023-10-02; issuers required to adopt a compliant clawback
policy by 2023-12-01). Because a firm-level hand-collected "did the firm already
have a *voluntary* clawback" flag is not on this WRDS subscription (Audit
Analytics here carries only restatement feeds, not clawback-policy adoption), we
proxy ex-ante clawback status with S&P index membership: by ~2013 voluntary
clawback policies were near-universal among large firms and rare among small
ones (Babenko, Bennett, Bizjak & Coles 2019). So:
    treated  (forced adopter, ex-ante NO clawback)  ~ S&P SmallCap 600
    control  (already-treated, ex-ante clawback)    ~ S&P 500
Membership is fixed at a pre-treatment baseline (2021-12-31) = intent-to-treat.

Pulls:
  (a) comp.idxcst_his  — S&P 500 / MidCap 400 / SmallCap 600 constituents
  (b) comp.funda       — accounting risk-taking inputs (capx, xrd, aqc, at, ...)
  (c) crsp.ccmxpf_lnkhist — gvkey -> permno link
  (d) comp_execucomp.anncomp — CEO total pay + pay mix
  (e) crsp.dsf / dsf_v2 + ff.factors_daily -> firm-year total & idiosyncratic
      return volatility (a CEO risk-taking outcome).

Everything raw & date-stamped to data/raw/. No fabrication; every figure traces
to a WRDS query logged below.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

db = wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
log('connected to WRDS')

# --- (a) S&P index constituents -------------------------------------------
# 000003 = S&P 500 (large); 024248 = S&P MidCap 400; 030824 = S&P SmallCap 600.
idx = db.raw_sql("""
SELECT gvkey, gvkeyx, "from" AS from_dt, thru AS thru_dt
FROM comp.idxcst_his
WHERE gvkeyx IN ('000003','024248','030824')
""")
idx.to_csv(os.path.join(RAW, 'sp_index_members.csv'), index=False)
log(f'(a) index membership rows: {len(idx)} '
    f'(500={ (idx.gvkeyx=="000003").sum() }, 400={ (idx.gvkeyx=="024248").sum() }, '
    f'600={ (idx.gvkeyx=="030824").sum() })')
gvkeys = tuple(sorted(idx.gvkey.dropna().unique()))
log(f'    distinct gvkeys in S&P 1500 union: {len(gvkeys)}')

# --- (b) Compustat annual --------------------------------------------------
funda = db.raw_sql(f"""
SELECT gvkey, datadate, fyear, conm, tic, cik, sich, naicsh,
       at, lt, ceq, csho, prcc_f, sale, revt, ni, oibdp, oiadp,
       capx, xrd, aqc, ppent, ppegt, dltt, dlc, che, act, lct, dp,
       xsga, txt, xint, emp, dvc, dvp, re, seq, wcap, invt, rect
FROM comp.funda
WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
  AND fyear BETWEEN 2013 AND 2026
  AND gvkey IN {gvkeys}
""")
funda.to_csv(os.path.join(RAW, 'funda.csv'), index=False)
log(f'(b) funda rows: {len(funda)} for {funda.gvkey.nunique()} gvkeys, '
    f'fyear {int(funda.fyear.min())}-{int(funda.fyear.max())}')

# --- (c) CCM link gvkey -> permno -----------------------------------------
ccm = db.raw_sql(f"""
SELECT gvkey, lpermno AS permno, linktype, linkprim, linkdt, linkenddt
FROM crsp.ccmxpf_lnkhist
WHERE linktype IN ('LC','LU','LS') AND linkprim IN ('P','C')
  AND gvkey IN {gvkeys}
""")
ccm.to_csv(os.path.join(RAW, 'ccm_link.csv'), index=False)
log(f'(c) ccm link rows: {len(ccm)} for {ccm.gvkey.nunique()} gvkeys, '
    f'{ccm.permno.nunique()} permnos')

# --- (d) Execucomp CEO pay -------------------------------------------------
exe = db.raw_sql(f"""
SELECT gvkey, year, execid, exec_fullname, ceoann, coname, age,
       salary, bonus, stock_awards, option_awards, noneq_incent,
       othcomp, total_sec, total_curr, shrown_tot_pct
FROM comp_execucomp.anncomp
WHERE ceoann = 'CEO' AND year BETWEEN 2013 AND 2025
  AND gvkey IN {gvkeys}
""")
exe.to_csv(os.path.join(RAW, 'execucomp_ceo.csv'), index=False)
log(f'(d) execucomp CEO rows: {len(exe)} for {exe.gvkey.nunique()} gvkeys, '
    f'year {int(exe.year.min())}-{int(exe.year.max())}')

# --- (e) CRSP daily -> firm-year total & idiosyncratic volatility ----------
permnos = tuple(int(x) for x in ccm.permno.dropna().unique())
log(f'(e) pulling daily returns for {len(permnos)} permnos, 2014-2025 ...')
ff = db.raw_sql("SELECT date, mktrf, rf FROM ff.factors_daily "
                "WHERE date BETWEEN '2014-01-01' AND '2025-12-31'")
ff['date'] = pd.to_datetime(ff['date'])

vol_rows = []
for yr in range(2014, 2026):
    if yr <= 2024:
        d = db.raw_sql(f"""
            SELECT permno, date, ret FROM crsp.dsf
            WHERE permno IN {permnos}
              AND date BETWEEN '{yr}-01-01' AND '{yr}-12-31'""")
    else:
        d = db.raw_sql(f"""
            SELECT permno, dlycaldt AS date, dlyret AS ret FROM crsp.dsf_v2
            WHERE permno IN {permnos}
              AND dlycaldt BETWEEN '{yr}-01-01' AND '{yr}-12-31'""")
    d['date'] = pd.to_datetime(d['date'])
    d['ret'] = pd.to_numeric(d['ret'], errors='coerce')
    d = d.dropna(subset=['ret'])
    d = d.merge(ff, on='date', how='left')
    d['exret'] = d['ret'] - d['rf']
    # firm-year aggregates
    g = d.groupby('permno')
    agg = pd.DataFrame({
        'ndays': g['ret'].size(),
        'ret_sd': g['ret'].std(),
        'exret_sd': g['exret'].std(),
        'mean_ret': g['ret'].mean(),
    })
    # idiosyncratic vol = sd(exret) * sqrt(1 - corr(exret, mktrf)^2)
    corr = g.apply(lambda x: np.corrcoef(x['exret'], x['mktrf'])[0, 1]
                   if x['exret'].notna().sum() > 20 and x['mktrf'].notna().sum() > 20
                   else np.nan)
    agg['corr_mkt'] = corr
    agg['fyear'] = yr
    agg = agg.reset_index()
    vol_rows.append(agg)
    log(f'    {yr}: daily rows={len(d)}, firm-years={len(agg)}')

vol = pd.concat(vol_rows, ignore_index=True)
vol = vol[vol['ndays'] >= 60].copy()                 # need a stable annual estimate
vol['total_vol'] = vol['ret_sd'] * np.sqrt(252)
vol['idio_vol'] = vol['exret_sd'] * np.sqrt(1.0 - vol['corr_mkt'].clip(-1, 1)**2) * np.sqrt(252)
vol.to_csv(os.path.join(RAW, 'crsp_annual_vol.csv'), index=False)
log(f'(e) firm-year vol rows (>=60 days): {len(vol)} for {vol.permno.nunique()} permnos; '
    f'mean total_vol={vol.total_vol.mean():.3f}, mean idio_vol={vol.idio_vol.mean():.3f}')

db.close()
log('DONE — raw data written to data/raw/')
logf.close()
