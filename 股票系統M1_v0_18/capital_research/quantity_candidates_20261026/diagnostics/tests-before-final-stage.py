"""Focused milestone checks reuse saved actuals; no old-suite regeneration."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from capital_research.quantity_candidates import generate
from capital_research import allocation
from capital_research.core import decide

HERE=Path(__file__).parent


def load(name,kind='actual'):
    return json.loads((HERE/'cases'/name/(kind+'.json')).read_text())


def tiny():
    r=load('legal-grid','input')
    r['bounds']=dict(retained_A=dict(minimum='99',maximum='99'),additional_B=dict(minimum='1',maximum='1'))
    return r


class QuantityCandidateTests(unittest.TestCase):
    def test_complete_grid_without_fixed_ratio_or_sampling(self):
        r=load('legal-grid')['research'];pairs={(int(x['plan']['targets']['A']),int(x['plan']['targets']['B'])) for x in r['candidates'] if x['plan']}
        self.assertTrue({(a,b) for a in range(98,101) for b in range(3)}<=pairs)
        self.assertEqual(r['grid_points'],9);self.assertTrue(r['enumeration_complete'])
        self.assertEqual(len(pairs),len(r['candidates']))
        kinds={kind for x in r['candidates'] for kind in x['kinds']}
        self.assertTrue({'HOLD','REDUCE_A_KEEP_CASH','PARTIAL_TRANSFER','FULL_TRANSFER'}<=kinds)

    def test_candidates_have_same_capital_and_preserve_other_holdings(self):
        data=load('legal-grid','input')['decision_input'];r=load('legal-grid')['research']
        for x in r['candidates']:
            self.assertEqual(x['plan']['targets']['C'],data['account']['holdings']['C']['shares'])
            self.assertEqual(x['core_evaluation']['common_account_id'],r['common_account_id'])
            self.assertEqual(x['core_evaluation']['initial_capital'],r['initial_capital'])
        self.assertEqual(r['baseline']['reserved_cash'],'100')

    def test_existing_full_transfer_is_called_and_then_rechecked(self):
        request=tiny();original=deepcopy(request)
        with patch.object(allocation,'full_transfer',wraps=allocation.full_transfer) as existing:
            result=generate(request)['research'];self.assertEqual(existing.call_count,1)
        full=next(x for x in result['candidates'] if 'FULL_TRANSFER' in x['kinds'])
        self.assertEqual(full['plan']['targets']['A'],'0')
        self.assertEqual(full['core_schema'],'capital-decision/0.8')
        self.assertEqual(request,original)

    def test_current_partial_matches_existing_core_cost_risk_and_funding(self):
        request=load('legal-grid','input');r=load('legal-grid')['research']
        proposal=next(x for x in r['candidates'] if x['plan']['targets']['A']=='99' and x['plan']['targets']['B']=='1')
        d=deepcopy(request['decision_input']);d['plans']=[proposal['plan']]
        existing=next(x for x in decide(d)['decision']['layer3']['alternatives'] if x['id']==proposal['id'])
        self.assertEqual(existing,proposal['core_evaluation'])

    def test_reused_and_shared_volume_triggers_reject_new_batch(self):
        for name in ('consumed-trigger','shared-volume-trigger','review-old-valid','after-fill-no-new-event','after-settlement-no-new-event'):
            with self.subTest(name=name):
                r=load(name)['research'];buys=[x for x in r['candidates'] if x.get('additional_B') and int(x['additional_B'])>0]
                self.assertTrue(buys)
                self.assertTrue(all(x['classification']=='REJECTED' and 'NO_NEW_INDEPENDENT_TRIGGER' in x['reasons'] for x in buys))

    def test_foreign_trigger_is_an_explicit_extra_batch_refusal(self):
        for x in load('foreign-trigger')['research']['candidates']:
            if x.get('additional_B') and int(x['additional_B'])>0:
                self.assertEqual(x['classification'],'REJECTED')
                self.assertIn('BATCH_TRIGGER_NOT_OWNED_BY_DESTINATION',x['reasons'])

    def test_unknown_invalidated_and_history_restriction_block_capital(self):
        for name in ('unknown-capital','invalidated-fact','history-revocation-not-erased'):
            with self.subTest(name=name):
                r=load(name)['research']
                self.assertFalse(r['baseline']['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
                for x in r['candidates']:
                    if x.get('additional_B') and int(x['additional_B'])>0:self.assertEqual(x['classification'],'REJECTED')

    def test_valid_old_review_is_allowed_but_not_a_new_trigger(self):
        old=load('review-old-valid')['research'];new=load('review-independent-new')['research']
        self.assertTrue(old['baseline']['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertTrue(new['groups']['CURRENTLY_FEASIBLE'])
        self.assertTrue(any(x['classification']=='CURRENTLY_FEASIBLE' and int(x['additional_B'] or '0')>0 for x in new['candidates']))
        self.assertIn('B-event',{e['id'] for e in new['baseline']['layer1']['B']['features']['price_volume']['support']})

    def test_no_family_override_or_injected_alternative_escape(self):
        request=tiny();request['family']='E'
        with self.assertRaises(ValueError):generate(request)
        request=tiny();request['decision_input']['plans']=[dict(id='injected-B',family='B',route='R1',targets=dict(A='1',B='500',C='0'),trigger_ids=[],edge_budget='1000',conditions=[])]
        r=generate(request)['research']
        self.assertNotIn('injected-B',{x['id'] for x in r['candidates']})
        for name in json.loads((HERE/'intake.json').read_text())['case_names']:
            for x in load(name)['research']['candidates']:
                if int(x.get('additional_B') or '0')>0:self.assertEqual(x['plan']['family'],'C')

    def test_settled_cash_reserve_and_waiting_are_separate(self):
        r=load('reserve-insufficient')['research']
        x=next(x for x in r['candidates'] if x['plan'] and x['plan']['targets']['A']=='100' and x['plan']['targets']['B']=='1')
        self.assertEqual(x['core_evaluation']['available_settled_cash'],'1')
        self.assertEqual(x['classification'],'REJECTED')
        r=load('wait-settlement')['research']
        x=next(x for x in r['candidates'] if x['plan'] and x['plan']['targets']['A']=='95')
        self.assertEqual(x['classification'],'WAIT_SETTLEMENT_REASSESSMENT')
        self.assertEqual(x['core_evaluation']['funding'],'WAIT_SALE_SETTLEMENT_AND_REEVALUATE')

    def test_non_monotone_domain_keeps_middle_feasible_candidates(self):
        r=load('non-monotone')['research']
        values={x['plan']['targets']['B']:x['classification'] for x in r['candidates'] if x['plan'] and x['plan']['targets']['A']=='100'}
        self.assertEqual(values,{'0':'REJECTED','1':'CURRENTLY_FEASIBLE','2':'CURRENTLY_FEASIBLE','3':'REJECTED'})
        self.assertNotIn('A-zero',r['groups']['CURRENTLY_FEASIBLE'])

    def test_both_limits_refuse_without_partial_candidate_prefix(self):
        for name in ('grid-over-limit','full-over-limit'):
            with self.subTest(name=name):
                r=load(name)['research'];self.assertEqual(r['status'],'REFUSED_SEARCH_LIMIT')
                self.assertEqual(r['candidates'],[]);self.assertFalse(r['enumeration_complete'])

    def test_existing_order_full_builder_and_credit_remain_unsupported(self):
        r=load('existing-order-full-unsupported')['research']
        self.assertEqual(next(x for x in r['candidates'] if 'FULL_TRANSFER' in x['kinds'])['classification'],'NOT_IMPLEMENTED')
        request=tiny();request['decision_input']['execution_model']['buying_power']='BROKER_CREDIT_RESEARCH'
        self.assertEqual(generate(request)['research']['status'],'NOT_IMPLEMENTED')

    def test_continuation_keeps_authoritative_account_latest_and_tokens(self):
        for name in ('review-old-valid','review-independent-new','after-fill-no-new-event','after-settlement-no-new-event','history-revocation-not-erased'):
            request=load(name,'input');r=load(name)['research'];cp=request['continuation']['checkpoint'];base=r['baseline']
            with self.subTest(name=name):
                self.assertEqual(base['continuity']['latest_predecessor_id'],cp['state']['latest_decision_id'])
                self.assertEqual(base['continuity']['origin_initial_capital'],cp['state']['origin_initial_capital'])
                self.assertTrue(set(cp['state']['reviewed_evidence_tokens'])<=set(base['reviewed_evidence_tokens']))
                self.assertEqual(base['reserved_cash'],cp['state']['general_reserved_cash'])
        self.assertTrue(load('after-fill-no-new-event','input')['continuation']['checkpoint']['state']['accepted_fills'])
        self.assertEqual(load('after-settlement-no-new-event','input')['decision_input']['account']['settled_cash'],'1080')

    def test_future_prefix_isolation_allows_integrity_metadata_to_differ(self):
        original=load('legal-grid')
        for name in ('future-A-wins','future-B-wins','future-both-fall'):
            self.assertEqual(original['research'],load(name)['research'])
            self.assertNotEqual(original['source_integrity_metadata'],load(name)['source_integrity_metadata'])

    def test_no_winner_orders_or_formal_qualification(self):
        for name in json.loads((HERE/'intake.json').read_text())['case_names']:
            r=load(name)['research'];self.assertIsNone(r['selected_id']);self.assertIsNone(r['ranking'])
            self.assertEqual(r['order_generation'],'NOT_PERFORMED');self.assertEqual(r['execution'],'NOT_PERFORMED')
            for key in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):self.assertIs(r[key],False)

    def test_invalid_bounds_and_late_policy_never_invent_a_domain(self):
        for mutation in ('range','fraction','step','late','real'):
            request=tiny()
            if mutation=='range':request['bounds']['retained_A']['minimum']='0'
            elif mutation=='fraction':request['bounds']['additional_B']['maximum']='1.5'
            elif mutation=='step':request['bounds']['additional_B']['step']='2'
            elif mutation=='late':request['policy']['available_at']='2026-01-12T17:00:00+08:00'
            else:request['synthetic']=False
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):generate(request)


if __name__=='__main__':unittest.main()
