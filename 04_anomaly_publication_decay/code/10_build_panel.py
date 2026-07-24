#!/usr/bin/env python3
"""
Project 04 -- Step 10: build the analytical anomaly-month panel.

Reshape PredictorLSretWide.csv (wide: date x 212 predictors) into a long
anomaly-month panel and merge SignalDoc metadata. For every anomaly i and
calendar month t we assign a publication REGIME, following McLean & Pontiff
(2016, JF):

    in-sample     : year(t) <= SampleEndYear_i          (original study window)
    post-sample   : SampleEndYear_i < year(t) < Year_i  (out of sample, pre-pub)
    post-pub      : year(t) >= Year_i                    (after publication)

We also build:
    postsample, postpub          -- mutually-exclusive regime dummies
    oos, pub                     -- NESTED McLean-Pontiff dummies
                                    oos = 1{year>SampleEndYear} (post-sample OR post-pub)
                                    pub = 1{year>=Year}         (post-pub, the extra effect)
    evt_year                     -- calendar year minus publication year (event time)
    risk_framed                  -- PROXY for a risk- vs mispricing-framed anomaly,
                                    from SignalDoc's Cat.Economic field (see below).

RISK-vs-MISPRICING PROXY (transparent, and deliberately crude): we label an
anomaly "risk-framed" if its OP economic category is one of an explicitly
risk-based set {risk, market risk, cash flow risk, default risk, optionrisk,
volatility, liquidity}; everything else (accruals, valuation, momentum,
investment, financing, profitability, ...) is "mispricing-framed." This is
ONLY a stand-in for the student's hand-read of each original paper's stated
economic story (e.g. book-to-market is coded "valuation"->mispricing here even
though Fama-French frame it as risk). The paper flags this explicitly.
"""
import os, datetime
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw')
INT  = os.path.join(HERE, 'data', 'interim');   os.makedirs(INT, exist_ok=True)
PROC = os.path.join(HERE, 'data', 'processed'); os.makedirs(PROC, exist_ok=True)
LOG  = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'build_{STAMP}.log'), 'a')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line + '\n'); logf.flush()

RISK_CATS = {'risk', 'market risk', 'cash flow risk', 'default risk',
             'optionrisk', 'volatility', 'liquidity'}
RISK_CATS_NARROW = {'risk', 'market risk', 'cash flow risk', 'default risk',
                    'optionrisk', 'volatility'}  # excludes liquidity (robustness)

# ---- load ----------------------------------------------------------------
wide = pd.read_csv(os.path.join(RAW, 'PredictorLSretWide.csv'))
doc  = pd.read_csv(os.path.join(RAW, 'SignalDoc.csv'))
log(f'loaded wide returns: {wide.shape[0]} months x {wide.shape[1]-1} predictors')
log(f'loaded SignalDoc: {doc.shape[0]} rows')

# wide -> long
long = wide.melt(id_vars='date', var_name='signal', value_name='ret').dropna(subset=['ret'])
long['date'] = pd.to_datetime(long['date'])
long['year'] = long['date'].dt.year
log(f'reshaped to long: {len(long):,} non-missing anomaly-month returns')

# metadata (keep only actual PREDICTORS with a publication year & sample end)
meta = doc[doc['Cat.Signal'] == 'Predictor'].copy()
meta = meta.rename(columns={'Acronym': 'signal', 'Year': 'pubyear',
                            'SampleEndYear': 'sampend', 'SampleStartYear': 'sampstart',
                            'Cat.Economic': 'econ_cat', 'Authors': 'authors',
                            'Journal': 'journal'})
meta = meta[['signal', 'authors', 'journal', 'pubyear', 'sampstart', 'sampend',
             'econ_cat', 'Sign', 'Return', 'T-Stat']]
meta = meta.dropna(subset=['pubyear', 'sampend'])
meta['pubyear'] = meta['pubyear'].astype(int)
meta['sampend'] = meta['sampend'].astype(int)
log(f'predictor metadata rows with pubyear & sampend: {len(meta)}')
# sanity: publication should come at or after the sample ends
bad = (meta['pubyear'] < meta['sampend']).sum()
log(f'  anomalies with pubyear < sampend (dropped as inconsistent): {bad}')
meta = meta[meta['pubyear'] >= meta['sampend']].copy()

# risk proxy
meta['risk_framed']        = meta['econ_cat'].isin(RISK_CATS).astype(int)
meta['risk_framed_narrow'] = meta['econ_cat'].isin(RISK_CATS_NARROW).astype(int)
log(f'risk-framed (broad, incl. liquidity): {int(meta.risk_framed.sum())} anomalies; '
    f'mispricing: {int((1-meta.risk_framed).sum())}')
log(f'risk-framed (narrow, excl. liquidity): {int(meta.risk_framed_narrow.sum())} anomalies')

# merge
d = long.merge(meta, on='signal', how='inner')
log(f'merged panel: {len(d):,} anomaly-months across {d.signal.nunique()} anomalies')

# ---- regimes -------------------------------------------------------------
d['postsample'] = ((d['year'] > d['sampend']) & (d['year'] < d['pubyear'])).astype(int)
d['postpub']    = (d['year'] >= d['pubyear']).astype(int)
d['insample']   = (d['year'] <= d['sampend']).astype(int)
# nested McLean-Pontiff dummies
d['oos'] = (d['year'] > d['sampend']).astype(int)   # out of sample (pre-pub OR post-pub)
d['pub'] = (d['year'] >= d['pubyear']).astype(int)  # extra publication effect
d['regime'] = np.select(
    [d['insample'] == 1, d['postsample'] == 1, d['postpub'] == 1],
    ['insample', 'postsample', 'postpub'], default='na')
d['evt_year'] = d['year'] - d['pubyear']            # event time (years from pub)

# per-anomaly in-sample mean return (for scale-free % decay robustness)
ins_mean = (d[d['insample'] == 1].groupby('signal')['ret'].mean()
            .rename('insample_mean').reset_index())
d = d.merge(ins_mean, on='signal', how='left')
# normalized return: 100 = the anomaly's own in-sample mean (only where that mean>0)
d['ret_norm'] = np.where(d['insample_mean'] > 0, 100.0 * d['ret'] / d['insample_mean'], np.nan)

# integer ids for clustering
d['sid'] = d['signal'].astype('category').cat.codes
d['mid'] = d['date'].astype('category').cat.codes

# ---- write ---------------------------------------------------------------
meta.to_csv(os.path.join(INT, 'anomaly_meta.csv'), index=False)
keep = ['date', 'year', 'signal', 'sid', 'mid', 'ret', 'ret_norm', 'insample_mean',
        'authors', 'journal', 'pubyear', 'sampstart', 'sampend', 'econ_cat',
        'risk_framed', 'risk_framed_narrow', 'regime',
        'insample', 'postsample', 'postpub', 'oos', 'pub', 'evt_year']
d[keep].to_csv(os.path.join(PROC, 'anomaly_panel.csv'), index=False)
log(f'wrote data/processed/anomaly_panel.csv  ({len(d):,} rows, {len(keep)} cols)')

# quick regime tally to the log
tally = d.groupby('regime')['ret'].agg(['count', 'mean'])
log('regime tally (count, mean monthly LS ret in %):\n' + tally.round(4).to_string())
log(f'anomalies with negative in-sample mean (excluded from ret_norm): '
    f'{int((ins_mean["insample_mean"] <= 0).sum())}')
log('build step complete.')
logf.close()
