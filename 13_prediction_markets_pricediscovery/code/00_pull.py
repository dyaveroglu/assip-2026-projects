#!/usr/bin/env python3
"""
Project 13 - Kalshi vs Polymarket price discovery.
Step 00: PULL raw high-frequency price series for matched FOMC decision contracts.

Matched-event family: FOMC rate-decision contracts. For each FOMC meeting both venues
list mutually-exclusive outcome markets (No change / 25bp cut / 50+ cut / 25bp hike /
50+ hike). Settlement is the SAME FOMC statement -> identical resolution (the student
verifies the exact wording line-by-line; see STUDENT_TASKS.md).

Kalshi  : GET /series/{s}/markets/{ticker}/candlesticks  (hourly close = YES prob, 0..1)
Polymarket: GET clob.polymarket.com/prices-history       (hourly YES-token price, 0..1)

Both venues cap request ranges, so we pull in chunks. We restrict to the last LOOKBACK
days before each meeting (where liquidity / price discovery concentrate). Every file and
row count is logged to logs/00_pull.log.
"""
import os, sys, time, json, csv, datetime as dt, calendar
import requests

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(HERE, 'data', 'raw')
LOG  = os.path.join(HERE, 'logs', '00_pull.log')
os.makedirs(os.path.join(RAW, 'kalshi'), exist_ok=True)
os.makedirs(os.path.join(RAW, 'poly'), exist_ok=True)

KBASE = 'https://api.elections.kalshi.com/trade-api/v2'
PHIST = 'https://clob.polymarket.com/prices-history'
GAMMA = 'https://gamma-api.polymarket.com'
NOW           = dt.datetime(2026, 7, 7)   # data-cut / "today"
KALSHI_CHUNK  = 25           # days per Kalshi candlestick request
POLY_CHUNK    = 6            # days per Polymarket prices-history request (hourly)

def log(msg):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {msg}"
    print(line)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def ts(d):
    return int(calendar.timegm(d.timetuple()))

def get(url, params, tries=5):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=45)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(1.5 * (i + 1)); continue
            return None
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None

# ---- matched FOMC meetings: (Kalshi event ticker, Polymarket event id, FOMC datetime UTC, resolved?) ----
# Kalshi's public API retains candlestick history only for markets that resolved very
# recently OR are still open. That yields four matched FOMC meetings: the just-resolved
# June-2026 meeting (used for the resolving-news event study) plus three open meetings
# (Jul/Sep/Oct 2026) still actively trading. FOMC statements release 2:00pm ET.
MEETINGS = [
    ('KXFEDDECISION-26JUN', 101772, dt.datetime(2026, 6, 17, 18), True),
    ('KXFEDDECISION-26JUL', 287395, dt.datetime(2026, 7, 29, 18), False),
    ('KXFEDDECISION-26SEP', 481717, dt.datetime(2026, 9, 16, 18), False),
    ('KXFEDDECISION-26OCT', 606422, dt.datetime(2026, 10, 28, 18), False),
]

# Kalshi outcome code -> canonical outcome; Polymarket groupItemTitle -> canonical outcome
KALSHI_OUT = {'H0': 'no_change', 'C25': 'cut25', 'C26': 'cut50p',
              'H25': 'hike25', 'H26': 'hike50p'}
def poly_canon(title):
    t = (title or '').lower()
    if 'no change' in t: return 'no_change'
    if '50+' in t and 'decrease' in t: return 'cut50p'
    if '25' in t and 'decrease' in t: return 'cut25'
    if '50+' in t and 'increase' in t: return 'hike50p'
    if '25' in t and 'increase' in t: return 'hike25'
    return None

def parse_iso(s):
    if not s: return None
    return dt.datetime.strptime(s.replace('Z', '').split('.')[0], '%Y-%m-%dT%H:%M:%S')

