#!/usr/bin/env python3
"""
Project 08 — Step 07: fetch Item-1A risk-factor text from the Hopper archive and
build an automated ANONYMIZED counterpart for each filing.

RAW text   -> data/raw/rf/{id}.txt          (truncated to MAXCHARS)
ANON text  -> data/interim/anon/{id}.txt

Automated anonymization (a defensible FLOOR; the human gold standard is the
student's task, see STUDENT_TASKS.md). We redact firm identity that an LLM could
use to "recognize the stock":
  * the company name and its distinctive word-tokens   -> [COMPANY]
  * the CRSP ticker (standalone)                        -> [TICKER]
  * any 4-digit year 19xx/20xx                          -> [YEAR]
  * U.S. state names / state of incorporation           -> [STATE]
Everything else (the actual risk content) is left intact. We log, per filing, how
many redactions were made and verify the company name no longer leaks.
"""
import os, sys, re, json, datetime, subprocess, warnings
warnings.filterwarnings('ignore')
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
RFDIR = os.path.join(RAW, 'rf'); ANONDIR = os.path.join(INT, 'anon')
LOG = os.path.join(HERE, 'logs')
for d in (RFDIR, ANONDIR): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'fetch_anon_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

MAXCHARS = 6000   # truncate risk-factor text (applied to BOTH raw & anon equally)

sample = pd.read_csv(os.path.join(INT, 'sample_final.csv'))
log(f'sample: {len(sample)} filings')

# ---- 1. fetch the section files from Hopper in one round-trip --------------
def section_path(raw_path):
    return raw_path.replace('raw.htm.gz', 'sections/item_1a_risk_factors.txt')
sample['sec_path'] = sample['raw_path'].map(section_path)

manifest = os.path.join(INT, 'sec_manifest.txt')
with open(manifest, 'w') as f:
    for _, r in sample.iterrows():
        f.write(f"{r.id}\t{r.sec_path}\n")

bundle_remote = '/tmp/rf_bundle_08.txt'
bundle_local = os.path.join(INT, 'rf_bundle.txt')
log('fetching risk-factor sections from Hopper ...')
subprocess.run(['scp', '-F', os.path.expanduser('~/.ssh/config_hopper'),
                manifest, 'hopper:/tmp/sec_manifest_08.txt'], check=True)
remote_cmd = (
    "while IFS=$'\\t' read -r id path; do "
    "echo \"===RFID:$id===\"; "
    "if [ -f \"$path\" ]; then cat \"$path\"; else echo '__MISSING__'; fi; "
    "done < /tmp/sec_manifest_08.txt > %s" % bundle_remote)
subprocess.run(['ssh', '-F', os.path.expanduser('~/.ssh/config_hopper'),
                'hopper', remote_cmd], check=True)
subprocess.run(['scp', '-F', os.path.expanduser('~/.ssh/config_hopper'),
                f'hopper:{bundle_remote}', bundle_local], check=True)
log(f'bundle fetched to {bundle_local} ({os.path.getsize(bundle_local)} bytes)')

# parse bundle into per-id raw text
text = open(bundle_local, encoding='utf-8', errors='replace').read()
parts = re.split(r'===RFID:([0-9]+)===\n', text)
raw_texts = {}
for i in range(1, len(parts), 2):
    rid = parts[i]; body = parts[i+1]
    raw_texts[rid] = body

# ---- 2. anonymizer ---------------------------------------------------------
GENERIC = {'INC','INCORPORATED','CORP','CORPORATION','CO','COMPANY','COMPANIES',
 'GROUP','HOLDINGS','HOLDING','LTD','LIMITED','LLC','PLC','LP','THE','AND','OF',
 'INTERNATIONAL','INTL','TECHNOLOGIES','TECHNOLOGY','SYSTEMS','SYSTEM','FINANCIAL',
 'BANCORP','BANCSHARES','BANKSHARES','INDUSTRIES','ENTERPRISES','ENTERPRISE',
 'PHARMACEUTICALS','PHARMACEUTICAL','PHARMA','CAPITAL','TRUST','REIT','ENERGY',
 'PARTNERS','SERVICES','SERVICE','SOLUTIONS','PRODUCTS','RESOURCES','MANAGEMENT',
 'PROPERTIES','COMMUNICATIONS','HEALTH','HEALTHCARE','MEDICAL','BANK','NATIONAL',
 'AMERICA','AMERICAN','US','USA','GLOBAL','WORLDWIDE','NEW','CLASS','COMMON','A','N'}
