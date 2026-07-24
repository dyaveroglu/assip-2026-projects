#!/usr/bin/env python3
"""
Project 04 (Anomaly Publication Decay) -- Step 00: download REAL data.

Open Source Asset Pricing (Chen & Zimmermann; openassetpricing.com), release
v2.0.0 (Oct 2025). Two public files, hosted on the project's Google Drive:

  * PredictorLSretWide.csv -- monthly long-short (LS) portfolio returns, in
    percent, for 212 published cross-sectional predictors (1926-2024).
  * SignalDoc.csv          -- signal metadata: original Authors, Year (of
    publication), Journal, SampleStartYear, SampleEndYear, and the
    Cat.Economic economic-category field.

Both are downloaded straight from Google Drive so the pull is reproducible.
Idempotent: skips a file that is already present and non-trivial in size.
"""
import os, re, sys, datetime, requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw'); os.makedirs(RAW, exist_ok=True)
LOG  = os.path.join(HERE, 'logs'); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'download_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

# Google Drive file IDs harvested from https://www.openassetpricing.com/data/
FILES = {
    'SignalDoc.csv':            '1Sev9s6cPFUGgxp1pFiej0lGzpsMqJCI2',
    'PredictorLSretWide.csv':   '10sOryk_ddjkXagaajTKUk1nwJs2ZLRiI',
}

def gdrive_download(file_id, dest):
    """Download a Google-Drive file, handling the large-file confirm token."""
    s = requests.Session()
    r = s.get('https://drive.google.com/uc?export=download',
              params={'id': file_id}, stream=True, timeout=180)
    token = None
    for k, v in r.cookies.items():
        if k.startswith('download_warning'):
            token = v
    if token is None:
        m = re.search(r'confirm=([0-9A-Za-z_\-]+)', r.text)
        token = m.group(1) if m else None
        m2 = re.search(r'name="uuid" value="([^"]+)"', r.text)
        uuid = m2.group(1) if m2 else None
        if token:
            params = {'id': file_id, 'export': 'download', 'confirm': token}
            if uuid:
                params['uuid'] = uuid
            r = s.get('https://drive.usercontent.google.com/download',
                      params=params, stream=True, timeout=600)
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(1 << 15):
            if chunk:
                f.write(chunk)
    return os.path.getsize(dest)

for name, fid in FILES.items():
    dest = os.path.join(RAW, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 10000:
        log(f'SKIP {name} (already present, {os.path.getsize(dest):,} bytes)')
        continue
    log(f'downloading {name} from Google Drive id={fid} ...')
    sz = gdrive_download(fid, dest)
    log(f'  -> {name}: {sz:,} bytes')
    if sz < 10000:
        log(f'  WARNING: {name} suspiciously small; download may have failed')

# report row counts
import pandas as pd
for name in FILES:
    p = os.path.join(RAW, name)
    try:
        df = pd.read_csv(p, nrows=5)
        n = sum(1 for _ in open(p, 'r', encoding='utf-8', errors='ignore')) - 1
        log(f'{name}: {n:,} data rows, {df.shape[1]} columns')
    except Exception as e:
        log(f'{name}: could not parse ({e})')
log('download step complete.')
logf.close()
