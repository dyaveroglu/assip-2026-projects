#!/usr/bin/env python3
"""
Project 14 (WARN) - Step 00: assemble a multi-state WARN mass-layoff panel.

Sources (all FREE, official state government data):
  (CA) California EDD detailed WARN reports. Four fiscal-year files covering
       07/2022 - 06/2026: three are PDFs, the current year is an XLSX.
       Columns: Notice Date, Received Date, Effective Date, Company, County,
                No. Of Employees, Layoff/Closure Type, Address.
  (TX) Texas Workforce Commission WARN notices, published as a Socrata dataset
       on data.texas.gov (id 8w53-c4f6). Columns include job_site_name,
       notice_date, total_layoff_number, county_name, city_name.
  (OR) Oregon WARN notices, Socrata dataset on data.oregon.gov (id ijbz-jpx8).
       Columns: company_name, received_date, layoff_date, laid_off, city, state.

Every raw file is written date-stamped to data/raw/. We then normalise the three
schemas to a common panel [state, company_raw, notice_date, n_employees, city,
layoff_type, source] and write data/interim/warn_all.csv. Nothing is fabricated;
row counts are logged at each step.
"""
import os, sys, io, json, datetime, warnings, urllib.request
warnings.filterwarnings('ignore')
import pandas as pd
import pdfplumber

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs')
for d in (RAW, INT, LOG): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

def fetch(url, dest, timeout=120):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        log(f'  cached {os.path.basename(dest)} ({os.path.getsize(dest)} bytes)'); return dest
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (research)'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    open(dest, 'wb').write(data)
    log(f'  downloaded {os.path.basename(dest)} ({len(data)} bytes)')
    return dest

# ---------------------------------------------------------------------------
# (CA) California EDD --------------------------------------------------------
# ---------------------------------------------------------------------------
CA_BASE = 'https://edd.ca.gov/siteassets/files/jobs_and_training/warn/'
CA_PDFS = {
    'warn-report-for-7-1-2022-to-06-30-2023.pdf': 'ca_2022_23.pdf',
    'warn-report-for-7-1-2023-to-06-30-2024.pdf': 'ca_2023_24.pdf',
    'warn-report-for-7-1-2024-to-06-30-2025.pdf': 'ca_2024_25.pdf',
}
CA_XLSX = ('warn_report1.xlsx', 'ca_2025_26.xlsx')  # current fiscal yr (07/2025-)

CA_HEADER_TOKENS = {'notice', 'received', 'company', 'employees'}
def _is_header(row):
    s = ' '.join(str(c).lower() for c in row if c)
    return sum(tok in s for tok in CA_HEADER_TOKENS) >= 2

