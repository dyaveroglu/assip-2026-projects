#!/usr/bin/env python3
"""
Project 06 — Step 00: pull all REAL, FREE data to data/raw/.

Design (distance/exposure DiD around two specific landfalls):
  * Outcome  : Zillow ZHVI, county-level, monthly typical home value.
  * Treatment: counties FEMA designated for the storm's *Individuals & Households
               Program* (IHP) -- i.e. counties with enough household-level damage
               that residents got direct federal aid. This is FEMA's own, primary-
               source measure of who was actually hit hard ("newly-salient high risk").
  * Events   : Hurricane Ian (landfall 2022-09-28, SW Florida) and Hurricane
               Helene (landfall 2024-09-26, Big Bend FL -> Appalachia).
  * Controls : non-IHP counties in the SAME storm-affected states.
  * Moderator: county climate beliefs (Yale YCOM 'worried'), with 2020 GOP vote
               share as an inverse-belief robustness proxy.
  * Baseline risk / salience: FEMA National Risk Index hurricane risk score.

Sources (all free, no key):
  Zillow ZHVI county CSV | OpenFEMA DisasterDeclarationsSummaries | Yale YCOM county
  CSV (GitHub) | MIT/tonmcg 2020 county presidential returns | FEMA National Risk
  Index Counties ArcGIS FeatureServer.
"""
import os, json, time, datetime, urllib.request, urllib.parse, io
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw'); LOG = os.path.join(HERE, 'logs')
os.makedirs(RAW, exist_ok=True); os.makedirs(LOG, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'pull_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

UA = {'User-Agent': 'Lei Gao leigao.gmu@gmail.com academic research'}
def get(url, timeout=180, tries=5):
    for a in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:
            log(f'  retry {a+1} on {url[:80]}... ({e})')
            if a == tries-1: raise
            time.sleep(3*(a+1))

# ---------------------------------------------------------------- 1) Zillow ZHVI
ZURL = ('https://files.zillowstatic.com/research/public_csvs/zhvi/'
        'County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
zpath = os.path.join(RAW, 'zhvi_county.csv')
open(zpath, 'wb').write(get(ZURL))
z = pd.read_csv(zpath)
ndate = len([c for c in z.columns if c[:2] == '20'])
log(f'ZHVI: {z.shape[0]} counties x {ndate} months, through '
    f'{[c for c in z.columns if c[:2]=="20"][-1]}')

# ---------------------------------------------------------------- 2) FEMA declarations
# Event -> (disasterNumber, state) for the storm's major-disaster (DR) declarations.
EVENTS = {
    'Ian':    {'landfall': '2022-09-28', 'drs': [4673, 4677]},               # FL, SC
    'Helene': {'landfall': '2024-09-26', 'drs': [4827, 4828, 4829, 4830, 4831, 4832]},  # NC,FL,SC,GA,VA,TN
}
FBASE = 'https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries'
FSEL = ('disasterNumber,femaDeclarationString,state,declarationType,declarationTitle,'
        'declarationDate,incidentBeginDate,fipsStateCode,fipsCountyCode,designatedArea,'
        'ihProgramDeclared,iaProgramDeclared,paProgramDeclared,hmProgramDeclared')
rows = []
for ev, meta in EVENTS.items():
    for dn in meta['drs']:
        q = {'$filter': f'disasterNumber eq {dn}', '$select': FSEL,
             '$top': 1000, '$format': 'json'}
        url = FBASE + '?' + urllib.parse.urlencode(q, safe="$,' ()").replace(' ', '%20')
        d = json.loads(get(url, timeout=120))['DisasterDeclarationsSummaries']
        for r in d:
            r['event'] = ev; r['landfall'] = meta['landfall']
            rows.append(r)
        log(f'  FEMA {ev} DR-{dn} ({d[0]["state"] if d else "?"}): {len(d)} rows')
fema = pd.DataFrame(rows)
fema.to_csv(os.path.join(RAW, 'fema_declarations.csv'), index=False)
ih = fema[fema.ihProgramDeclared == True]
log(f'FEMA: {len(fema)} declaration-area rows; '
    f'unique IHP counties by event = '
    f'{ih.groupby("event").apply(lambda x: x[["fipsStateCode","fipsCountyCode"]].drop_duplicates().shape[0]).to_dict()}')

# ---------------------------------------------------------------- 3) Yale YCOM county
YURL = ('https://raw.githubusercontent.com/yaleschooloftheenvironment/'
        'Yale-Climate-Change-Opinion-Maps/main/YCOM5.0_2020_webdata_2020-08-19.csv')
ybytes = get(YURL, timeout=120)
y = pd.read_csv(io.BytesIO(ybytes), encoding='latin-1')
y = y[y.GeoType == 'County'].copy()
y['fips'] = y['GEOID'].astype(int).astype(str).str.zfill(5)
YKEEP = ['fips', 'GeoName', 'TotalPop', 'happening', 'human', 'worried', 'personal',
         'harmUS', 'devharm', 'futuregen', 'CO2limits', 'regulate']
y[YKEEP].to_csv(os.path.join(RAW, 'ycom_county.csv'), index=False)
log(f'YCOM: {len(y)} counties; worried mean={y.worried.mean():.1f} '
    f'[{y.worried.min():.1f},{y.worried.max():.1f}]')

# ---------------------------------------------------------------- 4) 2020 vote share
VURL = ('https://raw.githubusercontent.com/tonmcg/US_County_Level_Election_Results_08-24/'
        'master/2020_US_County_Level_Presidential_Results.csv')
v = pd.read_csv(io.BytesIO(get(VURL, timeout=120)), dtype={'county_fips': str})
v['fips'] = v['county_fips'].str.zfill(5)
v[['fips', 'state_name', 'county_name', 'per_gop', 'per_dem', 'total_votes']
  ].to_csv(os.path.join(RAW, 'county_vote2020.csv'), index=False)
log(f'Vote2020: {len(v)} counties; GOP share mean={v.per_gop.mean():.3f}')

# ---------------------------------------------------------------- 5) FEMA NRI (ArcGIS)
NRI = ('https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/'
       'National_Risk_Index_Counties/FeatureServer/0/query')
NFLDS = 'STCOFIPS,STATE,COUNTY,RISK_SCORE,RISK_RATNG,EAL_SCORE,HRCN_RISKS,HRCN_RISKR,HRCN_EALT,CFLD_RISKS'
nri_rows, off = [], 0
while True:
    q = {'where': '1=1', 'outFields': NFLDS, 'resultOffset': off,
         'resultRecordCount': 1000, 'returnGeometry': 'false', 'f': 'json'}
    d = json.loads(get(NRI + '?' + urllib.parse.urlencode(q), timeout=120))
    feats = d.get('features', [])
    nri_rows += [f['attributes'] for f in feats]
    log(f'  NRI page offset {off}: +{len(feats)}')
    if len(feats) < 1000: break
    off += 1000
nri = pd.DataFrame(nri_rows)
nri['fips'] = nri['STCOFIPS'].astype(str).str.zfill(5)
nri.to_csv(os.path.join(RAW, 'nri_county.csv'), index=False)
log(f'NRI: {len(nri)} counties; HRCN_RISKS mean={pd.to_numeric(nri.HRCN_RISKS,errors="coerce").mean():.1f}')

log('DONE 00_pull')
logf.close()
