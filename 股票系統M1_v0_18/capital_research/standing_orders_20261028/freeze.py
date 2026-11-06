"""Freeze original-job paths, manual expectations and old-engine controls."""
import hashlib
import json
import subprocess
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent.parent
REPO=PROJECT.parent


def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    from capital_research.core import fingerprint,timestamp
    from capital_research.execution import simulate
    from capital_research.continuity import make_checkpoint
    from capital_research.cash_action import evaluate
    cash=PROJECT/'capital_research/cash_execution_20261028'
    qty=PROJECT/'capital_research/quantity_replay_20261026'
    source_paths=[cash/'actual/opening-B20/result.json',cash/'cases/exited-A-buy-B20/input.json',
        cash/'cases/zero-capacity-unfilled/input.json',cash/'cases/limit-up-unfilled/input.json',cash/'cases/partial-7-cancelled-13/input.json',
        qty/'after-final/partial-then-independent/actual.json',qty/'cases/limit-up-unfilled/input.json',
        PROJECT/'capital_research/rejected_reassessment_20261026/after-final/future-partial/input.json']
    protected=[PROJECT/'capital_research'/n for n in ('core.py','continuity.py','cash_action.py','cash_action_execution.py',
        'quantity_candidates.py','fact_lineage.py','eligibility.py','close_clock.py','reassessment_history.py','transition_risk.py')]
    protected += [PROJECT/'rotation_research/action_ledger.py',PROJECT/'rotation_research/core.py']+source_paths
    old_exec=PROJECT/'capital_research/execution.py';(ROOT/'baseline').mkdir(exist_ok=True)
    with (ROOT/'baseline/execution.py').open('x') as f:f.write(old_exec.read_text())
    save(ROOT/'intake.json',dict(baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        original_execution=info(old_exec),archived_execution=info(ROOT/'baseline/execution.py'),
        protected=[info(p) for p in protected],new_market_quotes=0,new_calendar_rows=0))
    base=load(source_paths[0])['run']['execution_job']
    q=load(source_paths[5])['replay']['rounds'][0]['execution_job']
    first=deepcopy(q['tape']);tail=load(source_paths[1])['execution_spec']['tape']
    zero_tail=load(source_paths[2])['execution_spec']['tape']
    roots={}
    for name in ['partial-fill','partial-no-fill','expired','revoked','late-published','payable-only','never-filled']:
        j=deepcopy(base);j['observed_until']='2026-01-12T16:00:00+08:00';j['tape']=deepcopy(first+tail)
        if name in ('partial-no-fill','expired'):j['tape']=deepcopy(first+zero_tail)
        if name=='expired':j['orders'][0]['expires_at']=q['orders'][1]['expires_at']
        if name in ('revoked','late-published'):
            declaration=load(source_paths[4])['action_input']['decision_template']['assets']['B']['evidence'][0]['validity']['invalidation']
            if name=='late-published':declaration['occurred_at']='2026-01-06T08:00:00+08:00'
            j['decision_input']['assets']['B']['evidence'][0]['validity']['invalidation']=declaration
            later=load(source_paths[4])['execution_spec']['tape'][-1]
            j['tape']=deepcopy(first+zero_tail+[later])
        if name=='payable-only':j['tape']=deepcopy(base['tape'])
        if name=='never-filled':
            first_up=load(source_paths[6])['rounds'][0]['tape']
            j['tape']=deepcopy(first_up+load(source_paths[3])['execution_spec']['tape'])
        roots[name]=j
    roots['past-reassessment']=load(source_paths[7])
    cuts={n:'2026-01-06T16:00:00+08:00' for n in roots};cuts['past-reassessment']='2026-01-09T16:00:00+08:00'
    expected={
        'partial-fill':dict(final_B='20',final_C='4',final_cash='677.600',remaining='0',order_status='FILLED',new_segment_fills=1,prefix_payable='141.140'),
        'partial-no-fill':dict(final_B='7',final_C='4',final_cash='938.860',remaining='13',order_status='EXPIRED_UNFILLED',new_segment_fills=0,prefix_payable='141.140'),
        'expired':dict(final_B='7',final_C='4',final_cash='938.860',remaining='13',order_status='EXPIRED_UNFILLED',new_segment_fills=0,prefix_payable='141.140'),
        'revoked':dict(final_B='7',final_C='4',final_cash='938.860',remaining='13',order_status='CANCELLED_EVIDENCE',new_segment_fills=0,prefix_payable='141.140'),
        'late-published':dict(final_B='7',final_C='4',final_cash='938.860',remaining='13',order_status='CANCELLED_EVIDENCE',new_segment_fills=0,prefix_payable='141.140'),
        'payable-only':dict(final_B='20',final_C='4',final_cash='678.600',remaining='0',order_status='FILLED',new_segment_fills=0,prefix_payable='401.400'),
        'never-filled':dict(final_B='0',final_C='4',final_cash='1080',remaining='20',order_status='EXPIRED_UNFILLED',new_segment_fills=0,prefix_payable='0'),
        'past-reassessment':dict(past_attempt_count=1,new_decisions=0,new_segment_fills=0)}
    save(ROOT/'manual-expected.json',dict(cases=expected,origin_capital='1180',general_reserve='100',
        first_buy='7*20.02+ceil(max(1,140.14*.001))=141.14',remaining_buy='13*20.02+1=261.26',
        final_cash='1000-141.14+80-261.26=677.60',remaining_limit_reserve='13*(20.03*1.001)+1=261.65039'))
    names=[];requests={}
    for name,j in roots.items():
        cut=cuts[name];save(ROOT/'cases'/name/'root-input.json',j);save(ROOT/'cases'/name/'expected.json',dict(status='CONTINUED_ORIGINAL_ORDERS',**expected[name]))
        prefix=deepcopy(j);prefix['observed_until']=cut;prefix['tape']=[o for o in j['tape'] if timestamp(o['at'])<=timestamp(cut)]
        save(ROOT/'cases'/name/'prefix-input.json',prefix)
        prior=simulate(prefix);full=simulate(j)
        assert prior['status']==full['status']=='SYNTHETIC_EXECUTION_REPLAY',name
        cp=make_checkpoint(j['ledger_input'],prior,through_at=cut)
        save(ROOT/'before'/name/'prefix-execution.json',prior);save(ROOT/'before'/name/'checkpoint.json',cp);save(ROOT/'before'/name/'full-execution.json',full)
        origin=j['ledger_input'];coverage=[]
        for row in origin['calendar']:
            day=row['date']
            if row['trading'] and j['decision_input']['data_cutoff'][:10]<day<=origin['end']:
                coverage.append(dict(date=day,source_ids=['fixture'],qualification='EXPLICIT_SYNTHETIC_COMPLETE_EXECUTION_OPPORTUNITIES',
                    observation_ids=[fingerprint(o) for o in j['tape'] if o['at'][:10]==day],no_other_execution_opportunities=True))
        path=dict(schema='capital-synthetic-order-path/0.1',version='frozen-synthetic-path/0.1',
            qualification='EXPLICIT_SYNTHETIC_COMPLETE_PATH_NOT_MARKET_PROOF',source_ids=['fixture'],
            origin_ledger_input_id=fingerprint(origin),start_at=j['decision_input']['data_cutoff'],through_at=j['observed_until'],
            observations=deepcopy(j['tape']),session_coverage=coverage)
        r=dict(schema='capital-standing-order-resume-input/0.1',synthetic=True,root_job=j,checkpoint=cp,
            expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=prior['latest_decision_id'],path=path,
            expected_path_id=fingerprint(path),segment_tape=[o for o in j['tape'] if timestamp(o['at'])>timestamp(cut)],
            observed_until=j['observed_until'],resume_at=(timestamp(cut)+timedelta(minutes=1)).isoformat())
        save(ROOT/'cases'/name/'input.json',r);requests[name]=r;names.append(name)
    def negative(name,r,reason):
        save(ROOT/'cases'/name/'input.json',r);save(ROOT/'cases'/name/'expected.json',dict(status='REFUSED',reason=reason,tail_observations=0));names.append(name)
    original=requests['partial-fill']
    x=deepcopy(original);x['expected_latest_decision_id']='wrong';negative('wrong-predecessor',x,'EXACT_LATEST_PREDECESSOR_REQUIRED')
    x=deepcopy(original);x['root_job']['ledger_input']['opening']['cash']='9999';negative('changed-origin',x,'ORIGIN_LEDGER_BINDING_REQUIRED')
    x=deepcopy(original);x['root_job']['orders'][0]['limit_price']='20.09';negative('changed-order-limit',x,'PREFIX_EXECUTION_MISMATCH')
    for name,field in [('missing-fills','fills'),('missing-orders','order_history')]:
        x=deepcopy(original);x['checkpoint']['execution_result'][field]=[];negative(name,x,'Execution fingerprint conflict')
    x=deepcopy(original);x['checkpoint']['execution_result']['fills'].append(deepcopy(x['checkpoint']['execution_result']['fills'][0]));negative('duplicate-fill',x,'Execution fingerprint conflict')
    x=deepcopy(original);x['segment_tape'].append(deepcopy(x['segment_tape'][0]));negative('duplicate-segment-observation',x,'SEGMENT_TAPE_MUST_MATCH_COMPLETE_PATH')
    x=deepcopy(original);x['segment_tape'].pop();negative('missing-middle-observation',x,'SEGMENT_TAPE_MUST_MATCH_COMPLETE_PATH')
    x=deepcopy(original);x['path']['observations'].insert(0,deepcopy(x['path']['observations'][0]));x['root_job']['tape']=deepcopy(x['path']['observations']);x['expected_path_id']=fingerprint(x['path']);negative('duplicate-full-path',x,'DUPLICATE_OR_UNORDERED_PATH_OBSERVATIONS')
    x=deepcopy(original);x['path']['session_coverage']=[s for s in x['path']['session_coverage'] if s['date']!='2026-01-07'];x['expected_path_id']=fingerprint(x['path']);negative('missing-empty-session-proof',x,'COMPLETE_SESSION_COVERAGE_REQUIRED')
    x=deepcopy(original);x['path']['source_ids']=['unknown'];x['expected_path_id']=fingerprint(x['path']);negative('unknown-path-source',x,'BOUND_SYNTHETIC_PATH_SOURCE_REQUIRED')
    x=deepcopy(original);x['orders']=[];negative('new-order-override',x,'EXACT_STANDING_CONTINUATION_REQUIRED')
    x=deepcopy(original);x['observed_until']='2026-01-13T16:00:00+08:00';negative('beyond-origin-window',x,'IN_WINDOW_ADVANCING_WATERMARK_REQUIRED')
    x=deepcopy(original);x['resume_at']='2026-01-06T15:00:00+08:00';negative('before-close-known',x,'CHECKPOINT_NOT_YET_KNOWN')
    x=deepcopy(original);x['root_job']['reassessments']=[dict(id='new-review',decision_input=dict(decision_at='2026-01-08T17:00:00+08:00'))];negative('future-new-review',x,'NEW_REASSESSMENT_NOT_IMPLEMENTED')
    # Self-consistent checkpoint from another path, not just a broken hash.
    fake=deepcopy(load(ROOT/'cases/partial-fill/prefix-input.json'));fake['tape'][-1]['capacity_shares']='0'
    wrong_execution=simulate(fake);wrong_cp=make_checkpoint(fake['ledger_input'],wrong_execution,through_at=fake['observed_until'])
    save(ROOT/'before/other-path/prefix-input.json',fake);save(ROOT/'before/other-path/checkpoint.json',wrong_cp)
    x=deepcopy(original);x['checkpoint']=wrong_cp;x['expected_checkpoint_id']=wrong_cp['checkpoint_id'];negative('self-consistent-other-path',x,'PREFIX_EXECUTION_MISMATCH')
    # Existing new-decision adapter still rejects a live order; keep that defense.
    old_request=load(cash/'cases/opening-cash-first-B/input.json') if (cash/'cases/opening-cash-first-B/input.json').exists() else load(PROJECT/'capital_research/cash_action_20261028/cases/opening-cash-first-B/input.json')
    cp=original['checkpoint'];old_request['account_source']=dict(kind='CHECKPOINT',checkpoint=cp,expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=cp['execution_result']['latest_decision_id'])
    old_request['decision_template']['data_cutoff']=cp['state']['through_at'];old_request['decision_template']['decision_at']=original['resume_at']
    save(ROOT/'before/new-decision-input.json',old_request);save(ROOT/'before/new-decision-actual.json',evaluate(old_request))
    save(ROOT/'case-index.json',dict(positive=list(roots),negative=names[len(roots):],all=names,market_samples=0,
        prefix_and_full_controls='baseline original engine, not independent market performance',new_market_quotes=0,new_calendar_rows=0))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='frozen.json']))
    print('Frozen',len(roots),'positive and',len(names)-len(roots),'negative cases; original prefix/full controls preserved')


if __name__=='__main__':main()