def parse_ca_pdf(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            tbl = pg.extract_table()
            if not tbl: continue
            for r in tbl:
                if not r or len(r) < 8: continue
                if _is_header(r): continue
                notice, recv, eff, company, county, nemp, ltype, addr = r[:8]
                if not company or not notice: continue
                rows.append(dict(notice_date=notice, company_raw=str(company).strip(),
                                 county=county, n_employees=nemp, layoff_type=ltype,
                                 city=None))
    return pd.DataFrame(rows)

def parse_ca_xlsx(path):
    xl = pd.ExcelFile(path)
    sheet = [s for s in xl.sheet_names if 'detailed warn' in s.lower()][0]
    d = pd.read_excel(path, sheet_name=sheet, header=None)
    # header row is the one containing 'Company'
    hdr = None
    for i in range(min(6, len(d))):
        if d.iloc[i].astype(str).str.contains('Company', case=False, na=False).any():
            hdr = i; break
    d = d.iloc[hdr+1:].copy()
    d.columns = list(range(d.shape[1]))
    # sheet layout: County, Notice, Processed, Effective, Company, Layoff/Closure,
    #               No.Employees, Address, Related Industry
    out = pd.DataFrame(dict(
        notice_date=d[1], company_raw=d[4].astype(str).str.strip(), county=d[0],
        n_employees=d[6], layoff_type=d[5], city=None))
    out = out[out.company_raw.notna() & (out.company_raw.str.len() > 1)]
    return out

log('=== (CA) California EDD ===')
ca_parts = []
for src, dst in CA_PDFS.items():
    p = fetch(CA_BASE + src, os.path.join(RAW, dst))
    df = parse_ca_pdf(p); df['source'] = dst
    log(f'  parsed {dst}: {len(df)} notices'); ca_parts.append(df)
p = fetch(CA_BASE + CA_XLSX[0], os.path.join(RAW, CA_XLSX[1]))
try:
    df = parse_ca_xlsx(p); df['source'] = CA_XLSX[1]
    log(f'  parsed {CA_XLSX[1]}: {len(df)} notices'); ca_parts.append(df)
except Exception as e:
    log(f'  WARN: CA xlsx parse failed ({e}); continuing with PDF years')
ca = pd.concat(ca_parts, ignore_index=True)
ca['state'] = 'CA'
ca['notice_date'] = pd.to_datetime(ca['notice_date'], errors='coerce')
ca['n_employees'] = pd.to_numeric(ca['n_employees'], errors='coerce')
ca.to_csv(os.path.join(RAW, 'warn_ca.csv'), index=False)
log(f'(CA) total parsed rows: {len(ca)}  (valid dates {ca.notice_date.notna().sum()})')

# ---------------------------------------------------------------------------
# (TX) Texas Workforce Commission via Socrata -------------------------------
# ---------------------------------------------------------------------------
log('=== (TX) data.texas.gov 8w53-c4f6 ===')
tx_url = ('https://data.texas.gov/resource/8w53-c4f6.json?$limit=50000'
          '&$order=notice_date')
fetch(tx_url, os.path.join(RAW, 'warn_tx.json'))
tx = pd.read_json(os.path.join(RAW, 'warn_tx.json'))
tx = pd.DataFrame(dict(
    state='TX', company_raw=tx['job_site_name'].astype(str).str.strip(),
    notice_date=pd.to_datetime(tx['notice_date'], errors='coerce'),
    n_employees=pd.to_numeric(tx.get('total_layoff_number'), errors='coerce'),
    city=tx.get('city_name'), county=tx.get('county_name'),
    layoff_type=None, source='warn_tx.json'))
tx.to_csv(os.path.join(RAW, 'warn_tx.csv'), index=False)
log(f'(TX) rows: {len(tx)}  (valid dates {tx.notice_date.notna().sum()})')

# ---------------------------------------------------------------------------
# (OR) Oregon via Socrata ---------------------------------------------------
# ---------------------------------------------------------------------------
log('=== (OR) data.oregon.gov ijbz-jpx8 ===')
or_url = 'https://data.oregon.gov/resource/ijbz-jpx8.json?$limit=50000'
fetch(or_url, os.path.join(RAW, 'warn_or.json'))
org = pd.read_json(os.path.join(RAW, 'warn_or.json'))
org = pd.DataFrame(dict(
    state=org.get('state', 'OR'),
    company_raw=org['company_name'].astype(str).str.strip(),
    notice_date=pd.to_datetime(org['received_date'], errors='coerce'),
    n_employees=pd.to_numeric(org.get('laid_off'), errors='coerce'),
    city=org.get('city'), county=None,
    layoff_type=org.get('layoff_type'), source='warn_or.json'))
org.to_csv(os.path.join(RAW, 'warn_or.csv'), index=False)
log(f'(OR) rows: {len(org)}  (valid dates {org.notice_date.notna().sum()})')

# ---------------------------------------------------------------------------
# Combine & filter to the 2022-2025 sample window ---------------------------
# ---------------------------------------------------------------------------
cols = ['state', 'company_raw', 'notice_date', 'n_employees', 'city', 'layoff_type', 'source']
allw = pd.concat([ca[cols], tx[cols], org[cols]], ignore_index=True)
allw = allw[allw.notice_date.notna() & allw.company_raw.notna()]
allw = allw[(allw.notice_date >= '2022-01-01') & (allw.notice_date <= '2025-12-31')]
allw = allw[allw.company_raw.str.len() >= 2]
allw = allw.sort_values(['state', 'notice_date']).reset_index(drop=True)
allw.to_csv(os.path.join(INT, 'warn_all.csv'), index=False)
log(f'COMBINED 2022-2025 WARN panel: {len(allw)} notices')
log('  by state: ' + allw.state.value_counts().to_dict().__str__())
log('  by year:  ' + allw.notice_date.dt.year.value_counts().sort_index().to_dict().__str__())
log(f'  distinct raw company names: {allw.company_raw.nunique()}')
log('DONE - raw WARN written to data/raw/, combined panel to data/interim/warn_all.csv')
logf.close()
