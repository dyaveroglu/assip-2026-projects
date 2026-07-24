#!/usr/bin/env python3
"""
Project 08 — Step 20: assemble the analytic panel.

Merges: sample_final (filing metadata + window) + returns (forward BHAR) +
llm_scores (raw & anonymized gpt-4o risk scores) + anon_stats (redaction counts).
The analytic sample keeps filings that have BOTH a raw and an anonymized score.
Scores are z-standardized on the POOLED distribution of {raw, anon} scores so
the raw and anon coefficients are directly comparable.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(HERE, 'data', 'interim'); PROC = os.path.join(HERE, 'data', 'processed')
LOG = os.path.join(HERE, 'logs'); os.makedirs(PROC, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'panel_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

sample = pd.read_csv(os.path.join(INT, 'sample_final.csv'), dtype={'id':str})
scores = pd.read_csv(os.path.join(INT, 'llm_scores.csv'), dtype={'id':str})
anon   = pd.read_csv(os.path.join(INT, 'anon_stats.csv'), dtype={'id':str})

df = sample.merge(scores, on='id', how='inner').merge(
     anon[['id','n_redactions','name_leak_raw','raw_chars']], on='id', how='left')
df = df.dropna(subset=['score_raw','score_anon']).copy()
df['post'] = (df.window == 'post').astype(int)
df['score_gap'] = df['score_raw'] - df['score_anon']

# pooled standardization of scores
pooled = pd.concat([df['score_raw'], df['score_anon']])
mu, sd = pooled.mean(), pooled.std()
df['z_raw']  = (df['score_raw']  - mu) / sd
df['z_anon'] = (df['score_anon'] - mu) / sd
df['z_gap']  = df['score_gap'] / sd

# winsorized DVs (1/99) for the main specs; keep raw too
def wins(s, p=0.01):
    lo, hi = s.quantile(p), s.quantile(1-p); return s.clip(lo, hi)
for k in ['bhar_3','bhar_6','bhar_12','firm_cum_12']:
    df[k+'_w'] = wins(df[k])

df = df.sort_values(['window','filing_date']).reset_index(drop=True)
df.to_csv(os.path.join(PROC, 'panel.csv'), index=False)
log(f'PANEL: {len(df)} filings with both scores  '
    f'(pre={ (df.window=="pre").sum() }, post={ (df.window=="post").sum() })')
log(f'  pooled score mu={mu:.1f} sd={sd:.1f}')
log('  by window:\n' + df.groupby('window')[['score_raw','score_anon','score_gap','bhar_12']]
      .mean().round(3).to_string())
logf.close()
