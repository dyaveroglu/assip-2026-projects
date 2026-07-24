#!/usr/bin/env python3
"""
Project 14 (WARN) - Step 05: fuzzy-match WARN filer names to public-firm tickers.

WARN notices are filed under the operating name at a job site ("Amgen",
"Lockheed Martin", "Applied Materials, Inc. (557 E. Ca...)"). To run an event
study we need the CRSP permno of the *listed* parent. This script:

  (1) pulls a name universe of U.S. common stocks active 2021-2026 from CRSP
      (crsp.stocknames) plus Compustat legal names (comp.company) linked to
      permno via the CRSP/Compustat link (cached to data/raw/);
  (2) normalises names on both sides (strip legal suffixes / "dba" trade names /
      store-and-site numbers / punctuation only - NOT industry words, so names
      do not collapse to generic tokens);
  (3) fuzzy-matches each distinct WARN filer to the nearest listed firm with
      rapidfuzz token_set_ratio, then keeps a match only when it clears a strict
      score AND a LEADING-ANCHOR test (the WARN filer name and the listed name
      share their first distinctive token). WARN filers overwhelmingly lead with
      the company name and append a location, so the anchor test removes the
      generic-token false positives that a bare token_set match produces.

The automated pass is deliberately HIGH-PRECISION and will still MISS
brand/subsidiary filings ("Pixar" -> Disney, "Optum" -> UnitedHealth) - resolving
those, and verifying these matches, is the student's hand-matching task
(STUDENT_TASKS.md). Every step logs row counts; nothing is fabricated.
"""
import os, re, time, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from rapidfuzz import process, fuzz
import wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs')
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'match_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

def wrds_connect(n=5):
    for i in range(n):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'WRDS connect retry {i}: {e}'); time.sleep(5*(i+1))
    raise RuntimeError('WRDS connect failed')

# ---------------------------------------------------------------------------
# name normalisation (MINIMAL: legal suffixes + dba/site-number/punct only)
# ---------------------------------------------------------------------------
LEGAL = r'\b(incorporated|inc|corporation|corp|company|co|llc|l\.l\.c|lp|l\.p|' \
        r'llp|ltd|limited|plc|the)\b'
