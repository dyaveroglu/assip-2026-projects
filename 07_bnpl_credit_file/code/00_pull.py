#!/usr/bin/env python3
"""
Project 07 (BNPL) — Step 00: pull CFPB complaints for pure-play BNPL lenders.

Design: within-firm DiD. When a BNPL lender starts FURNISHING loans to the credit
bureaus (Affirm -> Experian/TransUnion, 2025), credit-reporting complaints should
jump relative to that same lender's OTHER complaints (billing, refunds, fraud),
which are unaffected by furnishing. We pull every complaint for the pure-play BNPL
firms so we can build both series.

Free public data: CFPB Consumer Complaint Database API (no key).
"""
import os, json, time, datetime, urllib.request, urllib.parse
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

BASE = "https://consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
BASE = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
UA = {'User-Agent': 'Lei Gao leigao.gmu@gmail.com academic research'}
def api(params):
    url = BASE + "?" + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())
        except Exception as e:
            if attempt == 3: raise
            time.sleep(3*(attempt+1))

# 1) resolve exact company names for BNPL pure-plays
KEYWORDS = ['affirm', 'klarna', 'sezzle', 'zip co', 'quadpay', 'afterpay', 'perpay']
companies = set()
for kw in KEYWORDS:
    r = api({'search_term': kw, 'date_received_min': '2022-01-01', 'size': 0})
    for b in r['aggregations']['company']['company']['buckets']:
        if kw.split()[0] in b['key'].lower():
            companies.add(b['key'])
companies = sorted(companies)
log(f'resolved {len(companies)} BNPL company names: {companies}')

# 2) pull all complaints for those companies, 2022-01 .. 2026-06, paginated
FIELDS = ['complaint_id','date_received','product','sub_product','issue','sub_issue',
          'company','state','consumer_complaint_narrative','company_response',
          'timely','company_public_response','tags','submitted_via']
rows = []
for comp in companies:
    frm, size = 0, 1000
    while True:
        r = api({'company': comp, 'date_received_min': '2022-01-01',
                 'date_received_max': '2026-06-30', 'size': size, 'frm': frm, 'format': 'json'})
        if not r: break
        for h in r:
            s = h.get('_source', {})
            rows.append({k: s.get(k) for k in FIELDS})
        got = len(r)
        log(f'  {comp}: +{got} (offset {frm})')
        if got < size: break
        frm += size
        if frm >= 10000: break

df = pd.DataFrame(rows).drop_duplicates('complaint_id')
df.to_csv(os.path.join(RAW, 'cfpb_bnpl.csv'), index=False)
log(f'TOTAL complaints pulled: {len(df)} across {df.company.nunique()} firms, '
    f'{df.date_received.min()} .. {df.date_received.max()}')
log('product mix:\n' + df['product'].value_counts().head(8).to_string())
logf.close()
