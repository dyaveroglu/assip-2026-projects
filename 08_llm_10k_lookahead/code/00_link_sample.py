#!/usr/bin/env python3
"""
Project 08 — Step 00: build the filing sample and link CIK -> CRSP permno.

Design (placebo / look-ahead contamination):
  gpt-4o (gpt-4o-2024-11-20) has an October-2023 knowledge cutoff. We build two
  windows of 10-K filings whose 12-month post-filing return window falls cleanly
  on one side of that cutoff:

    PRE-cutoff  : filed 2019-01-01 .. 2021-12-31  (forward returns realized
                  2019..2022, BEFORE the cutoff -> the model could have
                  memorized the firm AND its subsequent stock path)
    POST-cutoff : filed 2024-01-01 .. 2024-12-31  (filing AND forward returns
                  entirely AFTER the cutoff -> no look-ahead possible)

Source: the reusable SEC 10-K archive on Hopper (/groups/LGAO/edgar_archive),
whose INDEX.csv was copied to data/raw/INDEX_edgar.csv. Each filing already has a
pre-extracted Item 1A (Risk Factors) section.

This step: filter INDEX to real 10-Ks with a 1A section, take one filing per CIK
per window (latest in-window), link CIK->permno via Compustat comp.company +
crsp.ccmxpf_lnkhist, keep filings with a valid link, and emit a candidate list.
Returns and the final analytic sample are built in 05_returns.py.
"""
import os, sys, datetime, warnings, time
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs')
for d in (RAW, INT, LOG): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'link_sample_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

SEED = 20260707
np.random.seed(SEED)
CAND_PER_WINDOW = 220   # oversample; final ~100/window survives returns filter

# ---------------------------------------------------------------- INDEX -----
idx = pd.read_csv(os.path.join(RAW, 'INDEX_edgar.csv'), dtype=str,
                  engine='python', on_bad_lines='skip')
log(f'INDEX rows read: {len(idx)}')
idx['filing_date'] = pd.to_datetime(idx['filing_date'], errors='coerce')
idx = idx[(idx['status'] == 'ok') & (idx['form'] == '10-K') & idx['filing_date'].notna()]
idx['has1A'] = idx['items_with_text'].fillna('').str.split(',').apply(
    lambda L: '1A' in [x.strip() for x in L])
idx = idx[idx['has1A']].copy()
idx['cik_int'] = pd.to_numeric(idx['cik'], errors='coerce')
idx = idx.dropna(subset=['cik_int'])
idx['cik_int'] = idx['cik_int'].astype('int64')
log(f'10-K + ok + has-1A + valid CIK: {len(idx)} rows, {idx.cik_int.nunique()} CIKs')

def window(df, lo, hi, tag):
    w = df[(df.filing_date >= lo) & (df.filing_date <= hi)].copy()
    # one filing per CIK: the latest within the window
    w = w.sort_values('filing_date').drop_duplicates('cik_int', keep='last')
    w['window'] = tag
    log(f'  window {tag} [{lo}..{hi}]: {len(w)} unique-CIK filings')
    return w

pre  = window(idx, '2019-01-01', '2021-12-31', 'pre')
post = window(idx, '2024-01-01', '2024-12-31', 'post')

# oversampled candidate CIKs per window (extra headroom for link/returns loss)
def draw(w, n):
    n = min(n, len(w))
    return w.sample(n=n, random_state=SEED)
cand = pd.concat([draw(pre, CAND_PER_WINDOW*2), draw(post, CAND_PER_WINDOW*2)],
                 ignore_index=True)
log(f'candidate filings drawn (pre-link): {len(cand)}  '
    f'(pre={ (cand.window=="pre").sum() }, post={ (cand.window=="post").sum() })')

# ---------------------------------------------------- WRDS CIK -> permno -----
import wrds
def connect():
    for i in range(5):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'  wrds retry {i}: {str(e)[:80]}'); time.sleep(5*(i+1))
    raise SystemExit('WRDS connection failed')
db = connect(); log('connected to WRDS')

comp = db.raw_sql("SELECT gvkey, cik FROM comp.company WHERE cik IS NOT NULL")
comp['cik_int'] = pd.to_numeric(comp['cik'], errors='coerce')
comp = comp.dropna(subset=['cik_int']); comp['cik_int'] = comp['cik_int'].astype('int64')
comp = comp.drop_duplicates('cik_int')          # one gvkey per cik (dominant)
log(f'comp.company cik->gvkey rows: {len(comp)}')

lnk = db.raw_sql("""SELECT gvkey, lpermno AS permno, linkdt, linkenddt, linktype, linkprim
                    FROM crsp.ccmxpf_lnkhist
                    WHERE linktype IN ('LC','LU','LS') AND linkprim IN ('P','C')
                       AND lpermno IS NOT NULL""")
lnk['linkdt'] = pd.to_datetime(lnk['linkdt'], errors='coerce')
lnk['linkenddt'] = pd.to_datetime(lnk['linkenddt'], errors='coerce').fillna(pd.Timestamp('2099-12-31'))
lnk['permno'] = lnk['permno'].astype('int64')
log(f'ccm link rows: {len(lnk)}')
db.close()

cand = cand.merge(comp[['cik_int','gvkey']], on='cik_int', how='inner')
log(f'after cik->gvkey merge: {len(cand)} filings ({cand.cik_int.nunique()} CIKs)')

m = cand.merge(lnk, on='gvkey', how='inner')
m = m[(m.linkdt <= m.filing_date) & (m.filing_date <= m.linkenddt)]
m = m.sort_values('linkprim').drop_duplicates(['accession'], keep='first')  # P before C
log(f'after date-valid permno link: {len(m)} filings ({m.permno.nunique()} permnos)')

# finalize candidate pool: keep up to CAND_PER_WINDOW per window
keep = []
for tag in ('pre','post'):
    sub = m[m.window == tag].drop_duplicates('permno')
    sub = sub.sample(n=min(CAND_PER_WINDOW, len(sub)), random_state=SEED)
    keep.append(sub)
cand = pd.concat(keep, ignore_index=True)
cand['id'] = cand['accession'].str.replace('-', '', regex=False)
cols = ['id','cik','cik_int','gvkey','permno','conm','accession','form',
        'filing_date','fiscal_year_end','raw_path','window']
cand = cand[cols].sort_values(['window','filing_date']).reset_index(drop=True)
cand.to_csv(os.path.join(INT, 'candidates.csv'), index=False)
log(f'CANDIDATES written: {len(cand)}  pre={ (cand.window=="pre").sum() } '
    f'post={ (cand.window=="post").sum() }')
log('sample of candidates:\n' +
    cand[['window','filing_date','permno','conm']].head(6).to_string(index=False))
logf.close()
