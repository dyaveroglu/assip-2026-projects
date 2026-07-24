#!/usr/bin/env python3
"""
Project 14 (WARN) - Step 08: build the firm-event panel + firm fundamentals.

Input : data/interim/warn_all.csv       (all WARN notices, multi-state)
        data/interim/name_matches.csv    (WARN filer name -> permno, confident)
        data/interim/permno_gvkey.csv     (permno -> gvkey link)

Steps :
  1. Attach the matched permno to every WARN notice (confident matches only).
  2. Collapse many job-site notices into firm EVENTS. A firm often files
     several notices across sites within days; overlapping CAR windows would
     double-count the same news. We therefore cluster a firm's notices: a new
     event starts when a notice is >20 calendar days after the current event's
     first notice. event_date = first notice in the cluster; headcount = sum of
     the cluster; n_notices = notices in the cluster.
  3. Pull Compustat fundamentals (comp.funda) for the matched firms and attach
     the most recent pre-event fiscal year: assets, employees, sales, market
     cap, industry. Build firm size and RELATIVE layoff size (cluster headcount
     / total employees).

Output: data/interim/warn_events.csv     (one row per firm-event)
All steps log row counts; nothing fabricated.
"""
import os, time, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs')
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'events_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

def wrds_connect(n=5):
    for i in range(n):
        try:
            return wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
        except Exception as e:
            log(f'WRDS retry {i}: {e}'); time.sleep(5*(i+1))
    raise RuntimeError('WRDS connect failed')

GAP = 20  # calendar-day gap that starts a new firm event

# ---- 1. attach permno --------------------------------------------------
warn = pd.read_csv(os.path.join(INT, 'warn_all.csv'), parse_dates=['notice_date'])
mm = pd.read_csv(os.path.join(INT, 'name_matches.csv'))
conf = mm[mm.auto_confident == 1][['company_raw', 'permno', 'matched_name', 'ticker', 'score']]
w = warn.merge(conf, on='company_raw', how='inner')
w['n_employees'] = pd.to_numeric(w['n_employees'], errors='coerce')
log(f'WARN notices with a confident permno: {len(w)} '
    f'(of {len(warn)}); distinct permnos {w.permno.nunique()}')

# ---- 2. cluster into firm events --------------------------------------
events = []
for permno, g in w.sort_values(['permno', 'notice_date']).groupby('permno'):
    g = g.reset_index(drop=True)
    cur_start = None; head = 0; nnot = 0; states = set(); ltypes = []; tick = None; mname = None
    def flush():
        if cur_start is not None:
            events.append(dict(permno=int(permno), event_date=cur_start,
                               headcount=head, n_notices=nnot,
                               states='|'.join(sorted(states)),
                               layoff_type=(ltypes[0] if ltypes else None),
                               ticker=tick, matched_name=mname))
    for _, r in g.iterrows():
        d = r.notice_date
        if cur_start is None or (d - cur_start).days > GAP:
            flush()
            cur_start = d; head = 0; nnot = 0; states = set(); ltypes = []
            tick = r.ticker; mname = r.matched_name
        head += (r.n_employees if pd.notna(r.n_employees) else 0)
        nnot += 1; states.add(r.state)
        if pd.notna(r.layoff_type): ltypes.append(str(r.layoff_type))
    flush()
ev = pd.DataFrame(events)
ev['event_date'] = pd.to_datetime(ev['event_date'])
ev['headcount'] = pd.to_numeric(ev['headcount'], errors='coerce')
log(f'firm events after clustering (gap>{GAP}d): {len(ev)} events, '
    f'{ev.permno.nunique()} firms; median headcount {ev.headcount.median():.0f}')
log('  events by year: ' + ev.event_date.dt.year.value_counts().sort_index().to_dict().__str__())

# ---- 3. Compustat fundamentals ----------------------------------------
pg = pd.read_csv(os.path.join(INT, 'permno_gvkey.csv'))
pg['gvkey'] = pg['gvkey'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)
ev = ev.merge(pg, on='permno', how='left')
gvkeys = tuple(sorted(ev.gvkey.dropna().unique()))
log(f'events with a gvkey: {ev.gvkey.notna().sum()}; distinct gvkeys {len(gvkeys)}')

db = wrds_connect(); log('connected to WRDS (funda)')
fun = db.raw_sql(f"""
  SELECT gvkey, datadate, fyear, at, emp, sale, prcc_f, csho, sich, fic
  FROM comp.funda
  WHERE gvkey IN {gvkeys} AND datadate >= '2020-01-01'
    AND indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
""")
db.close()
fun['gvkey'] = fun['gvkey'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)
fun['datadate'] = pd.to_datetime(fun['datadate'], errors='coerce')
fun = fun.dropna(subset=['datadate']).sort_values(['gvkey', 'datadate'])
fun.to_csv(os.path.join(RAW, 'comp_funda.csv'), index=False)
log(f'Compustat funda rows: {len(fun)} for {fun.gvkey.nunique()} gvkeys')

# most recent fiscal year with datadate strictly before the event date
def attach_fund(row):
    if pd.isna(row.gvkey): return pd.Series()
    cand = fun[(fun.gvkey == row.gvkey) & (fun.datadate < row.event_date)]
    if cand.empty:
        cand = fun[fun.gvkey == row.gvkey]  # fallback: nearest available
        if cand.empty: return pd.Series()
    r = cand.iloc[-1]
    return pd.Series(dict(at=r['at'], emp=r['emp'], sale=r['sale'], prcc_f=r['prcc_f'],
                          csho=r['csho'], sich=r['sich'], fic=r['fic'],
                          fund_datadate=r['datadate']))
fu = ev.apply(attach_fund, axis=1)
ev = pd.concat([ev, fu], axis=1)

for c in ['at', 'emp', 'sale', 'prcc_f', 'csho', 'sich']:
    ev[c] = pd.to_numeric(ev[c], errors='coerce')
ev['mktcap'] = ev['prcc_f'] * ev['csho']                 # $ millions
ev['ln_at'] = np.log(ev['at'].where(ev['at'] > 0))
ev['ln_mktcap'] = np.log(ev['mktcap'].where(ev['mktcap'] > 0))
ev['ln_headcount'] = np.log(ev['headcount'].where(ev['headcount'] > 0))
ev['tot_emp'] = ev['emp'] * 1000.0                       # emp is in thousands
ev['rel_layoff'] = ev['headcount'] / ev['tot_emp']        # fraction of workforce
ev['rel_layoff'] = ev['rel_layoff'].where(np.isfinite(ev['rel_layoff']))
ev['sic2'] = (ev['sich'] // 100).astype('Int64')
ev['is_tech'] = ev['sic2'].isin([35, 36, 37, 73, 48]).astype(int)  # comp/electronics/software
ev['is_closure'] = ev['layoff_type'].astype(str).str.contains('closure', case=False, na=False).astype(int)
ev['year'] = ev['event_date'].dt.year
ev['us'] = (ev['fic'] == 'USA').astype(int)

ev.to_csv(os.path.join(INT, 'warn_events.csv'), index=False)
log(f'FINAL firm-event panel: {len(ev)} events; with assets {ev["at"].notna().sum()}, '
    f'with emp {ev["emp"].notna().sum()}, with rel_layoff {ev["rel_layoff"].notna().sum()}')
log('  median headcount %.0f, median rel_layoff %.4f, median ln_at %.2f' %
    (ev.headcount.median(), ev.rel_layoff.median(), ev.ln_at.median()))
log('DONE - firm-event panel written to data/interim/warn_events.csv')
logf.close()
