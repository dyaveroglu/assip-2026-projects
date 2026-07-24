#!/usr/bin/env python3
"""
Project 12 (Half-Cent Tick) - Step 20: DiD estimation + tables.

Design: stock x day panel, 4 weeks pre vs 4 weeks post the Nov 3 2025 compliance
date. Treated = tick-constrained (Sept dollar quoted spread <= $0.015); control =
wide-spread. Estimand = treated x post (the DiD). Outcomes: relative quoted spread
(bps), dollar quoted spread (cents), closing effective-spread proxy (bps).
SE clustered by stock; robustness double-clustered by stock and day.

We report the result HONESTLY whatever its sign/significance (the daily closing
NBBO cannot resolve sub-penny intraday tightening, so a null here is a
measurement-resolution result, not proof the reform did nothing).
"""
import os, datetime, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, statsmodels.formula.api as smf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, 'data', 'processed'); OUT = os.path.join(HERE, 'output', 'tables')
os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(HERE, 'logs'); STAMP = datetime.date.today().isoformat()
logf = open(os.path.join(LOG, f'did_{STAMP}.log'), 'w')
def log(m):
    line=f'[{datetime.datetime.now().isoformat(timespec="seconds")}] {m}'; print(line); logf.write(line+'\n'); logf.flush()

did  = pd.read_csv(os.path.join(PROC, 'panel_did.csv'), parse_dates=['date'])
full = pd.read_csv(os.path.join(PROC, 'panel_full.csv'), parse_dates=['date'])
did['dstr'] = did.date.dt.strftime('%Y%m%d')
log(f'DiD panel: {len(did)} stock-days, {did.permno.nunique()} stocks')

def cl(m_formula, data, groups):
    return smf.ols(m_formula, data=data).fit(cov_type='cluster', cov_kwds={'groups': data[groups]})

# ===== Table 1: covariate balance (pre-period means, treated vs control) =====
pre = did[did.post == 0]
bvars = {'rqs_bps_w':'Relative quoted spread (bps)','dqs_c_w':'Dollar quoted spread (cents)',
         'lprice':'ln(price)','ldvol':'ln($ volume)','lnumtrd':'ln(#trades)'}
rows=[]
for v,lbl in bvars.items():
    a = pre[pre.treated==1][v]; b = pre[pre.treated==0][v]
    # two-sample t (stock-day obs; illustrative)
    from scipy import stats
    t,pval = stats.ttest_ind(a.dropna(), b.dropna(), equal_var=False)
    rows.append({'var':lbl,'treated_mean':a.mean(),'control_mean':b.mean(),
                 'diff':a.mean()-b.mean(),'t':t})
t1 = pd.DataFrame(rows); t1.to_csv(os.path.join(OUT,'t1_balance.csv'), index=False)
log('T1 balance (pre-period):\n'+t1.round(3).to_string(index=False))

# ===== Table 2: 2x2 mean spreads (relative & dollar) =====
def cell(v):
    m = did.groupby(['treated','post'])[v].mean().unstack()
    m.columns=['pre','post']; m['change']=m['post']-m['pre']
    return m
c_rqs = cell('rqs_bps_w'); c_dqs = cell('dqs_c_w')
did22 = pd.DataFrame({
    'group':['Control (wide)','Treated (tick-constrained)','DiD'],
    'rqs_pre':[c_rqs.loc[0,'pre'], c_rqs.loc[1,'pre'], np.nan],
    'rqs_post':[c_rqs.loc[0,'post'], c_rqs.loc[1,'post'], np.nan],
    'rqs_chg':[c_rqs.loc[0,'change'], c_rqs.loc[1,'change'],
               c_rqs.loc[1,'change']-c_rqs.loc[0,'change']],
    'dqs_pre':[c_dqs.loc[0,'pre'], c_dqs.loc[1,'pre'], np.nan],
    'dqs_post':[c_dqs.loc[0,'post'], c_dqs.loc[1,'post'], np.nan],
    'dqs_chg':[c_dqs.loc[0,'change'], c_dqs.loc[1,'change'],
               c_dqs.loc[1,'change']-c_dqs.loc[0,'change']],
})
did22.to_csv(os.path.join(OUT,'t2_did2x2.csv'), index=False)
log('T2 2x2 means (rqs bps, dqs cents):\n'+did22.round(4).to_string(index=False))