STATES = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado',
 'Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois',
 'Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland',
 'Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana',
 'Nebraska','Nevada','Ohio','Oklahoma','Oregon','Pennsylvania','Tennessee',
 'Texas','Utah','Vermont','Virginia','Washington','Wisconsin','Wyoming']

def name_tokens(conm):
    toks = re.split(r'[^A-Za-z0-9]+', str(conm).upper())
    return [t for t in toks if len(t) >= 3 and t not in GENERIC]

def anonymize(txt, conm, ticker):
    n = 0
    # full company name (as a phrase, case-insensitive)
    full = re.sub(r'[^A-Za-z0-9 ]+', ' ', str(conm)).strip()
    full = re.sub(r'\s+', r'\\s+', re.escape(full))
    if full:
        txt, k = re.subn(full, '[COMPANY]', txt, flags=re.IGNORECASE); n += k
    # distinctive name tokens
    for t in sorted(set(name_tokens(conm)), key=len, reverse=True):
        txt, k = re.subn(r'\b' + re.escape(t) + r'\b', '[COMPANY]', txt, flags=re.IGNORECASE)
        n += k
    # ticker (standalone, upper, len>=2)
    if isinstance(ticker, str) and ticker.strip() and len(ticker.strip()) >= 2:
        tk = ticker.strip().upper()
        txt, k = re.subn(r'\b' + re.escape(tk) + r'\b', '[TICKER]', txt); n += k
    # states
    for s in STATES:
        txt, k = re.subn(r'\b' + re.escape(s) + r'\b', '[STATE]', txt); n += k
    # 4-digit years
    txt, k = re.subn(r'\b(?:19|20)\d{2}\b', '[YEAR]', txt); n += k
    return txt, n

# ---- 3. write raw + anon, collect stats ------------------------------------
stats = []
n_missing = 0
for _, r in sample.iterrows():
    rid = str(r.id)
    body = raw_texts.get(rid, '')
    if (not body) or body.strip() == '__MISSING__':
        n_missing += 1
        stats.append(dict(id=rid, raw_chars=0, anon_chars=0, n_redactions=0,
                          name_leak_raw=0, name_leak_anon=0, ok=False)); continue
    body = re.sub(r'\s+\n', '\n', body).strip()
    raw = body[:MAXCHARS]
    anon, nred = anonymize(raw, r.conm, r.ticker)
    open(os.path.join(RFDIR, f'{rid}.txt'), 'w', encoding='utf-8').write(raw)
    open(os.path.join(ANONDIR, f'{rid}.txt'), 'w', encoding='utf-8').write(anon)
    toks = name_tokens(r.conm)
    def leak(s):
        return sum(len(re.findall(r'\b'+re.escape(t)+r'\b', s, flags=re.IGNORECASE)) for t in toks)
    stats.append(dict(id=rid, raw_chars=len(raw), anon_chars=len(anon),
                      n_redactions=nred, name_leak_raw=leak(raw),
                      name_leak_anon=leak(anon), ok=len(raw) > 200))
st = pd.DataFrame(stats)
st.to_csv(os.path.join(INT, 'anon_stats.csv'), index=False)
ok = st[st.ok]
log(f'written: {len(ok)} usable filings (missing/empty={ (~st.ok).sum() }, hopper-missing={n_missing})')
log(f'  mean raw chars = {ok.raw_chars.mean():.0f}, mean redactions/filing = {ok.n_redactions.mean():.1f}')
log(f'  name-token leakage: raw mean={ok.name_leak_raw.mean():.1f}  '
    f'anon mean={ok.name_leak_anon.mean():.2f}  (anon should be ~0)')
log(f'  filings with ZERO residual name leak in anon: {(ok.name_leak_anon==0).sum()}/{len(ok)}')
logf.close()
