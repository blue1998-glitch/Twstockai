"""Directed properties of this repair, not a strategy-performance suite."""
from copy import deepcopy
from decimal import Decimal,localcontext
import unittest
from unittest.mock import patch
from graph_core.core import fingerprint
from capital_research.core import decide,resume_decision
from capital_research.execution import simulate,compare_jobs
from capital_research.continuity import make_checkpoint,validate_checkpoint,account_at_checkpoint
from capital_research.trend_fixtures import path_fixture
from capital_research.trend_replay import run_fixture
from .fixtures import data_fixture,execution_job,prefix,advance,reassessed_job,continuation_job,partial_first,review


def candidate(result,key):
    return next(p for p in result['decision']['layer3']['alternatives'] if p['id']==key)


class RepairTests(unittest.TestCase):
    def test_not_qualified_excludes_candidate_and_prevents_fill(self):
        d=data_fixture();d['assets']['B']['capital_eligibility']['status']='NOT_QUALIFIED'
        r=decide(d);self.assertIn('NEW_CAPITAL_NOT_QUALIFIED:B',candidate(r,'C-event')['reasons'])
        self.assertNotIn('C-event',r['decision']['research_recommendation']['candidate_ids'])
        self.assertEqual(simulate(execution_job('C-event',d))['fills'],[])

    def test_missing_review_cannot_use_legacy_input_to_bypass_gate(self):
        d=data_fixture();d['assets']['B'].pop('capital_eligibility')
        self.assertFalse(candidate(decide(d),'C-event')['feasible'])

    def test_every_new_asset_needs_its_own_qualification(self):
        d=data_fixture();d['assets']['C']['capital_eligibility']['status']='NOT_QUALIFIED'
        r=decide(d);self.assertIn('NEW_CAPITAL_NOT_QUALIFIED:C',candidate(r,'E-joint')['reasons'])
        self.assertTrue(candidate(r,'C-event')['feasible'])

    def test_old_valid_facts_survive_a_current_review_without_becoming_new_events(self):
        j=prefix(execution_job());r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        fresh,ids=advance(j['decision_input'],cp)
        self.assertEqual(fresh['assets']['B']['evidence'],j['decision_input']['assets']['B']['evidence'])
        old=decide(j['decision_input']);new=resume_decision(old,fresh,checkpoint=cp,cancelled_order_ids=ids)
        self.assertTrue(candidate(new,'B-full')['feasible']);self.assertEqual(new['decision']['new_evidence_tokens'],[])
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER',candidate(new,'C-event')['reasons'])
        second=continuation_job(j,r,old,plan='B-full',fresh=fresh,ids=ids);out=simulate(second)
        self.assertEqual([(f['code'],f['shares'],f['decision_date']) for f in out['fills'] if f['id'] in out['new_fill_ids']], [('B','99','2026-01-08')])

    def test_future_review_is_not_a_today_qualification_or_identity_input(self):
        d=data_fixture();d['assets']['B']['capital_eligibility']['available_at']='2026-01-08T17:00:00+08:00'
        a=decide(d);d['assets']['B']['capital_eligibility']['status']='UNKNOWN';b=decide(d)
        self.assertEqual(a['decision'],b['decision']);self.assertFalse(candidate(a,'C-event')['feasible'])

    def test_review_cutoff_source_and_price_basis_are_bound(self):
        d=data_fixture();d['assets']['B']['capital_eligibility']['data_cutoff']='2026-01-02T14:00:00+08:00'
        self.assertFalse(candidate(decide(d),'C-event')['feasible'])
        for key in ('source_id','basis_id','adjustment_version'):
            d=data_fixture();d['assets']['B']['capital_eligibility'][key]='wrong'
            with self.assertRaisesRegex(ValueError,'source/basis'):decide(d)

    def test_unreleased_sellable_limit_refuses_instead_of_promoting_shares(self):
        d=data_fixture();d['account']['holdings']['A']['sellable']='0';j=prefix(execution_job('A-zero',d));r=simulate(j)
        cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        self.assertEqual(cp['state']['opening_unavailable_shares']['A'],'100')
        with self.assertRaisesRegex(ValueError,'SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED'):advance(d,cp)

    def test_fully_sellable_account_can_continue_and_reduce_risk(self):
        j=prefix(execution_job('A-zero'));r=simulate(j)
        out=simulate(continuation_job(j,r,decide(j['decision_input'])))
        self.assertEqual(out['ledger']['initial_equity'],'2000')
        self.assertEqual(out['ledger']['daily'][-1]['shares'],dict(A='0',B='0',C='0'))

    def test_intraday_watermark_refuses_before_ledger_execution(self):
        j=prefix(execution_job(),through='2026-01-08T09:00:00+08:00')
        with patch('capital_research.execution.replay',side_effect=AssertionError('must refuse before replay')):
            with self.assertRaisesRegex(ValueError,'DAILY_CLOSE_WATERMARK_REQUIRED'):simulate(j)

    def test_missing_daily_close_proof_is_not_filled_in(self):
        j=execution_job('A-zero');j.pop('ledger_close_proof')
        with self.assertRaisesRegex(ValueError,'EXPLICIT_LEDGER_CLOSE_PROOF_REQUIRED'):simulate(j)

    def test_delayed_daily_close_must_be_available_before_next_decision(self):
        j=prefix(execution_job());j['ledger_close_proof']['closes']['2026-01-08']['available_at']='2026-01-08T17:30:00+08:00'
        r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        with self.assertRaisesRegex(ValueError,'NOT_YET_AVAILABLE'):advance(j['decision_input'],cp,at='2026-01-08T17:00:00+08:00')
        fresh,ids=advance(j['decision_input'],cp,at='2026-01-08T17:31:00+08:00')
        self.assertEqual(fresh['account']['settled_cash'],'1995.000')
        self.assertTrue(candidate(resume_decision(decide(j['decision_input']),fresh,checkpoint=cp,cancelled_order_ids=ids),'B-full')['feasible'])

    def test_close_proof_source_and_availability_cannot_be_mismatched(self):
        for key,value in [('source_ids',['unknown']),('available_at','2026-01-08T15:00:00+08:00')]:
            j=prefix(execution_job());j['ledger_close_proof']['closes']['2026-01-08'][key]=value
            with self.assertRaises(ValueError):simulate(j)

    def test_common_market_identity_includes_close_availability(self):
        a=execution_job('A-zero');b=deepcopy(a)
        b['ledger_close_proof']['closes']['2026-01-08']['available_at']='2026-01-08T17:00:00+08:00'
        with self.assertRaisesRegex(ValueError,'exogenous'):compare_jobs(dict(a=a,b=b))

    def test_latest_reassessment_resumes_and_old_predecessor_refuses(self):
        j,old,new=reassessed_job();r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        fresh,ids=advance(j['reassessments'][0]['decision_input'],cp)
        good=resume_decision(new,fresh,checkpoint=cp,cancelled_order_ids=ids)
        self.assertEqual(good['decision']['continuity']['latest_predecessor_id'],new['decision']['decision_id'])
        with self.assertRaisesRegex(ValueError,'LATEST_PREDECESSOR_REQUIRED'):resume_decision(old,fresh,checkpoint=cp,cancelled_order_ids=ids)

    def test_reassessment_then_another_execution_keeps_all_fills_and_tokens(self):
        j,old,new=reassessed_job(extend=True);r=simulate(j)
        second=continuation_job(j,r,new);out=simulate(second)
        self.assertEqual(out['fills'][:len(r['fills'])],r['fills'])
        self.assertEqual(out['ledger']['initial_equity'],'2000')
        self.assertEqual(len(out['fills']),3)
        self.assertIn(new['decision']['decision_id'],out['decision_records'])
        token='fixture:event_id:B-reviewed-repair'
        self.assertIn(token,out['reviewed_evidence_tokens'])
        latest=out['decision_records'][out['latest_decision_id']]
        self.assertNotIn(token,latest['new_evidence_tokens'])

    def test_wrong_account_cutoff_or_missing_cancellation_does_not_resume(self):
        j=prefix(execution_job());r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        fresh,ids=advance(j['decision_input'],cp);old=decide(j['decision_input'])
        for key in ('cash','cutoff','cancellation'):
            d=deepcopy(fresh);cancel=ids
            if key=='cash':d['account']['settled_cash']='9000'
            elif key=='cutoff':d['data_cutoff']='2026-01-09T16:00:00+08:00'
            else:cancel=[]
            with self.assertRaises(ValueError):resume_decision(old,d,checkpoint=cp,cancelled_order_ids=cancel)

    def test_no_reassessment_record_does_not_self_reauthorize(self):
        r=simulate(execution_job())
        self.assertEqual([f['code'] for f in r['fills']],['A'])
        self.assertTrue(any(e['status']=='WAITING_REASSESSMENT' for e in r['execution_events']))

    def test_bad_reassessment_identity_and_observed_invalidation_refuse(self):
        j,_,_=reassessed_job();j['reassessments'][0]['decision_id']='wrong'
        with self.assertRaisesRegex(ValueError,'decision_id mismatch'):simulate(j)
        j,_,_=reassessed_job();j['tape'][2]['evidence_status']='INVALIDATED'
        r=simulate(j);self.assertEqual([f['code'] for f in r['fills']],['A'])

    def test_expired_fact_cannot_be_revived_by_a_current_review(self):
        j=execution_job();j['decision_input']['assets']['B']['evidence'][0]['validity']['valid_until']='2026-01-07T16:00:00+08:00'
        first=prefix(j);r=simulate(first);cp=make_checkpoint(j['ledger_input'],r,through_at=first['observed_until'])
        fresh,ids=advance(j['decision_input'],cp);new=resume_decision(decide(j['decision_input']),fresh,checkpoint=cp,cancelled_order_ids=ids)
        self.assertFalse(candidate(new,'B-full')['feasible'])
        self.assertTrue(any('EXPIRED' in x for x in new['decision']['layer2']['B']['capital_eligibility']['reasons']))

    def test_expiry_and_invalidation_cancel_standing_orders_inside_limit(self):
        for invalid in (False,True):
            j=execution_job('C-event');v=j['decision_input']['assets']['B']['evidence'][0]['validity']
            if invalid:v['invalidation']=dict(evidence_id='revoked',occurred_at='2026-01-06T09:00:00+08:00',available_at='2026-01-06T09:00:00+08:00',source_ids=['fixture'])
            else:v['valid_until']='2026-01-06T09:00:00+08:00'
            r=simulate(j);self.assertEqual([f['code'] for f in r['fills']],['A'])
            self.assertEqual(r['order_states']['B-buy']['status'],'CANCELLED_EVIDENCE')

    def test_future_revocation_does_not_rewrite_current_decision(self):
        d=data_fixture();base=decide(d)
        d['assets']['B']['evidence'][0]['validity']['invalidation']=dict(evidence_id='future',occurred_at='2026-01-09T09:00:00+08:00',available_at='2026-01-09T09:00:00+08:00',source_ids=['fixture'])
        self.assertEqual(base['decision'],decide(d)['decision'])

    def test_old_future_ledger_integrity_is_separate_from_prefix_decision(self):
        a=prefix(execution_job());b=deepcopy(a);b['ledger_input']['assets']['B']['quotes']['2026-01-12']='999'
        results=[]
        for j in (a,b):
            r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until']);d,ids=advance(j['decision_input'],cp)
            results.append(resume_decision(decide(j['decision_input']),d,checkpoint=cp,cancelled_order_ids=ids))
        self.assertEqual(results[0]['decision'],results[1]['decision'])
        self.assertNotEqual(results[0]['source_integrity_metadata'],results[1]['source_integrity_metadata'])

    def test_partial_fills_cancel_and_continue_without_losing_claims_or_reserves(self):
        self._check_partial(False)

    def test_partial_fills_expire_and_continue_without_inventing_cancellation(self):
        self._check_partial(True)

    def _check_partial(self,expire):
        j=partial_first(expire=expire);r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        self.assertEqual(r['ledger']['initial_equity'],'2180')
        self.assertEqual(cp['state']['row']['settled_cash'],'1056.660')
        self.assertEqual(cp['state']['row']['shares'],dict(A='80',B='7',C='0'))
        self.assertEqual(cp['state']['row']['cash_claims'][0]['amount'],'80')
        self.assertEqual(cp['state']['row']['share_receivables'][0]['shares'],'10')
        self.assertEqual({k:v['remaining'] for k,v in r['order_states'].items()}, {'A-sell':'30','B-buy':'13'})
        self.assertEqual(cp['state']['general_reserved_cash'],'100')
        second=continuation_job(j,r,decide(j['decision_input']));out=simulate(second)
        self.assertEqual(second['decision_input']['account']['reserved_cash'],'100')
        self.assertEqual(out['fills'][:2],r['fills']);self.assertEqual(len(out['fills']),4)
        for key in ('A-sell','B-buy'):
            self.assertEqual(out['order_states'][key]['reserved_cash'],'0')
            self.assertEqual(out['order_states'][key]['status'],'EXPIRED_UNFILLED' if expire else 'CANCELLED_AT_REVIEW')
        last=out['ledger']['daily'][-1]
        self.assertEqual(last['settled_cash'],'2069.720');self.assertEqual(last['shares'],dict(A='10',B='0',C='0'))
        self.assertEqual(last['cash_claims'],[]);self.assertEqual(last['share_receivables'],[])
        self.assertEqual(Decimal(last['net_accrual_equity'])+Decimal('9')+Decimal('1.28'),Decimal('2180'))
        for row in out['ledger']['daily']:
            rights={c:sum(Decimal(x['shares']) for x in row['share_receivables'] if x['code']==c) for c in row['shares']}
            value=Decimal(row['settled_cash'])+Decimal(row['cash_receivable'])-Decimal(row['purchase_payable'])
            value+=sum((Decimal(n)+rights[c])*Decimal(row['marks'][c]['value']) for c,n in row['shares'].items())
            self.assertEqual(value,Decimal(row['net_accrual_equity']))
        endcp=make_checkpoint(j['ledger_input'],out,through_at=out['observed_until']);fresh,ids=advance(second['decision_input'],endcp)
        d=resume_decision(dict(decision=out['decision_records'][out['latest_decision_id']]),fresh,checkpoint=endcp,cancelled_order_ids=ids)
        self.assertEqual(Decimal(candidate(d,'A-zero')['available_settled_cash']),Decimal('1969.720'))

    def test_unsettled_purchase_payable_still_refuses_continuation(self):
        j=partial_first();j['observed_until']='2026-01-06T16:00:00+08:00';r=simulate(j)
        cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        self.assertGreater(Decimal(cp['state']['row']['purchase_payable']),0)
        with self.assertRaisesRegex(ValueError,'PAYABLE_CONTINUATION_NOT_IMPLEMENTED'):advance(j['decision_input'],cp)

    def test_rehashed_wrong_fill_order_link_is_not_a_valid_checkpoint(self):
        j=partial_first();r=simulate(j);r['fill_order_ids'][r['fills'][0]['id']]='B-buy'
        r['result_id']=fingerprint({k:v for k,v in r.items() if k!='result_id'})
        with self.assertRaisesRegex(ValueError,'another order'):make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])

    def test_checkpoint_share_reconciliation_ignores_callers_decimal_precision(self):
        d=data_fixture();d['plans'].append(dict(id='E-count',family='E',route='R1',targets=dict(A='1',B='0',C='0'),trigger_ids=[],edge_budget='1000',conditions=['EXACT_INTEGER_COUNT']))
        j=prefix(execution_job('E-count',d));j['tape'][0]['capacity_shares']='33';r=simulate(j)
        regular=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        with localcontext() as context:
            context.prec=1
            low=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        self.assertEqual(regular,low)

    def test_rights_or_reserve_cannot_disappear_from_next_account(self):
        j=partial_first();r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until']);fresh,ids=advance(j['decision_input'],cp)
        for field,value in [('reserved_cash','0'),('cash_claims',[]),('share_claims',[])]:
            d=deepcopy(fresh);d['account'][field]=value
            with self.assertRaises(ValueError):resume_decision(decide(j['decision_input']),d,checkpoint=cp,cancelled_order_ids=ids)

    def test_failed_exit_still_cannot_release_joint_risk(self):
        d=data_fixture()
        for a in d['assets'].values():a['group']='shared'
        d['risk_limits']['group_value']={'shared':'1100'}
        d['plans'].append(dict(id='E-risk',family='E',route='R1',targets=dict(A='0',B='40',C='0'),trigger_ids=[],edge_budget='1000',conditions=['REPAIR_REGRESSION']))
        j=prefix(execution_job('E-risk',d));j['tape'][0]['market_state']='LIMIT_DOWN_NO_SELL';r=simulate(j)
        self.assertEqual(r['fills'],[])
        self.assertTrue(any(Decimal(x['joint_possible_fill_violations']['group:shared'])>0 for x in r['risk_observations']))

    def test_market_price_capacity_state_availability_source_and_basis_stay_bound(self):
        for key,value in [('price','21'),('capacity_shares','1'),('market_state','LIMIT_UP_NO_BUY'),('available_at','2026-01-06T09:00:30+08:00'),('source_id','wrong'),('basis_id','wrong')]:
            a=execution_job('A-zero');b=deepcopy(a);b['tape'][1][key]=value
            with self.assertRaisesRegex(ValueError,'exogenous'):compare_jobs(dict(a=a,b=b))

    def test_research_permission_never_grants_external_qualification_or_R2(self):
        d=data_fixture();r=decide(d);out=simulate(execution_job('C-event',d))
        for obj in (r['decision'],out):
            for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):self.assertIs(obj[k],False)
        self.assertIsNone(out['ledger']['total_net_return']);self.assertEqual(candidate(r,'F-min-regret')['status'],'NOT_IMPLEMENTED')


class TrendRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.negative=path_fixture('exit_repair_reentry');cls.positive=deepcopy(cls.negative)
        for f in (cls.positive['frames'][3],cls.positive['trend_input']['records'][3]):f['new_capital_evidence_qualified']=True
        cls.without=run_fixture(cls.negative);cls.with_review=run_fixture(cls.positive)

    def test_saved_reentry_counterexample_is_now_infeasible_and_unfilled(self):
        r=self.without['policy_results']['structure_hold']['rounds'][3]
        self.assertEqual(r['point_in_time_trend']['additional_capital_qualification'],'NOT_QUALIFIED')
        self.assertFalse(r['selected_policy_proposal']['feasible'])
        self.assertEqual(r['execution']['new_fill_ids'],[])
        self.assertNotIn('structure_hold',r['decision']['decision']['research_recommendation']['candidate_ids'])

    def test_explicit_qualified_reentry_fills_under_same_market_and_risk(self):
        a=self.with_review['policy_results']['structure_hold'];r=a['rounds'][3]
        self.assertTrue(r['selected_policy_proposal']['feasible'])
        fills=[f for f in r['execution']['fills'] if f['id'] in r['new_fill_ids']]
        self.assertEqual([(f['code'],f['shares'],f['date']) for f in fills],[('A','100','2026-01-19')])
        self.assertEqual(self.without['common_market_path_id'],self.with_review['common_market_path_id'])
        self.assertEqual(a['rounds'][0]['decision'],self.without['policy_results']['structure_hold']['rounds'][0]['decision'])
        self.assertIsNone(self.with_review['ranking'])


if __name__=='__main__':unittest.main()
