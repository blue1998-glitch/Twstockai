"""Directed ID/content collisions and idempotent retry behaviour only."""
from copy import deepcopy
import json
from pathlib import Path
from decimal import Decimal
import unittest
from graph_core.core import fingerprint
from capital_research.execution import simulate
from capital_research.continuity import make_checkpoint,validate_checkpoint
from .fixtures import specification,materialize,observed


class ReviewIdentityTests(unittest.TestCase):
    cache={}

    def case(self,name):
        if name not in self.cache:self.cache[name]=materialize(specification(name))
        return self.cache[name]

    def check_collision(self,name):
        r=self.case(name);a=observed(r)
        self.assertEqual(a['status'],'ERROR')
        self.assertIn('REASSESSMENT_ID_CONTENT_CONFLICT',a['error'])
        self.assertEqual(r['checkpoint']['state']['accepted_fills'],[])
        self.assertEqual(r['checkpoint']['state']['origin_initial_capital'],'2180')
        self.assertEqual(r['checkpoint']['state']['general_reserved_cash'],'100')
        validate_checkpoint(r['checkpoint'])
        return r

    def test_same_job_different_content_is_a_collision_not_a_retry(self):
        self.check_collision('same-job-collision')

    def test_inherited_id_cannot_hide_a_new_orders_restriction(self):
        self.check_collision('cross-round-collision')

    def test_same_job_identical_retry_does_not_repeat_fills_or_receipts(self):
        r=self.case('same-job-identical');e=r['result']['execution']
        self.assertEqual(r['result']['status'],'OK')
        once=deepcopy(r['job']);once['reassessments']=once['reassessments'][:1]
        self.assertEqual(e,simulate(once))
        self.assertEqual([f['shares'] for f in e['fills']],['20'])
        self.assertEqual(len(e['reassessment_attempts']),1)

    def test_cross_round_exact_retry_of_old_order_is_not_reauthorized(self):
        r=self.case('cross-round-identical');self.assertEqual(r['result']['status'],'OK')
        e=r['result']['execution'];plain=deepcopy(r['job']);plain['reassessments']=[]
        self.assertEqual(e,simulate(plain))
        self.assertEqual([f['shares'] for f in e['fills']],['20'])
        self.assertEqual(e['order_states']['B-buy']['status'],'CANCELLED_AT_REVIEW')
        self.assertEqual(e['order_states']['next-B-buy']['status'],'FILLED')
        self.assertEqual(e['latest_decision_id'],r['previous']['decision']['decision_id'])

    def test_same_job_distinct_id_admits_restriction_then_cancels(self):
        r=self.case('same-job-unique-control');a=observed(r)
        self.assertEqual(a['status'],'OK');self.assertEqual(a['B_fill_shares'],'0')
        self.assertEqual(a['attempts'],2)
        self.assertEqual(a['order_states']['B-buy']['status'],'CANCELLED_EVIDENCE')

    def test_cross_round_distinct_id_admits_restriction_then_cancels(self):
        r=self.case('cross-round-unique-control');a=observed(r)
        self.assertEqual(a['status'],'OK');self.assertEqual(a['B_fill_shares'],'0')
        self.assertEqual(a['attempts'],2)
        self.assertEqual(a['order_states']['next-B-buy']['status'],'CANCELLED_EVIDENCE')

    def test_future_changed_retry_does_not_change_earlier_prefix(self):
        r=self.case('same-job-collision');j=deepcopy(r['job'])
        j['tape']=[o for o in j['tape'] if o['at']<='2026-01-08T16:00:00+08:00']
        j['observed_until']='2026-01-08T16:00:00+08:00'
        actual=simulate(j);plain=deepcopy(j);plain['reassessments']=plain['reassessments'][:1]
        self.assertEqual(actual,simulate(plain))

    def test_saved_requests_bind_payload_not_receipt_time(self):
        from capital_research.reassessment_history import request_content_id
        r=self.case('cross-round-unique-control');e=r['result']['execution']
        for a in e['reassessment_attempts']:
            self.assertEqual(a['request_content_id'],request_content_id(a['request']))
            self.assertEqual(a['request']['id'],a['id'])
            self.assertEqual(a['request']['decision_id'],a['decision']['decision_id'])
        first=e['reassessment_attempts'][0]
        self.assertEqual(first['request'],self.case('cross-round-identical')['job']['reassessments'][0])
        origin=r['job']['ledger_input'];cp=make_checkpoint(origin,e,through_at=e['observed_until'])
        validate_checkpoint(cp)
        self.assertEqual(cp['state']['origin_initial_capital'],'2180')
        self.assertEqual(cp['state']['general_reserved_cash'],'100')
        self.assertEqual(cp['state']['row']['cash_receivable'],'0')
        self.assertEqual(cp['state']['row']['shares']['A'],'110')
        self.assertEqual(cp['state']['accepted_fills'],[])
        for a in e['reassessment_attempts']:
            self.assertTrue(set(a['decision']['reviewed_evidence_tokens'])<=set(cp['state']['reviewed_evidence_tokens']))

    def test_json_key_order_is_not_a_content_change(self):
        from capital_research.reassessment_history import request_content_id
        req=self.case('same-job-identical')['job']['reassessments'][0]
        def reverse(x):
            if isinstance(x,dict):return {k:reverse(v) for k,v in reversed(list(x.items()))}
            if isinstance(x,list):return [reverse(v) for v in x]
            return x
        self.assertEqual(request_content_id(req),request_content_id(reverse(req)))

    def test_all_identity_and_account_payload_changes_are_bound(self):
        from capital_research.reassessment_history import request_content_id
        original=self.case('same-job-identical')['job']['reassessments'][0]
        changes=[('plan_id','other'),('order_id','other'),('decision_id','wrong'),
                 ('checkpoint_id','wrong'),('cancelled_order_ids',[])]
        for key,value in changes:
            req=deepcopy(original);req[key]=value
            self.assertNotEqual(request_content_id(req),request_content_id(original),key)
        for key in ('account','fact','metadata'):
            req=deepcopy(original);d=req['decision_input']
            if key=='account':d['account']['settled_cash']='9999'
            elif key=='fact':d['assets']['B']['evidence'][0]['validity']['valid_until']=None
            else:d['source_integrity_metadata']['changed']='EXPLICIT_INTEGRITY_VARIANT'
            self.assertNotEqual(request_content_id(req),request_content_id(original),key)

    def test_rehashed_execution_cannot_change_stored_request(self):
        from capital_research.reassessment_history import request_content_id
        r=self.case('same-job-unique-control');e=deepcopy(r['result']['execution'])
        a=e['reassessment_attempts'][-1]
        old_attempt_id=a['attempt_id']
        a['request']['decision_input']['assets']['B']['evidence'][0]['validity']['valid_until']=None
        a['request_content_id']=request_content_id(a['request'])
        a['attempt_id']=fingerprint({k:v for k,v in a.items() if k!='attempt_id'})
        for event in e['execution_events']:
            if event.get('reassessment_attempt_id')==old_attempt_id:
                event['reassessment_attempt_id']=a['attempt_id']
        e['result_id']=fingerprint({k:v for k,v in e.items() if k!='result_id'})
        with self.assertRaisesRegex(ValueError,'Reassessment request/source binding conflict'):
            make_checkpoint(r['job']['ledger_input'],e,through_at=e['observed_until'])

    def test_historical_07_READ_is_preserved_not_implicitly_upgraded(self):
        p=Path(__file__).parent/'before/same-job-identical/actual.json'
        raw=p.read_bytes();old=json.loads(raw)['execution']
        self.assertEqual(old['schema'],'capital-execution/0.7')
        with self.assertRaisesRegex(ValueError,'LIFECYCLE_PROOF_REQUIRED'):
            make_checkpoint(specification('same-job-identical')['first_input']['ledger_input'],old,through_at=old['observed_until'])
        self.assertEqual(raw,p.read_bytes())

    def test_cross_round_retry_preserves_single_fill_cash_rights_and_reserve(self):
        r=self.case('cross-round-identical');e=r['result']['execution']
        self.assertEqual(r['checkpoint']['state']['accepted_fills'],[])
        self.assertEqual(r['checkpoint']['state']['row']['cash_receivable'],'80')
        self.assertEqual(r['checkpoint']['state']['general_reserved_cash'],'100')
        daily={d['date']:d for d in e['ledger']['daily']}
        self.assertEqual(Decimal(daily['2026-01-09']['purchase_payable']),Decimal('401.4'))
        self.assertEqual(Decimal(daily['2026-01-09']['settled_cash']),Decimal('1000'))
        last=daily['2026-01-12']
        self.assertEqual(Decimal(last['settled_cash']),Decimal('678.6'))
        self.assertEqual(Decimal(last['purchase_payable']),Decimal(0))
        self.assertEqual(last['shares'],dict(A='110',B='20',C='0'))
        cp=make_checkpoint(r['job']['ledger_input'],e,through_at=e['observed_until'])
        validate_checkpoint(cp)
        self.assertEqual(cp['origin_ledger_input'],r['checkpoint']['origin_ledger_input'])
        self.assertEqual(cp['state']['origin_initial_capital'],'2180')
        self.assertEqual(cp['state']['general_reserved_cash'],'100')
        self.assertEqual(cp['state']['accepted_fills'],e['fills'])
        self.assertEqual(len(e['fills']),1)
        for row in e['ledger']['daily']:
            rights={code:sum(Decimal(x['shares']) for x in row['share_receivables'] if x['code']==code) for code in row['shares']}
            nav=Decimal(row['settled_cash'])+Decimal(row['cash_receivable'])-Decimal(row['purchase_payable'])
            nav+=sum((Decimal(n)+rights[code])*Decimal(row['marks'][code]['value']) for code,n in row['shares'].items())
            self.assertEqual(nav,Decimal(row['net_accrual_equity']))


if __name__=='__main__':unittest.main()
