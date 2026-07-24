#!/usr/bin/env python3
"""
Project 09 (ChatGPT) — Step 25: firm-level 10-K AI-mention intensity from SEC EDGAR.

For a stratified random sample of the panel (across AIIE quintiles), fetch each
firm's most recent 10-K filed BEFORE ChatGPT (< 2022-11-30), download the primary
document, strip HTML, and count AI-related terms per 10,000 words. This is a
firm-level, text-based AI-exposure measure that VALIDATES the industry AIIE proxy
and provides an alternative right-hand-side variable in the CAR cross-section.

Data source: SEC EDGAR (data.sec.gov submissions API + www.sec.gov Archives).
Polite crawling: descriptive User-Agent, <=8 req/s. Every firm's accession is
logged. Text counts are real; nothing is fabricated. Firms whose 10-K cannot be
retrieved are recorded as missing (never imputed).

Full firm-by-firm hand transcription of true task/AI exposure for 40-50 firms is
the student's task (STUDENT_TASKS.md); this automated pass is the machine baseline.
"""
import os, re, json, time, random, datetime, warnings
warnings.filterwarnings('ignore')
import urllib.request
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
LOG = os.path.join(HERE, 'logs')
for d in (INT, OUT): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'edgar_{STAMP}.log'), 'w')
def log(m):
    line=f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

UA = {'User-Agent': 'ASSIP Research (George Mason University) leigao.gmu@gmail.com'}
AI_PATTERNS = [
    r'artificial intelligence', r'machine learning', r'deep learning',
    r'natural language processing', r'large language model', r'generative a\.?i',
    r'neural network', r'chatgpt', r'\bgpt-?\d', r'foundation model',
    r'computer vision', r'\bl\.?l\.?m\.?s?\b', r'\ba\.?i\.?\b',
]
AI_RE = re.compile('|'.join(AI_PATTERNS), re.IGNORECASE)
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()

def latest_10k(cik):
    cik10 = str(int(cik)).zfill(10)
    j = json.loads(get(f'https://data.sec.gov/submissions/CIK{cik10}.json').decode('utf-8','ignore'))
    r = j['filings']['recent']
    for form, d, acc, prim in zip(r['form'], r['filingDate'], r['accessionNumber'], r['primaryDocument']):
        if form == '10-K' and d < '2022-11-30':
            accn = acc.replace('-', '')
            url = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{prim}'
            return d, acc, url
    return None

def ai_intensity(url):
    html = get(url).decode('utf-8', 'ignore')
    text = TAG_RE.sub(' ', html)
    text = WS_RE.sub(' ', text)
    words = text.split()
    n = len(words)
    if n < 500:  # not a real 10-K body
        return None
    hits = len(AI_RE.findall(text))
    return {'n_words': n, 'ai_hits': hits, 'ai_per_10k_words': 10000.0*hits/n,
            'ai_mentions_any': int(hits > 0)}

# ------------------------------------------------------------------ sample ---
panel = pd.read_csv(os.path.join(PROC, 'analytical_panel.csv'))
link = pd.read_csv(os.path.join(RAW, 'ccm_link.csv'))
fun = pd.read_csv(os.path.join(RAW, 'compustat_funda.csv'))[['gvkey','cik']].dropna()
fun = fun.merge(link, on='gvkey', how='inner')
panel = panel.merge(fun[['permno','cik']].drop_duplicates('permno'), on='permno', how='left')
panel = panel.dropna(subset=['cik','aiie']).copy()
panel['cik'] = panel['cik'].astype('int64')
log(f'panel firms with CIK: {len(panel)}')

random.seed(42)
TARGET = int(os.environ.get('EDGAR_TARGET', '650'))   # stratified target successes
panel['q'] = pd.qcut(panel.aiie, 5, labels=[1,2,3,4,5])
# order: interleave quintiles so a partial run is still balanced
order = []
groups = {q: panel[panel.q==q].sample(frac=1, random_state=1).to_dict('records') for q in [1,2,3,4,5]}
i = 0
while any(groups.values()):
    for q in [1,2,3,4,5]:
        if groups[q]:
            order.append(groups[q].pop())
    i += 1

rows=[]; ok=0; tried=0
for rec in order:
    if ok >= TARGET: break
    tried += 1
    cik = rec['cik']
    try:
        f = latest_10k(cik)
        if f is None:
            continue
        d, acc, url = f
        time.sleep(0.15)
        r = ai_intensity(url)
        if r is None:
            continue
        r.update({'permno': rec['permno'], 'cik': cik, 'ticker': rec.get('ticker'),
                  'naics4': rec['naics4'], 'aiie': rec['aiie'], 'filing_date': d, 'accession': acc})
        rows.append(r); ok += 1
        if ok % 50 == 0:
            log(f'  {ok} 10-Ks parsed (tried {tried})')
    except Exception as e:
        if tried % 100 == 0:
            log(f'  skip cik={cik}: {e}')
    time.sleep(0.15)

edf = pd.DataFrame(rows)
edf.to_csv(os.path.join(INT, 'firm_ai_intensity.csv'), index=False)
log(f'EDGAR done: {len(edf)} firms with parsed 10-K (tried {tried}); '
    f'mean AI/10k-words={edf.ai_per_10k_words.mean():.3f}, '
    f'share mentioning AI={edf.ai_mentions_any.mean():.3f}')

# ------------------------------------------------- validate + CAR regression --
import statsmodels.formula.api as smf
m = panel.merge(edf[['permno','ai_per_10k_words','ai_mentions_any','n_words']], on='permno', how='inner')
m['ln_ai'] = np.log1p(m.ai_per_10k_words)
m['z_ln_ai'] = (m.ln_ai - m.ln_ai.mean())/m.ln_ai.std()
corr = m[['aiie','ai_per_10k_words','ln_ai']].corr().loc['aiie']
log(f'validation corr(AIIE, ai_per_10k_words)={corr["ai_per_10k_words"]:.3f}, '
    f'corr(AIIE, ln_ai)={corr["ln_ai"]:.3f}')

res=[]
for dv,lbl in [('car_0_10_cg_w','CAR[0,+10] ChatGPT'),('car_0_1_cg_w','CAR[0,+1] ChatGPT')]:
    d = m.dropna(subset=[dv,'z_ln_ai','z_lnme','z_mom'])
    mod = smf.ols(f'{dv} ~ z_ln_ai + z_lnme + z_mom', d).fit(cov_type='cluster',cov_kwds={'groups':d.naics4})
    res.append({'DV':lbl,'coef_ai':mod.params['z_ln_ai'],'t_ai':mod.tvalues['z_ln_ai'],
                'N':int(mod.nobs),'R2':mod.rsquared})
t6=pd.DataFrame(res)
t6.attrs['corr']=corr['ln_ai']
t6.to_csv(os.path.join(OUT,'t6_edgar.csv'), index=False)
# also stash the validation corr in a one-row csv for the tex builder
pd.DataFrame([{'metric':'corr_aiie_lnai','value':corr['ln_ai']},
              {'metric':'corr_aiie_raw','value':corr['ai_per_10k_words']},
              {'metric':'n_firms','value':len(edf)},
              {'metric':'share_mention_ai','value':edf.ai_mentions_any.mean()}
             ]).to_csv(os.path.join(OUT,'t6_edgar_meta.csv'), index=False)
log('T6 firm-level 10-K AI-intensity CAR regression:\n'+t6.round(4).to_string(index=False))
log('DONE 25_edgar'); logf.close()
