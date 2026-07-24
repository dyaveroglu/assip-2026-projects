#!/usr/bin/env python3
"""
Project 09 (ChatGPT / AI-exposed labor) — Step 00: build the AI-exposure measures.

Source: Felten, Raj, and Seamans (2021), "Occupational, industry, and geographic
exposure to artificial intelligence" (Strategic Management Journal). Their public
Data Appendix (github.com/AIOE-Data/AIOE) provides:
  * Appendix A: AI Occupational Exposure (AIOE) by 6-digit SOC occupation (774 occs)
  * Appendix B: AI *Industry* Exposure (AIIE) by 4-digit NAICS (250 industries)   <- KEY
  * Appendix D: AI-application x O*NET-ability matrix (incl. a 'Language Modeling'
                column that is the ChatGPT-relevant application)

AIIE is the canonical, employment-weighted industry AI-exposure measure: for each
4-digit NAICS industry it averages occupation AIOE weighted by the industry's BLS
OES occupational employment mix. Higher AIIE = the industry's task bundle is more
exposed to AI. We use it as our industry-level AI-exposure proxy, then merge to
CRSP firms on 4-digit NAICS.

This script downloads the appendix (date-stamped to data/raw), writes tidy
industry- and occupation-level exposure CSVs to data/interim, and builds a
transparent substitution-vs-complement bucket map (data/interim/naics_buckets.csv)
whose economic logic is refined by the student's hand-coding task.

Nothing is fabricated; the raw workbook is preserved in data/raw for audit.
"""
import os, sys, datetime, hashlib, warnings
warnings.filterwarnings('ignore')
import urllib.request
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs')
for d in (RAW, INT, LOG): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_aioe_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

# ---------------------------------------------------------------- download ---
URLS = [
    'https://raw.githubusercontent.com/AIOE-Data/AIOE/master/AIOE_DataAppendix.xlsx',
    'https://raw.githubusercontent.com/AIOE-Data/AIOE/main/AIOE_DataAppendix.xlsx',
]
xlsx_path = os.path.join(RAW, 'AIOE_DataAppendix.xlsx')
if not os.path.exists(xlsx_path):
    ok = False
    for u in URLS:
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (ASSIP research)'})
            data = urllib.request.urlopen(req, timeout=60).read()
            if len(data) > 50000:
                open(xlsx_path, 'wb').write(data); ok = True
                log(f'downloaded AIOE appendix from {u} ({len(data)} bytes)'); break
        except Exception as e:
            log(f'download failed {u}: {e}')
    if not ok:
        log('FATAL: could not download AIOE appendix'); sys.exit(1)
else:
    log(f'AIOE appendix already present: {xlsx_path}')
log('sha256(appendix)=' + hashlib.sha256(open(xlsx_path, "rb").read()).hexdigest()[:16])

xl = pd.ExcelFile(xlsx_path)

# ---------------------------------------------------------- occupation AIOE ---
aioe = xl.parse('Appendix A').rename(columns={'SOC Code': 'soc', 'Occupation Title': 'occ',
                                              'AIOE': 'aioe'})
aioe['soc'] = aioe['soc'].astype(str).str.strip()
aioe.to_csv(os.path.join(INT, 'aioe_by_occupation.csv'), index=False)
log(f'AIOE occupations: {len(aioe)}  (mean {aioe.aioe.mean():.3f}, sd {aioe.aioe.std():.3f})')

# ------------------------------------------------------------ industry AIIE ---
aiie = xl.parse('Appendix B').rename(columns={'NAICS': 'naics4', 'Industry Title': 'industry',
                                              'AIIE': 'aiie'})
aiie['naics4'] = pd.to_numeric(aiie['naics4'], errors='coerce').astype('Int64')
aiie = aiie.dropna(subset=['naics4']).copy()
aiie['naics4'] = aiie['naics4'].astype(int)
aiie = aiie.drop_duplicates('naics4')
aiie.to_csv(os.path.join(INT, 'aiie_by_naics4.csv'), index=False)
log(f'AIIE industries (4-digit NAICS): {len(aiie)}  '
    f'(mean {aiie.aiie.mean():.3f}, sd {aiie.aiie.std():.3f}, '
    f'min {aiie.aiie.min():.3f}, max {aiie.aiie.max():.3f})')
log('  most AI-exposed industries:\n' +
    aiie.sort_values('aiie', ascending=False).head(8)[['naics4','industry','aiie']].to_string(index=False))
log('  least AI-exposed industries:\n' +
    aiie.sort_values('aiie').head(8)[['naics4','industry','aiie']].to_string(index=False))

# --------------------------------------------------- substitution/complement --
# Transparent, hand-checkable economic classification of the SIGN channel.
#   BUCKET = 'supplier'      : the firm BUILDS AI / sells compute-&-software that
#                              generative AI complements (expect POSITIVE).
#   BUCKET = 'substitution'  : the firm's OUTPUT is cognitive labor that generative
#                              AI can itself produce -> product-market substitution
#                              threat (sign ambiguous / potentially NEGATIVE).
#   BUCKET = 'user'          : everyone else -> AI is an internal productivity input
#                              (complement to the firm's non-core labor).
# These NAICS lists are a COARSE proxy; the student's hand-coding of true task
# exposure for 40-50 firms (STUDENT_TASKS.md) is what makes the split credible.
# Tightened to the least-ambiguous 4-digit codes (CRSP NAICS tags are noisy: e.g.
# NAICS 5614 lumps call-centers with payment/data firms like Visa & Moody's, and
# 5415 IT-services both build AND are threatened by code-generating AI -- the
# canonical ambiguous case left to the student's hand-coding).
SUPPLIER_NAICS4 = {3341, 3344,                      # computers & semiconductors (AI hardware)
                   5112, 5182}                      # software publishers, data processing/cloud
SUBSTITUTION_NAICS4 = {5111, 5191,                  # publishers, other information services (content)
                       5411, 5416, 5418,            # legal, consulting, advertising
                       5613,                        # employment services / staffing
                       6113, 6114, 6116}            # colleges, business/computer training, other schools
def bucket(n4):
    if n4 in SUPPLIER_NAICS4: return 'supplier'
    if n4 in SUBSTITUTION_NAICS4: return 'substitution'
    return 'user'
aiie['bucket'] = aiie['naics4'].map(bucket)
aiie[['naics4','industry','aiie','bucket']].to_csv(os.path.join(INT, 'naics_buckets.csv'), index=False)
log('bucket counts among AIIE industries: ' + aiie.bucket.value_counts().to_dict().__str__())

logf.close()
print('DONE 00_pull_aioe')
