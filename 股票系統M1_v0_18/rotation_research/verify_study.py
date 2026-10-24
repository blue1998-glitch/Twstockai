"""Actual archived-data, ledger and replay verification; no strategy approval."""
import copy, hashlib, json, subprocess
from pathlib import Path
from decimal import Decimal as D
from .core import compare, replay, evidence
from .study import HERE, ROOT

def main():
    out=HERE/'generated';data=json.loads((out/'input.json').read_text());rs=json.loads((out/'results.json').read_text())
    checks=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    for source in json.loads((out/'sources.json').read_text()):
        p=ROOT/source['path'];raw=p.read_bytes()
        check('source-sha:'+p.name,hashlib.sha256(raw).hexdigest()==source['sha256'])
        old=subprocess.check_output(['git','show',data['source_commit']+':'+source['path']],cwd=ROOT)
        check('git-source-preserved:'+p.name,old==raw)
    groups={}
    for r in rs:
        groups.setdefault((r['cutoff'],r['incumbent'],r['horizon']),[]).append(r)
        check('eligibility:'+r['case_id'],not r['policy_authorized'] and not r['historical_signal_eligible'] and r['research_only'])
        check('decision-order:'+r['case_id'],all(t['decision_cutoff']<t['date'] for t in r['trades']))
        q={r['incumbent']:data['initial_shares'],r['candidate']:0};cash=D(data['initial_cash'])
        for point,allocation in zip(r['nav'],r['allocation']):
            for t in (t for t in r['trades'] if t['date']==point['date']):
                cash+=D(t['cash_flow']);q[t['code']]+=t['shares']*(1 if t['side']=='BUY' else -1)
                asset=data['assets'][t['code']];prior=next(b for b in asset['bars'] if b['date']==t['decision_cutoff'])
                check('capacity:'+r['case_id']+t['date']+t['side'],D(t['shares'])<=D(prior['volume'])*D(data['execution']['participation']))
            check('account:'+r['case_id']+point['date'],cash==D(allocation['cash']) and q==allocation['shares'] and cash>=0 and min(q.values())>=0)
        check('end-cost:'+r['case_id'],D(r['metrics']['end_mark_equity'])-D(r['metrics']['estimated_terminal_exit_cost'])==D(r['metrics']['end_net_liquidation_equity']))
    for key,g in groups.items():check('same-capital:'+str(key),len(g)==6 and len({r['metrics']['initial_equity'] for r in g})==1)
    for cutoff in ('2026-01-02','2026-08-03'):
        for a,b in [('1101','2884'),('2884','1101')]:
            long=compare(data,a,b,cutoff,40);short=compare(data,a,b,cutoff,5)
            end=short['hold']['nav'][-1]['date'];prefix=copy.deepcopy(data)
            for asset in prefix['assets'].values():asset['bars']=[x for x in asset['bars'] if x['date']<=end]
            replayed=compare(prefix,a,b,cutoff,5)
            check('full-prefix:'+cutoff+a,short==replayed)
            check('future-append:'+cutoff+a,all(long[p]['nav'][:5]==short[p]['nav'] for p in long))
            poisoned=copy.deepcopy(data)
            for asset in poisoned['assets'].values():
                for bar in asset['bars']:
                    if bar['date']>cutoff and not bar.get('missing'):
                        for k in ('open','high','low','close'):bar[k]=str(D(bar[k])*100)
            check('future-price-poison:'+cutoff+a,all(evidence(data['assets'][c],cutoff)==evidence(poisoned['assets'][c],cutoff) for c in data['assets']))
    missing=[(c,b['date']) for c,a in data['assets'].items() for b in a['bars'] if b.get('missing')]
    check('retained-no-quotes',missing==[('1101','2025-08-13'),('2884','2025-11-05')])
    check('strict-block',False) if data['strict'] else None
    check('refused-40-sessions',len(json.loads((out/'unavailable.json').read_text()))==2)
    result={'status':'PASS','assertions':len(checks),'source_commit':data['source_commit'],
            'comparisons':len(groups),'plans':len(rs),'checks':checks,
            'investment_validated':False,'total_return_validated':False}
    (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
if __name__=='__main__':main()
