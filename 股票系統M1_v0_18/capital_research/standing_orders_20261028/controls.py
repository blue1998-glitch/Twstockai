"""Freeze each control input/expectation before its create-only actual."""
import importlib.util
from copy import deepcopy
from .freeze import ROOT, PROJECT, load, save, info
from capital_research.core import fingerprint, resume_decision, decide, timestamp
from capital_research.continuity import make_checkpoint
from capital_research.execution_continuation import resume_orders, _capture_original


def baseline_simulate(j):
    spec=importlib.util.spec_from_file_location('capital_research._standing_baseline',ROOT/'baseline/execution.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.simulate(j)


def run(name,r,expected):
    save(ROOT/'controls'/name/'input.json',r)
    save(ROOT/'controls'/name/'expected.json',expected)
    a=resume_orders(r);save(ROOT/'controls'/name/'actual.json',a);return a


def until(r,at):
    x=deepcopy(r);x['observed_until']=at
    x['segment_tape']=[o for o in x['path']['observations'] if timestamp(x['checkpoint']['state']['through_at'])<timestamp(o['at'])<=timestamp(at)]
    return x


def next_segment(r,cp,end):
    x=deepcopy(r);x.update(checkpoint=cp,expected_checkpoint_id=cp['checkpoint_id'],
        expected_latest_decision_id=cp['execution_result']['latest_decision_id'],resume_at=cp['state']['through_at'].replace('16:00:00','16:01:00'))
    return until(x,end)


def main():
    save(ROOT/'controls/specification.json',dict(synthetic=True,market_samples=0,
        sequential='Jan6 checkpoint -> Jan8 (no new tape, settle141.14) -> Jan12, original full execution equal',
        expired='expiry event once through two resumes, no remaining reserve',
        future='change only post-Jan8 B price/capacity/state and its integrity hashes; Jan8 known numeric state equal',
        no_tape='revocation only at Jan9 noon, no opportunity after known time; Jan8 reserve retained, Jan9 released; old B7 remains',
        accepted_receipt='one accepted past review, same latest and original receipt/token retained; no future new reviews',
        inherited_legacy='exact saved partial live result and settled second-round result, new-decision live guard still rejects'))
    save(ROOT/'controls/source-versions.json',dict(files=[info(PROJECT/'capital_research/execution.py'),info(PROJECT/'capital_research/execution_continuation.py')]))
    for case in ('partial-fill','expired'):
        r=load(ROOT/'cases'/case/'input.json');first=until(r,'2026-01-08T16:00:00+08:00')
        a=run(case+'-to-Jan8',first,dict(status='CONTINUED_ORIGINAL_ORDERS',cash='858.860',payable='0',new_fills=0))
        if a['checkpoint'] is None:raise ValueError(a)
        run(case+'-to-Jan12',next_segment(r,a['checkpoint'],r['observed_until']),dict(status='CONTINUED_ORIGINAL_ORDERS',execution_equal_original_full=True))
    r=load(ROOT/'controls/partial-fill-to-Jan8/input.json');x=deepcopy(r)
    for o in x['path']['observations']:
        if timestamp(o['at'])>timestamp(x['observed_until']) and o['code']=='B':
            o.update(price='999',capacity_shares='0',market_state='LIMIT_UP_NO_BUY')
    x['root_job']['tape']=deepcopy(x['path']['observations'])
    for row in x['path']['session_coverage']:row['observation_ids']=[fingerprint(o) for o in x['path']['observations'] if o['at'][:10]==row['date']]
    x['expected_path_id']=fingerprint(x['path'])
    run('future-changed',x,dict(status='CONTINUED_ORIGINAL_ORDERS',same_known_numeric_state_as='partial-fill-to-Jan8',different_integrity=True))
    r=load(ROOT/'cases/revoked/input.json');r['path']['observations']=r['path']['observations'][:-1]
    r['root_job']['tape']=deepcopy(r['path']['observations'])
    for row in r['path']['session_coverage']:row['observation_ids']=[fingerprint(o) for o in r['path']['observations'] if o['at'][:10]==row['date']]
    r['expected_path_id']=fingerprint(r['path'])
    run('no-tape-before-known',until(r,'2026-01-08T16:00:00+08:00'),dict(status='CONTINUED_ORIGINAL_ORDERS',remaining='13',reserved='261.65039',cancelled=False))
    a=run('no-tape-after-known',until(r,'2026-01-09T16:00:00+08:00'),dict(status='CONTINUED_ORIGINAL_ORDERS',remaining='13',reserved='0',cancelled=True,filled_B='7'))
    if a['checkpoint'] is None:raise ValueError(a)
    run('no-tape-to-Jan12',next_segment(r,a['checkpoint'],r['observed_until']),dict(status='CONTINUED_ORIGINAL_ORDERS',remaining='13',reserved='0',filled_B='7',cash='938.860'))
    # A legitimate earlier review, bound with the same current provisional proof.
    r=load(ROOT/'cases/past-reassessment-current/input.json');j=r['root_job'];review=j['reassessments'][0]
    review['decision_input']['assets']['B']['evidence']=deepcopy(j['decision_input']['assets']['B']['evidence'])
    cp=load(ROOT/'diagnostics/current-provisional-checkpoint.json')
    review['decision_id']=resume_decision(decide(j['decision_input']),review['decision_input'],checkpoint=cp,cancelled_order_ids=review['cancelled_order_ids'])['decision']['decision_id']
    cut=r['checkpoint']['state']['through_at'];prefix=deepcopy(j);prefix['observed_until']=cut;prefix['tape']=[o for o in j['tape'] if timestamp(o['at'])<=timestamp(cut)]
    save(ROOT/'controls/accepted-history/root-input.json',j);save(ROOT/'controls/accepted-history/prefix-input.json',prefix)
    save(ROOT/'controls/accepted-history/expected.json',dict(past_outcome='ACCEPTED',attempts=1,new_decisions=0,all_tokens_retained=True))
    prior=baseline_simulate(prefix);full=baseline_simulate(j)
    save(ROOT/'controls/accepted-history/baseline-prefix.json',prior);save(ROOT/'controls/accepted-history/baseline-full.json',full)
    cp=make_checkpoint(j['ledger_input'],prior,through_at=cut)
    r.update(checkpoint=cp,expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=prior['latest_decision_id'])
    run('accepted-history-resume',r,dict(status='CONTINUED_ORIGINAL_ORDERS',past_outcome='ACCEPTED',execution_equal_original_full=True))
    # Old guard remains: this new API is not permission for a new decision.
    from capital_research.cash_action import evaluate
    old=load(PROJECT/'capital_research/cash_action_20261028/cases/opening-cash-first-B/input.json')
    original=load(ROOT/'cases/partial-fill/input.json');cp=original['checkpoint']
    old['account_source']=dict(kind='CHECKPOINT',checkpoint=cp,expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=cp['execution_result']['latest_decision_id'])
    old['decision_template'].update(data_cutoff=cp['state']['through_at'],decision_at=original['resume_at'])
    save(ROOT/'controls/new-decision/input.json',old);save(ROOT/'controls/new-decision/expected.json',dict(must_not_be_qualified=True))
    save(ROOT/'controls/new-decision/actual.json',evaluate(old))
    print('Created sequential, future, watermark and accepted-history controls; no old suite')


if __name__=='__main__':main()
