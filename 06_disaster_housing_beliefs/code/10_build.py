#!/usr/bin/env python3
"""
Project 06 — Step 10: build the stacked county x month analytical panel.

For each event (Ian 2022-09, Helene 2024-09):
  frame  = every county whose STATE was hit by that storm's DR declarations.
  treated= county received FEMA Individuals & Households Program aid (IHP) -> hard hit.
  control= non-IHP county in the same storm states.
We align calendar months to months-since-landfall (rel_month), keep a symmetric
[-24, +20] window (Helene's 20 post months bind), require full ZHVI coverage so the
event study is balanced, then STACK the two events (unit = event x county). We merge
county climate beliefs (Yale 'worried'), 2020 GOP vote share, and FEMA National Risk
Index hurricane risk.

Outputs: data/interim/zhvi_long.csv, data/processed/panel.csv
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
PROC = os.path.join(HERE, 'data', 'processed'); LOG = os.path.join(HERE, 'logs')
for d in (INT, PROC): os.makedirs(d, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'build_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

PRE, POSTW = 24, 20   # months pre / post landfall in the balanced window

# ------------------------------------------------------------- FEMA: treated sets
fema = pd.read_csv(os.path.join(RAW, 'fema_declarations.csv'),
                   dtype={'fipsStateCode': str, 'fipsCountyCode': str})
fema['fips'] = fema.fipsStateCode.str.zfill(2) + fema.fipsCountyCode.str.zfill(3)
fema = fema[fema.fipsCountyCode.astype(int) > 0]           # drop statewide rows (county 000)
LANDFALL = {'Ian': '2022-09', 'Helene': '2024-09'}
ev_states, ev_treat, ev_desig = {}, {}, {}
for ev in ['Ian', 'Helene']:
    sub = fema[fema.event == ev]
    ev_states[ev] = sorted(sub.state.unique())
    ev_desig[ev] = set(sub.fips.unique())
    ev_treat[ev] = set(sub[sub.ihProgramDeclared == True].fips.unique())
    log(f'{ev}: states={ev_states[ev]} designated={len(ev_desig[ev])} IHP-treated={len(ev_treat[ev])}')

# ------------------------------------------------------------- ZHVI long (frame states)
z = pd.read_csv(os.path.join(RAW, 'zhvi_county.csv'))
z['fips'] = (z.StateCodeFIPS.astype(int).astype(str).str.zfill(2)
             + z.MunicipalCodeFIPS.astype(int).astype(str).str.zfill(3))
FRAME_STATES = sorted(set(sum(ev_states.values(), [])))
z = z[z.State.isin(FRAME_STATES)].copy()
datecols = [c for c in z.columns if c[:2] == '20']
zl = z.melt(id_vars=['fips', 'RegionName', 'State'], value_vars=datecols,
            var_name='date', value_name='zhvi')
zl['month'] = pd.to_datetime(zl.date).dt.to_period('M')
zl = zl.dropna(subset=['zhvi'])
zl.to_csv(os.path.join(INT, 'zhvi_long.csv'), index=False)
log(f'ZHVI long (frame states {FRAME_STATES}): {len(zl):,} county-months, '
    f'{zl.fips.nunique()} counties')

# ------------------------------------------------------------- moderators
y = pd.read_csv(os.path.join(RAW, 'ycom_county.csv'), dtype={'fips': str})
v = pd.read_csv(os.path.join(RAW, 'county_vote2020.csv'), dtype={'fips': str})
nri = pd.read_csv(os.path.join(RAW, 'nri_county.csv'), dtype={'fips': str})
for c in ['HRCN_RISKS', 'RISK_SCORE', 'CFLD_RISKS', 'HRCN_EALT']:
    nri[c] = pd.to_numeric(nri[c], errors='coerce')

# ------------------------------------------------------------- stack the events
frames = []
for ev in ['Ian', 'Helene']:
    lf = pd.Period(LANDFALL[ev], 'M')
    sub = zl[zl.State.isin(ev_states[ev])].copy()
    sub['event'] = ev
    sub['rel_month'] = (sub.month - lf).apply(lambda x: x.n)
    sub = sub[(sub.rel_month >= -PRE) & (sub.rel_month <= POSTW)]
    # balanced: keep counties present for every month in the window
    need = PRE + POSTW + 1
    cnt = sub.groupby('fips').month.nunique()
    keep = cnt[cnt == need].index
    sub = sub[sub.fips.isin(keep)].copy()
    sub['treat'] = sub.fips.isin(ev_treat[ev]).astype(int)
    sub['designated'] = sub.fips.isin(ev_desig[ev]).astype(int)
    sub['post'] = (sub.rel_month >= 1).astype(int)          # first full post month = landfall+1
    frames.append(sub)
    log(f'{ev}: balanced counties={sub.fips.nunique()} '
        f'(treated={sub[sub.treat==1].fips.nunique()}, control={sub[sub.treat==0].fips.nunique()}), '
        f'rows={len(sub):,}')

p = pd.concat(frames, ignore_index=True)
p = p.merge(y[['fips', 'worried', 'happening', 'personal', 'harmUS']], on='fips', how='left')
p = p.merge(v[['fips', 'per_gop']], on='fips', how='left')
p = p.merge(nri[['fips', 'HRCN_RISKS', 'RISK_SCORE', 'CFLD_RISKS', 'HRCN_EALT']], on='fips', how='left')

# ln outcome + standardized moderators + belief split (within analysis sample, county-level)
p['ln_zhvi'] = np.log(p.zhvi)
ccov = p.drop_duplicates('fips')          # one row per county for cross-sec medians/means
def z_of(col):
    m, s = ccov[col].mean(), ccov[col].std()
    return (p[col] - m) / s
p['worried_z'] = z_of('worried')
p['gop_z']     = z_of('per_gop')
p['hrcn_z']    = z_of('HRCN_RISKS')
med_w = ccov['worried'].median()
p['high_belief'] = (p.worried >= med_w).astype(int)
p['treatpost'] = p.treat * p.post
p['ce_id'] = p.event + '_' + p.fips                 # county x event  FE
p['em_id'] = p.event + '_' + p.month.astype(str)    # event x calendar-month FE
p['mstr']  = p.month.astype(str)

# drop county-events missing the key moderator (worried)
before = p.ce_id.nunique()
p = p.dropna(subset=['worried', 'ln_zhvi'])
log(f'dropped {before - p.ce_id.nunique()} county-events missing belief; median worried={med_w:.1f}')

p.to_csv(os.path.join(PROC, 'panel.csv'), index=False)
log(f'PANEL: {len(p):,} rows, {p.ce_id.nunique()} county-events, '
    f'{p.fips.nunique()} counties, treated county-events={p[p.treat==1].ce_id.nunique()}')
log(f'  treated by event: '
    f'{p[p.treat==1].groupby("event").fips.nunique().to_dict()}; '
    f'high-belief treated share={p[p.treat==1].high_belief.mean():.2f}')
log('DONE 10_build')
logf.close()
