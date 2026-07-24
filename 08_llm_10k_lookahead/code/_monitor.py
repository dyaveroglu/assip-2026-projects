import json, os, time, collections
p='/mnt/d/ccli/assip26/08_llm_10k_lookahead/data/interim/llm_scores.jsonl'
TARGET=55   # complete filings (both scores) desired
CAP=95*60   # seconds
t0=time.time()
while True:
    recs=[json.loads(l) for l in open(p)] if os.path.exists(p) else []
    ok=[r for r in recs if r.get('score') is not None]
    d=collections.defaultdict(set)
    win={}
    for r in ok:
        d[r['id']].add(r['cond']); win[r['id']]=r['window']
    comp=[k for k,v in d.items() if {'raw','anon'}<=v]
    npre=sum(1 for k in comp if win[k]=='pre'); npost=sum(1 for k in comp if win[k]=='post')
    el=int(time.time()-t0)
    print(f'[{el}s] ok_calls={len(ok)} complete={len(comp)} (pre={npre} post={npost})', flush=True)
    # stop if enough in BOTH windows or time cap or scorer finished
    scorer_done = not os.system("pgrep -f 10_llm_score.py >/dev/null 2>&1")==0
    if (len(comp)>=TARGET and npre>=20 and npost>=20) or el>CAP:
        print('STOP: target/cap reached', flush=True); break
    time.sleep(60)
