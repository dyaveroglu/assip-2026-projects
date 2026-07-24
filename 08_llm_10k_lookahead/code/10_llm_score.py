#!/usr/bin/env python3
"""
Project 08 — Step 10: score each filing's risk-factor text with gpt-4o, TWICE:
once on the RAW text and once on the ANONYMIZED text. Identical prompt.

The score is a 0-100 expected-downside-risk rating over the 12 months after the
filing (higher = the model expects the stock to do worse). If the model is truly
"reading the 10-K", raw and anonymized scores should agree and predict returns
equally. If it is "remembering the stock" (look-ahead), the RAW score for
PRE-cutoff filings should track realized future returns more tightly than the
anonymized score -- and that gap should vanish for POST-cutoff filings.

Model: gpt-4o (gpt-4o-2024-11-20) via the GMU PatriotAI gateway. Knowledge
cutoff October 2023. Calls are sequential with exponential backoff; results are
appended to a JSONL so the job is fully resumable under the shared TPM cap.
"""
import os, sys, re, json, time, random, datetime, itertools
import pandas as pd
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(HERE, 'data', 'interim'); RAW = os.path.join(HERE, 'data', 'raw')
LOG = os.path.join(HERE, 'logs')
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'llm_score_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line, flush=True); logf.write(line+'\n'); logf.flush()

BASE = os.environ["PATRIOTAI_BASE_URL"]; KEY = os.environ["PATRIOTAI_API_KEY"]
SLUG = "gpt-4o"
OUT_JSONL = os.path.join(INT, 'llm_scores.jsonl')
SCORE_MAXCHARS = 2800   # per-call text budget (lower TPM pressure under the shared cap)

PROMPT = (
 "You are an equity analyst. Below is the Risk Factors (Item 1A) section from a "
 "company's annual report (Form 10-K). Assess the overall severity of DOWNSIDE "
 "risk to this company's common stock over the 12 months following this filing, "
 "weighing both the number and the seriousness of the risks described. Respond "
 "with ONLY a JSON object of the form {\"risk_score\": N}, where N is an integer "
 "from 0 to 100 (0 = minimal downside risk, the stock is likely to outperform; "
 "100 = severe downside risk, the stock is likely to decline sharply).\n\n"
 "RISK FACTORS:\n%s")

def call_llm(text):
    body = {"messages": [{"role": "user", "content": PROMPT % text}],
            "max_tokens": 30, "temperature": 0.0}
    req = Request(f"{BASE}openai/deployments/{SLUG}/chat/completions?api-version=2024-10-21",
                  data=json.dumps(body).encode(),
                  headers={"api-key": KEY, "Content-Type": "application/json"})
    r = json.loads(urlopen(req, timeout=120).read())
    txt = r["choices"][0]["message"]["content"]
    usage = r.get("usage", {}).get("total_tokens", 0)
    return txt, usage

def parse_score(txt):
    if not txt: return None
    m = re.search(r'"?risk_score"?\s*[:=]\s*(-?\d+)', txt)
    if not m:
        m = re.search(r'\b(\d{1,3})\b', txt)
    if m:
        v = int(m.group(1))
        return v if 0 <= v <= 100 else None
    return None

def score_with_backoff(text, tag):
    delay = 3.0
    for attempt in range(24):        # TPM cap is contended; keep trying, cap wait ~35s (per-minute reset)
        try:
            txt, usage = call_llm(text)
            s = parse_score(txt)
            if s is None:
                log(f'    {tag}: unparseable response {txt!r}; retry'); time.sleep(delay); delay=min(delay*1.5,35); continue
            return s, usage, txt
        except HTTPError as e:
            code = e.code
            try: ra = float(e.headers.get('Retry-After', 0) or 0)
            except Exception: ra = 0
            msg = e.read().decode()[:160]
            if code == 400 and 'content_filter' in msg:
                log(f'    {tag}: content_filter -> skip'); return None, 0, 'content_filter'
            if code in (429, 500, 502, 503):
                wait = ra if ra > 0 else delay + random.uniform(0, 3)
                wait = min(wait, 40)
                time.sleep(wait); delay = min(delay*1.6, 35); continue
            log(f'    {tag}: HTTP {code} {msg}; retry'); time.sleep(delay); delay=min(delay*1.6,35)
        except (URLError, TimeoutError) as e:
            time.sleep(delay); delay=min(delay*1.6,35)
        except Exception as e:
            log(f'    {tag}: err {type(e).__name__} {str(e)[:80]}; retry'); time.sleep(delay); delay=min(delay*1.6,35)
    return None, 0, 'exhausted'

