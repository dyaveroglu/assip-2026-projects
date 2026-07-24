#!/usr/bin/env python3
"""
Project 10 (SVB) — Step 05: build the 2022Q4 bank regulatory panel (CORRECT).

Design decision (validated by diagnostics):
  * ASSETS / EQUITY / SECURITIES come from the CONSOLIDATED FR Y-9C
    (bank.wrds_holding_bhck_*), keyed by the holding-company RSSD.  Summing
    subsidiary Call Reports double-counts multi-tier holdcos (NYCB summed to
    $270B vs true consolidated $90.1B), so we do NOT sum for these.
  * UNINSURED DEPOSITS (RCON5597) exists only in bank-level Call Reports, so we
    take the LEAD subsidiary bank (largest RCON2170) of each holder.  Summing
    across a holder's subsidiaries is provided as a robustness column; correctly
    aggregating multi-bank holdcos is the student's hand-verification task.

Identifying variables (2022Q4):
  uninsured deposits (lead bank)  RCON5597 / consolidated assets  -> uninsured_ratio
  HTM unrealized loss             BHCK1754 - BHCK1771 (consolidated)
  AFS unrealized loss             BHCK1772 - BHCK1773 (consolidated)
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, wrds

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs'); os.makedirs(INT, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'regpanel_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

db = wrds.Connection(wrds_username=os.environ['WRDS_USERNAME'])
log('connected')

# --- all-bank Call Report cells (2022Q4) ----------------------------------
c1 = db.raw_sql("""SELECT rssd9001, rcon5597, rcon1754, rcon1773
                   FROM bank.wrds_call_rcon_1 WHERE wrdsreportdate='2022-12-31'""")
c2 = db.raw_sql("""SELECT rssd9001, rcon1771, rcon1772, rcon2170, rcon3210
                   FROM bank.wrds_call_rcon_2 WHERE wrdsreportdate='2022-12-31'""")
call = c1.merge(c2, on='rssd9001', how='outer')
for c in ['rcon5597','rcon1754','rcon1773','rcon1771','rcon1772','rcon2170','rcon3210']:
    call[c] = pd.to_numeric(call[c], errors='coerce')
call['rssd9001'] = call.rssd9001.astype('int64')
log(f'all-bank call rows: {len(call)}')

# --- ultimate holder via parent chain (non-premium relationships) ----------
rel = db.raw_sql("""SELECT id_rssd_offspring AS child, id_rssd_parent AS parent, date_start
                    FROM bank.wrds_struct_relationships
                    WHERE date_start <= '2022-12-31' AND (date_end >= '2022-12-31' OR date_end IS NULL)""")
rel = rel.dropna(subset=['child','parent'])
rel['child'] = rel.child.astype('int64'); rel['parent'] = rel.parent.astype('int64')
rel = rel.sort_values('date_start').drop_duplicates('child', keep='last')
c2p = dict(zip(rel.child, rel.parent))
def ultimate(r, cap=15):
    seen = set()
    while r in c2p and r not in seen and cap > 0:
        seen.add(r); r = c2p[r]; cap -= 1
    return r
call['holder'] = call.rssd9001.map(ultimate)

# lead subsidiary bank (max assets) per holder -> uninsured deposits
call_sorted = call.sort_values('rcon2170', ascending=False)
lead = call_sorted.drop_duplicates('holder', keep='first').set_index('holder')
uninsured_sum = call.groupby('holder')['rcon5597'].sum()   # robustness only

# --- consolidated FR Y-9C for the CRSP-linked holders ----------------------
link = pd.read_csv(os.path.join(RAW, 'bank_crsp_link_active.csv'))[['rssd9001','permco','name','inst_type']]
link['rssd9001'] = link.rssd9001.astype('int64')
uni = pd.read_csv(os.path.join(RAW, 'bank_universe.csv'))[['permno','permco','ticker','comnam']]
holders = tuple(int(x) for x in link.rssd9001.dropna().unique())

y1 = db.raw_sql(f"""SELECT rssd9001, bhck1754, bhck1773 FROM bank.wrds_holding_bhck_1
                    WHERE rssd9999='2022-12-31' AND rssd9001 IN {holders}""")
y2 = db.raw_sql(f"""SELECT rssd9001, bhck1771, bhck1772, bhck2170, bhck3210 FROM bank.wrds_holding_bhck_2
                    WHERE rssd9999='2022-12-31' AND rssd9001 IN {holders}""")
y9c = y1.merge(y2, on='rssd9001', how='outer')
for c in ['bhck1754','bhck1773','bhck1771','bhck1772','bhck2170','bhck3210']:
    y9c[c] = pd.to_numeric(y9c[c], errors='coerce')
y9c['rssd9001'] = y9c.rssd9001.astype('int64')
y9c = y9c.drop_duplicates('rssd9001')
log(f'Y-9C holders with data: {len(y9c)}')

# --- assemble panel: one row per holder -----------------------------------
rows = []
for _, lk in link.iterrows():
    h = lk.rssd9001
    yy = y9c[y9c.rssd9001 == h]
    if len(yy):                                   # consolidated Y-9C available
        assets = yy.bhck2170.iloc[0]; equity = yy.bhck3210.iloc[0]
        htm_loss = yy.bhck1754.iloc[0] - yy.bhck1771.iloc[0]
        afs_loss = yy.bhck1772.iloc[0] - yy.bhck1773.iloc[0]
        src = 'Y9C'
    elif h in lead.index:                         # standalone bank -> own Call
        r = lead.loc[h]
        assets = r.rcon2170; equity = r.rcon3210
        htm_loss = r.rcon1754 - r.rcon1771; afs_loss = r.rcon1772 - r.rcon1773
        src = 'CALL'
    else:
        continue
    uninsured = lead.loc[h].rcon5597 if h in lead.index else np.nan
    rows.append(dict(holder=h, permco=lk.permco, name=lk['name'], inst_type=lk.inst_type,
                     assets=assets, equity=equity, htm_unreal_loss=htm_loss,
                     afs_unreal_loss=afs_loss, uninsured=uninsured,
                     uninsured_sum=uninsured_sum.get(h, np.nan), src=src))
p = pd.DataFrame(rows)
p = p.merge(uni, on='permco', how='inner')
for col in ['assets','equity','htm_unreal_loss','afs_unreal_loss','uninsured','uninsured_sum']:
    p[col] = pd.to_numeric(p[col], errors='coerce')
p = p[(p.assets > 0) & (p.equity > 0)]
p['sec_unreal_loss'] = p.htm_unreal_loss + p.afs_unreal_loss
p['uninsured_ratio'] = p.uninsured / p.assets
p['htm_loss_eq']     = p.htm_unreal_loss / p.equity
p['sec_loss_eq']     = p.sec_unreal_loss / p.equity
p['size']            = np.log(p.assets)
p = p.sort_values('assets', ascending=False).drop_duplicates('permno')
p.to_csv(os.path.join(INT, 'bank_reg_panel.csv'), index=False)
db.close()
log(f'FINAL panel: {len(p)} banks | src={p.src.value_counts().to_dict()} | '
    f'uninsured nonnull={p.uninsured_ratio.notna().sum()}')
log('sanity (top 6 by assets, assets in $000):\n' +
    p[['ticker','assets','uninsured_ratio','htm_loss_eq','sec_loss_eq']].head(6).to_string(index=False))
logf.close()