# ===== Table 3: main DiD, progressive specs (DV = relative quoted spread bps) =====
specs = {
 '(1) 2x2, no FE'       : ('rqs_bps_w ~ treated + post + tp', 'permno'),
 '(2) + Stock FE'       : ('rqs_bps_w ~ post + tp + C(permno)', 'permno'),
 '(3) TWFE'             : ('rqs_bps_w ~ tp + C(permno) + C(dstr)', 'permno'),
 '(4) TWFE + controls'  : ('rqs_bps_w ~ tp + lprice + ldvol + C(permno) + C(dstr)', 'permno'),
}
res={}
for name,(f,g) in specs.items():
    res[name]=cl(f, did, g)
def grab(m):
    return {'coef':m.params.get('tp',np.nan),'t':m.tvalues.get('tp',np.nan),
            'se':m.bse.get('tp',np.nan),'N':int(m.nobs),'r2':m.rsquared}
t3 = pd.DataFrame([{'spec':k, **grab(v)} for k,v in res.items()])
# add a double-clustered robustness of spec (3)
from statsmodels.formula.api import ols as _ols
m3 = _ols('rqs_bps_w ~ tp + C(permno) + C(dstr)', data=did).fit(
        cov_type='cluster', cov_kwds={'groups': np.stack([did.permno, did.date.view('int64')],axis=1)})
t3 = pd.concat([t3, pd.DataFrame([{'spec':'(3d) TWFE, cluster stock+day',
        'coef':m3.params['tp'],'t':m3.tvalues['tp'],'se':m3.bse['tp'],
        'N':int(m3.nobs),'r2':m3.rsquared}])], ignore_index=True)
t3.to_csv(os.path.join(OUT,'t3_did_main.csv'), index=False)
log('T3 main DiD (DV=relative quoted spread, bps; treated x post):\n'+t3.round(4).to_string(index=False))

# ===== Table 4: alt outcomes (dollar spread cents; effective-spread proxy bps) =====
alt = {
 'Dollar spread (cents), TWFE'     : ('dqs_c_w ~ tp + C(permno) + C(dstr)', 'dqs_c_w'),
 'Dollar spread (cents), +controls': ('dqs_c_w ~ tp + lprice + ldvol + C(permno) + C(dstr)', 'dqs_c_w'),
 'Eff-spread proxy (bps), TWFE'    : ('espr_bps_w ~ tp + C(permno) + C(dstr)', 'espr_bps_w'),
 'Eff-spread proxy (bps), +ctrl'   : ('espr_bps_w ~ tp + lprice + ldvol + C(permno) + C(dstr)', 'espr_bps_w'),
}
rows=[]
for name,(f,dv) in alt.items():
    m=cl(f, did, 'permno')
    rows.append({'spec':name,'dv':dv,'coef':m.params['tp'],'t':m.tvalues['tp'],
                 'se':m.bse['tp'],'N':int(m.nobs),'r2':m.rsquared})
t4=pd.DataFrame(rows); t4.to_csv(os.path.join(OUT,'t4_altoutcomes.csv'), index=False)
log('T4 alternative outcomes:\n'+t4.round(4).to_string(index=False))

# ===== Table 5: event-study (weekly DiD coefficients, base week = -1) =====
ev = full[(full.evt_week >= -6) & (full.evt_week <= 6)].copy()
ev['dstr'] = ev.date.dt.strftime('%Y%m%d')
# interaction of treated with each event-week dummy, omit week -1 (base)
def wk_name(w):
    return f'twk_m{abs(w)}' if w < 0 else f'twk_p{w}'
weeks = sorted([w for w in ev.evt_week.unique() if w != -1])
for w in weeks:
    ev[wk_name(w)] = ((ev.evt_week==w) & (ev.treated==1)).astype(int)
terms = ' + '.join([wk_name(w) for w in weeks])
mev = smf.ols(f'rqs_bps_w ~ {terms} + C(permno) + C(dstr)', data=ev).fit(
        cov_type='cluster', cov_kwds={'groups': ev.permno})
erows=[]
for w in sorted(ev.evt_week.unique()):
    if w==-1:
        erows.append({'evt_week':w,'coef':0.0,'se':0.0,'t':np.nan}); continue
    k=wk_name(w)
    erows.append({'evt_week':w,'coef':mev.params[k],'se':mev.bse[k],'t':mev.tvalues[k]})