# ---- build task list -------------------------------------------------------
sample = pd.read_csv(os.path.join(INT, 'sample_final.csv'))
st = pd.read_csv(os.path.join(INT, 'anon_stats.csv'))
usable = set(st[st.ok].id.astype(str))
random.seed(20260707)
# order: interleave pre/post at the FILING level, and score raw+anon of a filing
# back-to-back, so early termination still yields balanced, COMPLETE filings.
pre_ids  = [str(r.id) for _, r in sample.iterrows() if r.window=='pre'  and str(r.id) in usable]
post_ids = [str(r.id) for _, r in sample.iterrows() if r.window=='post' and str(r.id) in usable]
random.shuffle(pre_ids); random.shuffle(post_ids)
win = {str(r.id): r.window for _, r in sample.iterrows()}
order = []
for a, b in itertools.zip_longest(pre_ids, post_ids):
    for rid in (a, b):
        if rid is not None: order.append(rid)
tasks = []
for rid in order:
    tasks.append((rid, win[rid], 'raw'))
    tasks.append((rid, win[rid], 'anon'))

done = set()
if os.path.exists(OUT_JSONL):
    for line in open(OUT_JSONL):
        try:
            j = json.loads(line)
            if j.get('score') is not None: done.add((str(j['id']), j['cond']))
        except: pass
todo = [t for t in tasks if (t[0], t[2]) not in done]
log(f'tasks total={len(tasks)} done={len(done)} todo={len(todo)}')

tok_total = 0; n_ok = 0; t0 = time.time()
outf = open(OUT_JSONL, 'a')
for i, (rid, window, cond) in enumerate(todo):
    path = os.path.join(RAW, 'rf', f'{rid}.txt') if cond == 'raw' else os.path.join(INT, 'anon', f'{rid}.txt')
    text = open(path, encoding='utf-8', errors='replace').read()[:SCORE_MAXCHARS]
    s, usage, rawresp = score_with_backoff(text, f'{rid}/{cond}')
    tok_total += usage
    rec = dict(id=rid, window=window, cond=cond, score=s, tokens=usage)
    outf.write(json.dumps(rec) + '\n'); outf.flush()
    if s is not None: n_ok += 1
    if (i+1) % 20 == 0:
        rate = (i+1)/(time.time()-t0)
        log(f'  progress {i+1}/{len(todo)}  ok={n_ok}  tokens={tok_total}  '
            f'{rate:.2f} calls/s  eta {int((len(todo)-i-1)/max(rate,1e-9))}s')
    time.sleep(0.25)
outf.close()
log(f'DONE this run: attempted={len(todo)} newly-ok={n_ok} tokens={tok_total}')

# ---- pivot to wide CSV -----------------------------------------------------
recs = [json.loads(l) for l in open(OUT_JSONL) if l.strip()]
d = pd.DataFrame(recs)
d = d[d.score.notna()].drop_duplicates(['id','cond'], keep='last')
wide = d.pivot(index='id', columns='cond', values='score').reset_index()
wide.columns.name = None
wide = wide.rename(columns={'raw':'score_raw','anon':'score_anon'})
wide['id'] = wide['id'].astype(str)
wide.to_csv(os.path.join(INT, 'llm_scores.csv'), index=False)
both = wide.dropna(subset=['score_raw','score_anon'])
log(f'scores.csv: {len(wide)} filings ({len(both)} with BOTH raw+anon)')
if len(both):
    log(f'  score_raw mean={both.score_raw.mean():.1f} sd={both.score_raw.std():.1f} | '
        f'score_anon mean={both.score_anon.mean():.1f} sd={both.score_anon.std():.1f} | '
        f'mean|raw-anon|={ (both.score_raw-both.score_anon).abs().mean():.2f}')
logf.close()
