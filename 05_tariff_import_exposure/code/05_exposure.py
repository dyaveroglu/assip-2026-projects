#!/usr/bin/env python3
"""
Project 05 - Step 05: build INDUSTRY IMPORTED-INPUT INTENSITY from BEA data.

Construct, for each BEA summary industry j,
    imp_intensity_j = (imported intermediate inputs used by industry j)
                      / (industry j gross output, 2023).
Numerator  = column sum over imported commodities in the BEA 2023 Summary
             Import Matrix (Before Redefinitions).
Denominator= BEA Gross Output by industry, 2023 (current $).
Then map BEA summary code -> NAICS-3 so it can be merged to CRSP/Compustat firms.

This is the real, downloadable, "imported-input-exposure" proxy the paper's
core result uses. The student's hand-verified 10-K input sourcing (see
STUDENT_TASKS.md) will later sharpen this industry proxy into a firm-level one.
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, openpyxl

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, 'data', 'raw'); INT = os.path.join(HERE, 'data', 'interim')
LOG = os.path.join(HERE, 'logs'); os.makedirs(INT, exist_ok=True)
STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'exposure_{STAMP}.log'), 'w')
def log(m):
    line = f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'
    print(line); logf.write(line+'\n'); logf.flush()

def norm(x): return str(x).strip() if x is not None else ''
def num(x):
    try:
        s = str(x).replace(',', '').strip()
        if s in ('', '...', '.', '(D)', '(NA)', 'NM', 'None'): return 0.0
        return float(s)
    except Exception: return 0.0

# ---- 1) imported intermediate inputs by using industry (2023) -------------
wb = openpyxl.load_workbook(os.path.join(RAW, 'bea_import_matrix.xlsx'), data_only=True)
ws = wb['2023']; R = [[c.value for c in r] for r in ws.iter_rows()]
hdr = R[5]                                   # column IOCodes
hdr_codes = {j: norm(hdr[j]) for j in range(len(hdr)) if norm(hdr[j])}
comm_rows = [i for i in range(7, len(R)) if norm(R[i][0]) and norm(R[i][1])]
code_name = {norm(R[i][0]): norm(R[i][1]) for i in comm_rows}       # IOCode -> name
# using-industry columns = header codes that are industries (not final demand F*/T*/V*)
ind_cols = {c: j for j, c in hdr_codes.items()
            if j >= 2 and not c.startswith(('F0', 'F1', 'T0', 'T1', 'V0'))
            and c not in ('IOCode', 'Name')}
imp = {}
for code, j in ind_cols.items():
    imp[code] = sum(num(R[i][j]) for i in comm_rows)
log(f'imported-input column sums built for {len(imp)} BEA industries')

# ---- 2) gross output by industry (2023) -----------------------------------
wb2 = openpyxl.load_workbook(os.path.join(RAW, 'bea_gross_output.xlsx'), data_only=True)
ws2 = wb2['TGO105-A']; G = [[c.value for c in r] for r in ws2.iter_rows()]
yrs = G[7]
col2023 = [j for j in range(len(yrs)) if norm(yrs[j]) == '2023'][0]
go_by_title = {}
for i in range(8, len(G)):
    t = norm(G[i][1])
    if t:
        go_by_title[t.lower()] = num(G[i][col2023])
log(f'gross-output titles parsed: {len(go_by_title)} (2023 col idx {col2023}, '
    f'all-industries=${num(G[8][col2023]):,.0f}M)')

# ---- 3) intensity by BEA industry -----------------------------------------
rows, unmatched = [], []
for code, iv in imp.items():
    name = code_name.get(code, '')
    go = go_by_title.get(name.lower(), np.nan)
    if not np.isfinite(go) or go <= 0:
        unmatched.append((code, name)); continue
    rows.append({'bea_code': code, 'bea_name': name,
                 'imp_inputs_musd': iv, 'gross_output_musd': go,
                 'imp_intensity': iv / go})
bea = pd.DataFrame(rows).sort_values('imp_intensity', ascending=False)
log(f'BEA industries with intensity: {len(bea)}; unmatched titles: {unmatched}')
log('Top-10 imported-input-intensive BEA industries:\n' +
    bea.head(10)[['bea_code', 'bea_name', 'imp_intensity']].round(3).to_string(index=False))
log('Bottom-8:\n' + bea.tail(8)[['bea_code', 'bea_name', 'imp_intensity']].round(3).to_string(index=False))

# ---- 4) BEA summary code -> NAICS-3 crosswalk -----------------------------
BEA2NAICS = {
 '111CA': ['111','112'], '113FF': ['113','114','115'], '211': ['211'],
 '212': ['212'], '213': ['213'], '22': ['221'], '23': ['236','237','238'],
 '321': ['321'], '327': ['327'], '331': ['331'], '332': ['332'], '333': ['333'],
 '334': ['334'], '335': ['335'], '3361MV': ['336'], '3364OT': ['336'],
 '337': ['337'], '339': ['339'], '311FT': ['311','312'], '313TT': ['313','314'],
 '315AL': ['315','316'], '322': ['322'], '323': ['323'], '324': ['324'],
 '325': ['325'], '326': ['326'], '42': ['423','424','425'], '441': ['441'],
 '445': ['445'], '452': ['452'],
 '4A0': ['442','443','444','446','447','448','451','453','454'],
 '481': ['481'], '482': ['482'], '483': ['483'], '484': ['484'], '485': ['485'],
 '486': ['486'], '487OS': ['487','488','492'], '493': ['493'], '511': ['511'],
 '512': ['512'], '513': ['515','516','517'], '514': ['518','519'],
 '521CI': ['521','522'], '523': ['523'], '524': ['524'], '525': ['525'],
 '532RL': ['532','533'], '5411': ['541'], '5415': ['541'],
 '5412OP': ['541'], '55': ['551'], '561': ['561'], '562': ['562'], '61': ['611'],
 '621': ['621'], '622': ['622'], '623': ['623'], '624': ['624'],
 '711AS': ['711','712'], '713': ['713'], '721': ['721'], '722': ['722'],
 '81': ['811','812','813','814'], 'ORE': ['531'], 'HS': ['531'],
}
# NAICS-3 -> intensity (if two BEA codes map to same NAICS3, take output-weighted mean)
bea_i = bea.set_index('bea_code')
naics_rows = {}
for code, n3list in BEA2NAICS.items():
    if code not in bea_i.index:
        continue
    inten = bea_i.loc[code, 'imp_intensity']; go = bea_i.loc[code, 'gross_output_musd']
    for n3 in n3list:
        naics_rows.setdefault(n3, []).append((inten, go, code))
xwalk = []
for n3, lst in naics_rows.items():
    tot = sum(g for _, g, _ in lst)
    inten = sum(i*g for i, g, _ in lst)/tot if tot > 0 else np.mean([i for i, _, _ in lst])
    xwalk.append({'naics3': n3, 'imp_intensity': inten,
                  'bea_codes': '|'.join(sorted(set(c for _, _, c in lst)))})
xw = pd.DataFrame(xwalk).sort_values('naics3')
xw.to_csv(os.path.join(INT, 'industry_import_intensity.csv'), index=False)
bea.to_csv(os.path.join(INT, 'bea_industry_intensity.csv'), index=False)
log(f'NAICS-3 crosswalk rows: {len(xw)} (median intensity {xw.imp_intensity.median():.3f})')
log('DONE - industry_import_intensity.csv written')
logf.close()