t5=pd.DataFrame(erows).sort_values('evt_week'); t5.to_csv(os.path.join(OUT,'t5_eventstudy.csv'), index=False)
log('T5 event-study (weekly treated coefs vs week -1 base):\n'+t5.round(4).to_string(index=False))

# ===== Table 6: placebo (fake event = Oct 6, using pre-period only) =====
plb = full[(full.date >= '2025-09-08') & (full.date <= '2025-10-31')].copy()
plb['dstr']=plb.date.dt.strftime('%Y%m%d')
plb['fpost']=(plb.date >= '2025-10-06').astype(int); plb['ftp']=plb.treated*plb.fpost
mp = smf.ols('rqs_bps_w ~ ftp + C(permno) + C(dstr)', data=plb).fit(
        cov_type='cluster', cov_kwds={'groups':plb.permno})
# also real donut robustness: control = all dqs>0.015 already; alt threshold treated<=0.012
t6 = pd.DataFrame([{'test':'Placebo fake-event 2025-10-06 (pre-period only)',
                    'coef':mp.params['ftp'],'t':mp.tvalues['ftp'],'se':mp.bse['ftp'],'N':int(mp.nobs)}])
t6.to_csv(os.path.join(OUT,'t6_placebo.csv'), index=False)
log('T6 placebo:\n'+t6.round(4).to_string(index=False))

# ===== Table 7: within-group paired pre/post changes (descriptive) =====
from scipy import stats as _st
def within(v, grp):
    piv = did[did.treated==grp].groupby(['permno','post'])[v].mean().unstack().dropna()
    piv.columns=['pre','post']; ch=piv['post']-piv['pre']
    t,pval=_st.ttest_rel(piv['post'],piv['pre'])
    return {'pre':piv['pre'].mean(),'post':piv['post'].mean(),'chg':ch.mean(),
            'pct':100*ch.mean()/piv['pre'].mean(),'t':t,'p':pval,'n':len(piv)}
rows=[]
for lbl,grp in [('Treated (tick-constrained)',1),('Control (wide)',0)]:
    for v,vl in [('dqs_c_w','Dollar spread (cents)'),('rqs_bps_w','Relative spread (bps)')]:
        d=within(v,grp); d.update({'group':lbl,'measure':vl}); rows.append(d)
t7=pd.DataFrame(rows)[['group','measure','pre','post','chg','pct','t','p','n']]
t7.to_csv(os.path.join(OUT,'t7_withingroup.csv'), index=False)
log('T7 within-group paired pre/post changes:\n'+t7.round(4).to_string(index=False))

# ===== Table 8: penny-grid censoring of the daily close (mechanism) =====
full['subpenny']=(full.dqs_c<0.99).astype(int)
full['atpenny']=((full.dqs_c>=0.99)&(full.dqs_c<1.01)).astype(int)
PRE0,PRE1='2025-10-06','2025-10-31'; POST0,POST1='2025-11-03','2025-11-28'
rows=[]
for lbl,grp in [('Treated (tick-constrained)',1),('Control (wide)',0)]:
    for plbl,(d0,d1) in [('Pre',(PRE0,PRE1)),('Post',(POST0,POST1))]:
        s=full[(full.treated==grp)&(full.date>=d0)&(full.date<=d1)]
        rows.append({'group':lbl,'period':plbl,'n':len(s),
                     'share_subpenny':s.subpenny.mean(),'share_at_1c':s.atpenny.mean(),
                     'mean_dqs_c':s.dqs_c.mean()})
t8=pd.DataFrame(rows); t8.to_csv(os.path.join(OUT,'t8_censoring.csv'), index=False)
log('T8 penny-grid censoring of closing quotes:\n'+t8.round(4).to_string(index=False))

# minimum detectable effect (MDE) note: 2.8*SE of preferred spec
pref = res['(4) TWFE + controls']
mde = 2.8*pref.bse['tp']
log(f'Preferred spec (4): DiD={pref.params["tp"]:+.4f} bps (t={pref.tvalues["tp"]:.2f}), '
    f'95%CI=[{pref.params["tp"]-1.96*pref.bse["tp"]:+.3f},{pref.params["tp"]+1.96*pref.bse["tp"]:+.3f}], '
    f'~MDE(80% power)={mde:.3f} bps')
log('DONE - tables written to output/tables/')
logf.close()
