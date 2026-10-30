"""Directed repairs of Work hypotheses. No market window producer or old suite."""
from copy import deepcopy
from decimal import Decimal
import unittest
from graph_core.core import fingerprint
from rotation_research.action_fixtures import event
from .core import decide,resume_decision
from .execution import simulate,compare_jobs
from .continuity import make_checkpoint,validate_checkpoint,account_at_checkpoint
from .fixtures import fixture,job,observation
from .review_20261025.reproduce import risk_job
from .review_20261025.fixtures import first_segment,next_input,reauthorized_job,continued_job


class ReviewTests(unittest.TestCase):
    def test_failed_exit_cannot_fund_a_joint_risk_breach(self):
        r=simulate(risk_job());self.assertEqual(r['fills'],[])
        self.assertEqual(r['ledger']['daily'][-1]['shares'],dict(A='100',B='0',C='0'))
        self.assertTrue(any(Decimal(x['joint_possible_fill_violations']['group:shared'])>0 for x in r['risk_observations']))

    def test_successful_exit_releases_risk_after_actual_fill(self):
        j=risk_job();j['tape'][0]['market_state']='OPEN';r=simulate(j)
        self.assertEqual([(f['code'],f['shares']) for f in r['fills']],[('A','100'),('B','40')])

    def test_partial_exit_is_not_a_complete_risk_release(self):
        j=risk_job();j['tape'][0].update(market_state='OPEN',capacity_shares='20')
        r=simulate(j)
        self.assertEqual(r['ledger']['daily'][-1]['shares'],dict(A='80',B='0',C='0'))

    def test_share_rights_count_even_before_they_become_sellable(self):
        j=risk_job();j['tape'][0]['market_state']='OPEN'
        j['decision_input']['account']['share_claims']=[dict(id='existing-A',code='A',shares='40',delivery_date='2026-01-08',tradable_date='2026-01-12',source_ids=['fixture'])]
        j['ledger_input']['opening']['share_claims']=deepcopy(j['decision_input']['account']['share_claims'])
        # Opening exceeds 1100; selling A reduces it, but rights40 + B40 still exceed.
        r=simulate(j)
        self.assertEqual([f['code'] for f in r['fills']],['A'])

    def test_observed_market_breach_does_not_invent_an_exit(self):
        j=job('A-zero');j['decision_input']['risk_limits']['group_value']['original']='1100'
        j['tape'][0].update(price='20',market_state='LIMIT_DOWN_NO_SELL')
        r=simulate(j);self.assertEqual(r['fills'],[])
        self.assertTrue(any(Decimal(x['actual_violations']['group:original'])>0 for x in r['risk_observations']))

    def test_stale_held_mark_blocks_risk_increase_without_inventing_price(self):
        j=job('C-event');j['tape']=[o for o in j['tape'] if o['code']!='A']
        r=simulate(j);self.assertEqual(r['fills'],[])
        self.assertTrue(any('A' in x['stale_exposure_marks'] for x in r['risk_observations']))

    def test_waiting_for_settlement_never_self_reauthorizes(self):
        r=simulate(job());self.assertEqual([f['code'] for f in r['fills']],['A'])
        self.assertTrue(any(e['status']=='WAITING_REASSESSMENT' for e in r['execution_events']))

    def test_invalidated_breakout_cancels_even_below_buy_limit(self):
        j=job();j['tape'][2]['evidence_status']='INVALIDATED'
        r=simulate(j);self.assertEqual([f['code'] for f in r['fills']],['A'])
        self.assertEqual(r['order_states']['B-buy']['status'],'CANCELLED_EVIDENCE')

    def test_pre_funded_persistent_order_can_continue_without_funding_reassessment(self):
        j=risk_job();j['decision_input']['risk_limits']['group_value']['shared']='3000'
        r=simulate(j)
        self.assertEqual([f['code'] for f in r['fills']],['B'])
        self.assertEqual(r['fills'][0]['decision_date'],'2026-01-05')

    def test_new_decision_binds_account_evidence_cutoff_and_fill_decision(self):
        j,cp,new=reauthorized_job();r=simulate(j)
        b=next(f for f in r['fills'] if f['code']=='B')
        self.assertEqual((b['shares'],b['decision_date']),('99','2026-01-08'))
        self.assertEqual(r['reassessments'][0]['decision_id'],new['decision']['decision_id'])
        self.assertEqual(r['reassessments'][0]['checkpoint_id'],cp['checkpoint_id'])

    def test_reassessment_cannot_override_observed_invalidation(self):
        j,_,_=reauthorized_job();j['tape'][2]['evidence_status']='INVALIDATED'
        self.assertEqual([f['code'] for f in simulate(j)['fills']],['A'])

    def test_wrong_checkpoint_or_decision_id_refuses_reassessment(self):
        for key in ('decision_id','checkpoint_id'):
            j,_,_=reauthorized_job();j['reassessments'][0][key]='sha256:wrong'
            with self.assertRaises(ValueError):simulate(j)

    def test_modified_cash_or_dropped_rights_cannot_resume(self):
        first,r,cp=first_segment();fresh,ids=next_input(first['decision_input'],cp)
        fresh['account']['settled_cash']='9000'
        with self.assertRaises(ValueError):resume_decision(decide(first['decision_input']),fresh,checkpoint=cp,cancelled_order_ids=ids)

    def test_no_checkpoint_means_no_continuity_claim(self):
        a=decide(fixture());b=fixture();b['decision_at']='2026-01-05T16:00:00+08:00'
        with self.assertRaisesRegex(ValueError,'CHECKPOINT_REQUIRED'):resume_decision(a,b)

    def test_unfilled_order_cannot_disappear_at_a_review(self):
        first,r,cp=first_segment();fresh,ids=next_input(first['decision_input'],cp)
        self.assertEqual(ids,['B-buy'])
        with self.assertRaisesRegex(ValueError,'ORDER_CONTINUATION_NOT_IMPLEMENTED'):
            resume_decision(decide(first['decision_input']),fresh,checkpoint=cp)

    def test_checkpoint_modification_is_not_repaired_or_silently_accepted(self):
        first,r,cp=first_segment();cp['state']['row']['settled_cash']='9000'
        with self.assertRaises(ValueError):validate_checkpoint(cp)

    def test_continued_fills_keep_original_capital_and_only_one_cash_ledger(self):
        first,r,j=continued_job();out=simulate(j)
        self.assertEqual(out['ledger']['initial_equity'],'2000')
        self.assertEqual(Decimal(out['ledger']['daily'][-1]['net_accrual_equity']),Decimal('1991.020'))
        self.assertEqual(len(out['fills']),2);self.assertEqual(len(out['new_fill_ids']),1)
        self.assertEqual(out['fills'][0],r['fills'][0])

    def test_checkpoint_rights_flow_through_without_double_counting(self):
        data=fixture();j=job(data=data);event(j['ledger_input'])
        j['observed_until']='2026-01-08T16:00:00+08:00';j['tape']=[x for x in j['tape'] if x['at'][:10]<='2026-01-08']
        r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        fresh,ids=next_input(data,cp)
        self.assertEqual(Decimal(fresh['account']['cash_claims'][0]['amount']),Decimal('80'))
        old=decide(data);good=resume_decision(old,fresh,checkpoint=cp,cancelled_order_ids=ids)
        self.assertEqual(Decimal(good['decision']['initial_capital']),Decimal('2075'))
        fresh['account']['cash_claims']=[]
        with self.assertRaises(ValueError):resume_decision(old,fresh,checkpoint=cp,cancelled_order_ids=ids)

    def test_joint_market_comparison_rejects_different_state_price_capacity_or_availability(self):
        for key,v in [('market_state','LIMIT_UP_NO_BUY'),('price','21'),('capacity_shares','1'),('available_at','2026-01-09T09:01:00+08:00')]:
            a=job();b=deepcopy(a);b['tape'][2][key]=v
            with self.assertRaisesRegex(ValueError,'exogenous'):compare_jobs(dict(a=a,b=b))

    def test_same_market_allows_different_orders(self):
        a=job('A-zero');b=job('D-cash')
        r=compare_jobs(dict(hold=a,cash=b));self.assertIsNone(r['ranking'])
        self.assertFalse(r['total_net_return_comparison_qualified'])

    def test_static_pareto_is_not_a_policy_elimination_rule(self):
        r=decide(fixture())['decision']
        self.assertEqual(r['layer3']['comparison'],'STATIC_TARGET_SCENARIO_PARETO_NOT_POLICY_COMPARISON')
        ps=r['layer3']['alternatives']
        self.assertEqual(set(r['research_recommendation']['candidate_ids']),{p['id'] for p in ps if p['feasible']})
        for p in ps:
            if p['feasible']:self.assertEqual(p['policy_dominance'],'NOT_EVALUATED')

    def test_two_candidates_share_the_risk_envelope_after_failed_exit(self):
        j=risk_job();d=j['decision_input'];d['risk_limits']['group_value']['shared']='1200'
        d['plans'][-1]['targets']=dict(A='0',B='5',C='5')
        j=job('E-transition',d)
        j['tape']=[observation('A','2026-01-06T09:00:00+08:00',state='LIMIT_DOWN_NO_SELL',settlement='2026-01-08'),
                   observation('B','2026-01-06T09:01:00+08:00',settlement='2026-01-08'),
                   observation('C','2026-01-06T09:02:00+08:00',settlement='2026-01-08')]
        j['observed_until']='2026-01-08T16:00:00+08:00';r=simulate(j)
        last=r['ledger']['daily'][-1]
        exposure=sum(Decimal(n)*Decimal(last['marks'][c]['value']) for c,n in last['shares'].items())
        self.assertLessEqual(exposure,Decimal('1200'))
        self.assertTrue(any(Decimal(x['joint_group_values']['shared'])>Decimal('1200') for x in r['risk_observations']))

    def test_unfilled_hedge_is_not_credited_as_account_risk_protection(self):
        j=risk_job();d=j['decision_input'];d['risk_limits']['group_value']['shared']='3000'
        d['risk_limits']['account_stress_loss']='100'
        d['scenario_set']['scenarios']=[dict(id='B_down_C_hedge',prices=dict(A='10',B='10',C='50'))]
        d['plans'][-1]['targets']=dict(A='0',B='10',C='10');j=job('E-transition',d)
        j['tape']=[observation('A','2026-01-06T09:00:00+08:00',state='LIMIT_DOWN_NO_SELL',settlement='2026-01-08'),
                   observation('C','2026-01-06T09:01:00+08:00',state='LIMIT_UP_NO_BUY',settlement='2026-01-08'),
                   observation('B','2026-01-06T09:02:00+08:00',settlement='2026-01-08')]
        j['observed_until']='2026-01-08T16:00:00+08:00';r=simulate(j)
        self.assertEqual(r['fills'],[])
        self.assertTrue(any(Decimal(x['joint_possible_fill_violations']['account_stress'])>0 for x in r['risk_observations']))

    def test_infeasible_fresh_entry_does_not_reauthorize_even_with_a_valid_id(self):
        j,cp,new=reauthorized_job();review=j['reassessments'][0]
        review['decision_input']['assets']['B']['entry_context']['formal_reference']=None
        fresh=resume_decision(decide(j['decision_input']),review['decision_input'],checkpoint=cp,cancelled_order_ids=review['cancelled_order_ids'])
        review['decision_id']=fresh['decision']['decision_id'];r=simulate(j)
        self.assertEqual([f['code'] for f in r['fills']],['A'])

    def test_unsettled_payable_continuation_refuses_instead_of_rebasing(self):
        j=job('C-event');j['tape']=[o for o in j['tape'] if o['at'][:10]=='2026-01-06'];j['observed_until']='2026-01-06T16:00:00+08:00'
        r=simulate(j);cp=make_checkpoint(j['ledger_input'],r,through_at=j['observed_until'])
        self.assertGreater(Decimal(cp['state']['row']['purchase_payable']),0)
        with self.assertRaisesRegex(ValueError,'PAYABLE_CONTINUATION_NOT_IMPLEMENTED'):
            account_at_checkpoint(cp,decision_at='2026-01-06T17:00:00+08:00')

    def test_future_ledger_prices_change_integrity_but_not_a_prefix_decision(self):
        a,ra,cpa=first_segment();b=deepcopy(a)
        b['ledger_input']['assets']['B']['quotes']['2026-01-12']='999'
        rb=simulate(b);cpb=make_checkpoint(b['ledger_input'],rb,through_at=b['observed_until'])
        self.assertEqual(cpa['state_id'],cpb['state_id']);self.assertNotEqual(cpa['integrity'],cpb['integrity'])
        da,ids=next_input(a['decision_input'],cpa);db,idsb=next_input(b['decision_input'],cpb)
        x=resume_decision(decide(a['decision_input']),da,checkpoint=cpa,cancelled_order_ids=ids)
        y=resume_decision(decide(b['decision_input']),db,checkpoint=cpb,cancelled_order_ids=idsb)
        self.assertEqual(x['decision'],y['decision'])
        self.assertNotEqual(x['source_integrity_metadata'],y['source_integrity_metadata'])


if __name__=='__main__':unittest.main()
