"""Finish intake after preserving an incompatible archived review binding."""
from .freeze import *

def main():
    from capital_research.core import fingerprint,timestamp,decide,resume_decision
    from capital_research.execution import simulate
    from capital_research.continuity import make_checkpoint,account_at_checkpoint
    requests={n:load(ROOT/'cases'/n/'input.json') for n in ['partial-fill','partial-no-fill','expired','revoked','late-published','payable-only','never-filled']}
    names=list(requests)
    old=load(ROOT/'cases/past-reassessment/root-input.json');j=deepcopy(old)
    cp=load(ROOT/'diagnostics/current-provisional-checkpoint.json')
    review=j['reassessments'][0];fresh=review['decision_input']
    fresh['account']=account_at_checkpoint(cp,decision_at=fresh['decision_at'],cancelled_order_ids=review['cancelled_order_ids'])
    review['checkpoint_id']=cp['checkpoint_id']
    review['decision_id']=resume_decision(decide(j['decision_input']),fresh,checkpoint=cp,cancelled_order_ids=review['cancelled_order_ids'])['decision']['decision_id']
    name='past-reassessment-current';cut='2026-01-09T16:00:00+08:00'
    save(ROOT/'cases'/name/'root-input.json',j)
    save(ROOT/'cases'/name/'expected.json',dict(status='CONTINUED_ORIGINAL_ORDERS',past_attempt_count=1,new_decisions=0,new_segment_fills=0))
    prefix=deepcopy(j);prefix['observed_until']=cut;prefix['tape']=[o for o in j['tape'] if timestamp(o['at'])<=timestamp(cut)]
    save(ROOT/'cases'/name/'prefix-input.json',prefix)
    prior=simulate(prefix);full=simulate(j);cp=make_checkpoint(j['ledger_input'],prior,through_at=cut)
    save(ROOT/'before'/name/'prefix-execution.json',prior);save(ROOT/'before'/name/'checkpoint.json',cp);save(ROOT/'before'/name/'full-execution.json',full)
    original=requests['partial-fill'];path=deepcopy(original['path'])
    path.update(origin_ledger_input_id=fingerprint(j['ledger_input']),start_at=j['decision_input']['data_cutoff'],observations=deepcopy(j['tape']))
    for row in path['session_coverage']:row['observation_ids']=[fingerprint(o) for o in j['tape'] if o['at'][:10]==row['date']]
    r=dict(schema='capital-standing-order-resume-input/0.1',synthetic=True,root_job=j,checkpoint=cp,expected_checkpoint_id=cp['checkpoint_id'],
        expected_latest_decision_id=prior['latest_decision_id'],path=path,expected_path_id=fingerprint(path),
        segment_tape=[o for o in j['tape'] if timestamp(o['at'])>timestamp(cut)],observed_until=j['observed_until'],resume_at='2026-01-09T16:01:00+08:00')
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
    save(ROOT/'case-index.json',dict(positive=list(requests),negative=names[len(requests):],all=names,market_samples=0,new_market_quotes=0,new_calendar_rows=0,
        excluded_archived_intake='past-reassessment: exact old review checkpoint mismatch, original input/diagnostic retained'))
    save(ROOT/'frozen.json',dict(files=[info(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='frozen.json']))
    print('Frozen',len(requests),'positive,',len(names)-len(requests),'negative; archived intake failure retained')

if __name__=='__main__':main()
