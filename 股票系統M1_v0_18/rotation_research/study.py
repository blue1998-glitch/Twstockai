"""Reproducible small-sample study; archived official responses only.

Run from project directory: python3 -m rotation_research.study
Selection: first saved session each month, both pair directions, no winners filter.
"""
from pathlib import Path
import csv, hashlib, json
from .core import compare, evidence

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
HEAD='9dd0554f723cb598f9c88f2e0928dead28fa6166'

def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def build_input():
    source=HERE.parent/'pressure_chart/data/history-20261018/raw'
    manifest=[];assets={}
    for code in ('1101','2884'):
        bars=[]
        for p in sorted(source.glob(code+'_*.json')):
            if p.name.endswith('_meta.json'):continue
            x=json.loads(p.read_text())
            if x.get('stat') != 'OK': raise ValueError('Source status')
            raw=p.read_bytes();meta=json.loads(p.with_name(p.stem+'_meta.json').read_text())
            sha=hashlib.sha256(raw).hexdigest()
            if sha != meta['sha256']:raise ValueError('Archived response/meta mismatch')
            manifest.append({'path':str(p.relative_to(ROOT)),'sha256':sha,'url':meta['url'],
                             'captured_at':meta['fetched_at_utc'],'rows':len(x['data'])})
            for row in x['data']:
                year,month,day=map(int,row[0].split('/'));date=f'{year+1911:04d}-{month:02d}-{day:02d}'
                if not ('2025-07-01' <= date <= '2026-10-16'):continue
                vals=[v.replace(',','').strip() for v in row]
                bar=dict(zip(('date','volume','open','high','low','close'),
                             (date,vals[1],vals[3],vals[4],vals[5],vals[6])))
                if '--' in [bar[k] for k in ('open','high','low','close')]:
                    bar.update({k:None for k in ('open','high','low','close')})
                    bar['missing']=True;bar['missing_reason']='ARCHIVED_NO_QUOTE_NOT_IMPUTED'
                bars.append(bar)
        bars.sort(key=lambda b:b['date'])
        identity=hashlib.sha256(json.dumps(bars,sort_keys=True).encode()).hexdigest()
        assets[code]={'source_id':'archived-months:'+identity,'basis_id':'RAW:'+identity,
                      'volume_unit':'SHARES_REPORTED','bars':bars,'exchange':'TWSE',
                      'security_type':'COMMON_STOCK_EXISTING_PROJECT_SCOPE_NOT_NEW_MASTER_AUDIT'}
    return {'schema':'rotation-input/0.1','source_commit':HEAD,'mode':'RAW','strict':False,
            'proxy_window':20,'initial_shares':20000,'initial_cash':'0',
            'execution':{'fee_rate':'0.001425','minimum_fee':'20','sell_tax':'0.003',
                         'slippage_bps':'10','participation':'0.001','lot':1000,'settlement_lag':0},
            'eligibility':{'company_actions':'UNVERIFIED_INCOMPLETE',
                           'calendar':'MATCHED_SAVED_DATES_NOT_EXHAUSTIVE',
                           'historical_availability':'UNVERIFIED_RETROSPECTIVE_CAPTURE',
                           'real_execution':'NOT_ESTABLISHED_DAILY_OHLC_ONLY',
                           'price_basis':'EXPLICIT_RAW_RESEARCH_SELECTION_NOT_USER_CURRENT_TRADE_MODE'},
            'corporate_actions':[],'assets':assets},manifest

def main():
    out=HERE/'generated';out.mkdir(exist_ok=True)
    data,manifest=build_input();dump(out/'input.json',data);dump(out/'sources.json',manifest)
    dates=[b['date'] for b in data['assets']['1101']['bars']]
    selected=[next(d for d in dates if d.startswith(f'2026-{m:02d}')) for m in range(1,10)]
    design={'source_commit':HEAD,'selection':'FIRST_SAVED_SESSION_OF_EACH_MONTH_BOTH_DIRECTIONS',
            'cutoffs':selected,'horizons':[5,10,20,40],
            'development_period':'2026-01..2026-04','temporal_holdout':'2026-05..2026-09',
            'holdout_status':'TEMPORAL_PARTITION_ONLY_NOT_GENUINELY_UNSEEN_MARKET_VALIDATION',
            'parameter_selection':'FIXED_BEFORE_THIS_RUN_NO_BEST_PARAMETER_SELECTION',
            'proxies':'20 prior daily highs/lows, not approved structure',
            'plans':{'hold':'retain original A shares', 'full':'sell A at next open; buy B with modeled available cash',
                     'staged25':'25% initial A shares per new B price/volume evidence, up to 4 steps',
                     'staged50':'50% initial A shares per new B price/volume evidence, up to 2 steps',
                     'cash':'sell A at next open; no reinvestment/interest',
                     'delay5':'retain A five additional sessions; full switch on session 6'},
            'staging_event':'prior close > frozen B proxy AND prior close > previous close AND prior volume > previous volume',
            'sensitivity':'10/30 bps slippage and settled-cash T+2 variant at 20 sessions'}
    dump(out/'design.json',design)
    runs=[];unavailable=[];rows=[];sens=[]
    for cutoff in selected:
        period='development' if cutoff<'2026-05-01' else 'temporal_holdout'
        for a,b in [('1101','2884'),('2884','1101')]:
            for horizon in design['horizons']:
                try: result=compare(data,a,b,cutoff,horizon)
                except ValueError as e:
                    unavailable.append({'cutoff':cutoff,'A':a,'B':b,'horizon':horizon,'reason':str(e)});continue
                for plan,r in result.items():
                    r['period']=period;r['case_id']=f'{a}-{b}-{cutoff}-{horizon}-{plan}';runs.append(r)
                    rows.append({'case_id':r['case_id'],'period':period,'A':a,'B':b,'cutoff':cutoff,
                                 'horizon':horizon,'plan':plan,**r['metrics']})
            # Cost and cash-availability sensitivity are explicit competing assumptions.
            for slip,lag in [('30',0),('10',2)]:
                import copy
                d=copy.deepcopy(data);d['execution']['slippage_bps']=slip;d['execution']['settlement_lag']=lag
                try:
                    result=compare(d,a,b,cutoff,20)
                    sens.extend({'cutoff':cutoff,'A':a,'B':b,'plan':p,'slippage_bps':slip,'settlement_lag':lag,'metrics':r['metrics']} for p,r in result.items())
                except ValueError as e: unavailable.append({'cutoff':cutoff,'variant':[slip,lag],'reason':str(e)})
    dump(out/'results.json',runs);dump(out/'unavailable.json',unavailable);dump(out/'sensitivity.json',sens)
    with (out/'metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Display examples are predeclared calendar cases, never selected by future P&L.
    examples=[r for r in runs if r['horizon']==40 and r['cutoff'] in ('2026-01-02','2026-08-03')]
    dump(out/'chart-examples.json',examples)
    from .loop import replay_loop
    loops=[replay_loop(data,'2026-05-04','2026-10-16',policy)
           for policy in ('hold','full_review10','half_review10','cash_review10')]
    dump(out/'loop-results.json',loops)
    print(json.dumps({'runs':len(runs),'comparisons':len(runs)//6,'unavailable':len(unavailable),
                      'sensitivity_runs':len(sens),'bars':{c:len(a['bars']) for c,a in data['assets'].items()}}))
if __name__=='__main__': main()