def norm(s):
    s = str(s).lower()
    s = re.sub(r'\bdba\b.*$', ' ', s)             # drop "dba ..." trade names
    s = re.sub(r'#?\s*\d[\d\-]*', ' ', s)          # drop store/site numbers
    s = re.sub(r'[^a-z0-9 ]', ' ', s)              # punctuation -> space
    s = re.sub(LEGAL, ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

STOP1 = {'foods','distribution','southern','information','national','general',
         'industries','systems','services','solutions','technologies','energy',
         'financial','capital','holdings','group','healthcare','health','media',
         'transportation','logistics','manufacturing','pharmaceuticals',
         'therapeutics','renewable','international','american','pacific'}
def first_tok(n):
    t = n.split()
    return t[0] if t else ''

# ---------------------------------------------------------------------------
# (1) public-firm name universe from WRDS (cached)
# ---------------------------------------------------------------------------
sn_p = os.path.join(RAW, 'crsp_stocknames.csv')
lk_p = os.path.join(RAW, 'ccm_link.csv')
cp_p = os.path.join(RAW, 'comp_company.csv')
if all(os.path.exists(p) for p in (sn_p, lk_p, cp_p)):
    sn = pd.read_csv(sn_p); link = pd.read_csv(lk_p); comp = pd.read_csv(cp_p)
    log('loaded cached WRDS universe from data/raw/')
else:
    db = wrds_connect(); log('connected to WRDS')
    sn = db.raw_sql("""
      SELECT permno, ticker, comnam, siccd, shrcd, exchcd, namedt, nameenddt
      FROM crsp.stocknames
      WHERE nameenddt >= '2021-06-01' AND namedt <= '2026-07-01'
        AND shrcd IN (10,11) AND exchcd IN (1,2,3)""")
    sn.to_csv(sn_p, index=False)
    link = db.raw_sql("""
      SELECT lpermno AS permno, gvkey, linkprim, linktype, linkdt, linkenddt
      FROM crsp.ccmxpf_lnkhist
      WHERE linktype IN ('LU','LC') AND linkprim IN ('P','C')
        AND (linkenddt >= '2021-06-01' OR linkenddt IS NULL)""")
    link['gvkey'] = link['gvkey'].astype(str).str.zfill(6)
    gvkeys = tuple(str(g) for g in link.gvkey.dropna().unique())
    comp = db.raw_sql(f"SELECT gvkey, conm FROM comp.company WHERE gvkey IN {gvkeys}")
    comp['gvkey'] = comp['gvkey'].astype(str).str.zfill(6)
    link.to_csv(lk_p, index=False); comp.to_csv(cp_p, index=False)
    db.close()
log(f'CRSP stocknames rows: {len(sn)}, {sn.permno.nunique()} permnos; '
    f'CCM link: {len(link)}; Compustat names: {len(comp)}')

link['gvkey'] = link['gvkey'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)
comp['gvkey'] = comp['gvkey'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)
link['linkdt'] = pd.to_datetime(link['linkdt'], errors='coerce')
lk = link.sort_values('linkdt').drop_duplicates('permno', keep='last')[['permno', 'gvkey']]
lk.to_csv(os.path.join(INT, 'permno_gvkey.csv'), index=False)

# latest CRSP name/ticker per permno + Compustat legal names
sn_last = sn.sort_values('nameenddt').drop_duplicates('permno', keep='last')
u1 = sn_last[['permno', 'ticker', 'comnam']].rename(columns={'comnam': 'name'}); u1['nsrc'] = 'crsp'
comp_named = comp.merge(lk, on='gvkey', how='inner')[['permno', 'conm']]
comp_named = comp_named.merge(sn_last[['permno', 'ticker']], on='permno', how='left')
u2 = comp_named.rename(columns={'conm': 'name'})[['permno', 'ticker', 'name']]; u2['nsrc'] = 'comp'
uni = pd.concat([u1, u2], ignore_index=True)
uni['nname'] = uni['name'].map(norm)
uni = uni[uni.nname.str.len() >= 3].drop_duplicates(['permno', 'nname'])
# drop universe names that are a single generic industry token (over-match risk)
uni = uni[~((uni.nname.str.split().str.len() == 1) & (uni.nname.isin(STOP1)))]
log(f'match universe: {len(uni)} (permno,name) pairs, {uni.permno.nunique()} permnos, '
    f'{uni.nname.nunique()} distinct normalised names')

choice_map = {}
for _, r in uni.iterrows():
    choice_map.setdefault(r.nname, r.permno)
choices = list(choice_map.keys())
choice_first = {c: first_tok(c) for c in choices}

# ---------------------------------------------------------------------------
# (3) fuzzy match distinct WARN filer names with anchor guard
# ---------------------------------------------------------------------------
warn = pd.read_csv(os.path.join(INT, 'warn_all.csv'))
wn = pd.DataFrame({'company_raw': warn.company_raw.dropna().unique()})
wn['nname'] = wn.company_raw.map(norm)
wn = wn[wn.nname.str.len() >= 3].copy()
log(f'distinct normalised WARN names to match: {len(wn)}')

THRESH = 92
rows = []
t0 = time.time()
for i, (_, r) in enumerate(wn.iterrows()):
    wnn = r.nname; wf = first_tok(wnn)
    # take top few candidates, then pick best that satisfies the anchor test
    cands = process.extract(wnn, choices, scorer=fuzz.token_set_ratio, limit=8)
    # keep candidates that clear the threshold AND the leading-anchor test, then
    # pick the one whose FULL name is closest (max token_sort_ratio) to break the
    # "Snap" vs "Snap One Holdings" collisions in favour of the exact firm.
    passed = []
    for matched_name, score, _ in cands:
        if score < THRESH:
            continue
        if wf != choice_first[matched_name]:
            continue
        tsort = fuzz.token_sort_ratio(wnn, matched_name)
        passed.append((matched_name, score, tsort))
    if not passed:
        continue
    passed.sort(key=lambda x: (x[2], x[1]), reverse=True)
    matched_name, score, tsort = passed[0]
    permno = choice_map[matched_name]
    rows.append(dict(company_raw=r.company_raw, warn_nname=wnn,
                     matched_name=matched_name, permno=int(permno),
                     score=score, tsort=tsort, n_tokens=len(wnn.split()),
                     matched_tokens=len(matched_name.split())))
    if (i+1) % 600 == 0:
        log(f'  matched {i+1}/{len(wn)} ({time.time()-t0:.0f}s)')

mm = pd.DataFrame(rows)
mm = mm.merge(uni[['permno', 'ticker']].dropna().drop_duplicates('permno'), on='permno', how='left')
mm = mm.merge(uni[['permno', 'name']].drop_duplicates('permno'), on='permno', how='left')
# auto-confident: cleared threshold + anchor already; keep them all as confident
mm['auto_confident'] = 1
mm.to_csv(os.path.join(INT, 'name_matches.csv'), index=False)
log(f'name matches (anchored, score>={THRESH}): {len(mm)} distinct filer names -> '
    f'{mm.permno.nunique()} distinct permnos')
log('DONE - matches written to data/interim/name_matches.csv')
logf.close()