def pull_kalshi(event_ticker, fomc):
    """Return dict outcome -> list[(ts, price, vol)] hourly close for each outcome market."""
    series = event_ticker.split('-')[0]           # KXFEDDECISION
    ev = get(f'{KBASE}/events/{event_ticker}', {'with_nested_markets': 'true'})
    if not ev or 'event' not in ev:
        log(f'  KALSHI {event_ticker}: event not found'); return {}, {}
    mkts = ev['event'].get('markets', [])
    end_all = min(fomc, NOW) + dt.timedelta(days=1)
    out, result = {}, {}
    for m in mkts:
        code = m['ticker'].split('-')[-1]
        oc = KALSHI_OUT.get(code)
        if oc is None:
            continue
        result[oc] = m.get('result')
        start = parse_iso(m.get('open_time')) or (fomc - dt.timedelta(days=300))
        rows = []
        c0 = start
        while c0 < end_all:
            c1 = min(c0 + dt.timedelta(days=KALSHI_CHUNK), end_all)
            j = get(f'{KBASE}/series/{series}/markets/{m["ticker"]}/candlesticks',
                    {'start_ts': ts(c0), 'end_ts': ts(c1), 'period_interval': 60})
            for c in (j or {}).get('candlesticks', []):
                pd_ = c.get('price', {}).get('close_dollars')
                if pd_ not in (None, '', 'null'):
                    rows.append((int(c['end_period_ts']), float(pd_),
                                 float(c.get('volume_fp') or 0)))
            c0 = c1
            time.sleep(0.03)
        rows = sorted(set(rows))
        out[oc] = rows
        log(f'  KALSHI {event_ticker} {oc:9s} {code:4s}: {len(rows)} hourly bars')
    return out, result

def pull_poly(event_id, fomc):
    ev = get(f'{GAMMA}/events/{event_id}', {})
    if not ev:
        log(f'  POLY {event_id}: event not found'); return {}, {}
    end_all = min(fomc, NOW) + dt.timedelta(days=1)
    out, res = {}, {}
    for m in ev.get('markets', []):
        oc = poly_canon(m.get('groupItemTitle'))
        if oc is None:
            continue
        try:
            toks = json.loads(m['clobTokenIds']); outs = json.loads(m['outcomes'])
        except Exception:
            continue
        yes_i = outs.index('Yes') if 'Yes' in outs else 0
        tok = toks[yes_i]
        try:
            op = json.loads(m.get('outcomePrices') or '[]')
            res[oc] = 'yes' if (op and float(op[yes_i]) > 0.5) else 'no'
        except Exception:
            res[oc] = None
        start = parse_iso(m.get('startDate')) or (fomc - dt.timedelta(days=300))
        rows = []
        c0 = start
        while c0 < end_all:
            c1 = min(c0 + dt.timedelta(days=POLY_CHUNK), end_all)
            j = get(PHIST, {'market': tok, 'startTs': ts(c0), 'endTs': ts(c1), 'fidelity': 60})
            for h in (j or {}).get('history', []):
                rows.append((int(h['t']), float(h['p'])))
            c0 = c1
            time.sleep(0.03)
        rows = sorted(set(rows))
        out[oc] = rows
        log(f'  POLY   {event_id} {oc:9s}: {len(rows)} hourly points')
    return out, res

def main():
    open(LOG, 'w').close()
    # clear any orphaned files from earlier runs
    for sub in ('kalshi', 'poly'):
        d = os.path.join(RAW, sub)
        for f in os.listdir(d):
            if f.endswith('.csv'): os.remove(os.path.join(d, f))
    log(f'START pull  {len(MEETINGS)} matched FOMC meetings')
    manifest = []
    for kev, pid, fomc, resolved in MEETINGS:
        tag = kev.replace('KXFEDDECISION-', '')
        log(f'MEETING {tag}  FOMC={fomc.isoformat()}  resolved={resolved}  Kalshi={kev} Poly={pid}')
        kdata, kresult = pull_kalshi(kev, fomc)
        pdata, presult = pull_poly(pid, fomc)
        for oc in set(list(kdata) + list(pdata)):
            kr = kdata.get(oc, []); pr = pdata.get(oc, [])
            if kr:
                with open(os.path.join(RAW, 'kalshi', f'{tag}_{oc}.csv'), 'w', newline='') as f:
                    w = csv.writer(f); w.writerow(['ts', 'price', 'volume'])
                    w.writerows(kr)
            if pr:
                with open(os.path.join(RAW, 'poly', f'{tag}_{oc}.csv'), 'w', newline='') as f:
                    w = csv.writer(f); w.writerow(['ts', 'price'])
                    w.writerows(pr)
            manifest.append({'meeting': tag, 'fomc_utc': fomc.isoformat(), 'resolved': resolved,
                             'outcome': oc, 'kalshi_n': len(kr), 'poly_n': len(pr),
                             'kalshi_result': kresult.get(oc), 'poly_result': presult.get(oc)})
    # write manifest
    import pandas as pd
    mf = pd.DataFrame(manifest)
    mf.to_csv(os.path.join(RAW, 'manifest.csv'), index=False)
    log(f'DONE. manifest rows={len(mf)}  kalshi files={sum(mf.kalshi_n>0)}  poly files={sum(mf.poly_n>0)}')
    log(f'total kalshi bars={int(mf.kalshi_n.sum())}  total poly points={int(mf.poly_n.sum())}')

if __name__ == '__main__':
    main()
