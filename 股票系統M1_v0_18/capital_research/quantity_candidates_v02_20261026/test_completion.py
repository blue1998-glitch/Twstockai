"""New protocol checks reuse actuals, plus only necessary API regressions."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from capital_research.quantity_candidates import generate

HERE=Path(__file__).parent
PRIOR=HERE.parent/'quantity_candidates_20261026'


def saved(name,kind='actual'):
    return json.loads((HERE/'cases'/name/(kind+'.json')).read_text())


class CompletionTests(unittest.TestCase):
    def test_manual_grid_and_all_A_sold_domain_are_complete(self):
        r=saved('first-manual-grid')['research'];expected=saved('first-manual-grid','expected')['manual_grid']
        pairs={(x['plan']['targets']['A'],x['plan']['targets']['B']) for x in r['candidates'] if x['plan']}
        self.assertTrue({tuple(x) for x in expected}<=pairs);self.assertEqual(r['grid_points'],9)
        r=saved('all-A-sale-partial-B')['research']
        self.assertEqual(r['grid_points'],6)
        self.assertTrue(all(any(x['plan'] and x['plan']['targets']['A']=='0' and x['plan']['targets']['B']==n for x in r['candidates']) for n in ('0','1','2')))
        self.assertFalse(r['account_liquidation_claimed'])

    def test_first_entry_requires_capital_but_not_new_trigger(self):
        r=saved('first-old-fact-reviewed')['research']
        self.assertTrue(r['baseline']['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertTrue(any(x['classification']=='CURRENTLY_FEASIBLE' and int(x['additional_B'] or '0')>0 for x in r['candidates']))
        for name in ('first-capital-unknown','first-invalidated'):
            self.assertTrue(all(x['classification']=='REJECTED' for x in saved(name)['research']['candidates'] if int(x['additional_B'] or '0')>0))

    def test_additional_requires_new_independent_event(self):
        old=saved('additional-old-trigger')['research'];new=saved('additional-independent')['research']
        self.assertTrue(all(x['classification']=='REJECTED' for x in old['candidates'] if int(x['additional_B'] or '0')>0))
        self.assertTrue(any(x['classification']=='CURRENTLY_FEASIBLE' and int(x['additional_B'] or '0')>0 for x in new['candidates']))
        for x in new['candidates']:
            if int(x['additional_B'] or '0')>0:self.assertEqual(x['plan']['family'],'C')

    def test_first_label_unknown_or_review_cannot_reset_history(self):
        for name,reason in [('cannot-relabel-first-after-fill','FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY'),
                            ('cannot-reset-first-without-history','FIRST_ENTRY_HISTORY_NOT_ESTABLISHED'),('unknown-batch-phase','BATCH_PHASE_UNKNOWN'),
                            ('known-history-not-erased','NEW_CAPITAL_NOT_QUALIFIED:B')]:
            r=saved(name)['research']
            with self.subTest(name=name):
                self.assertTrue(all(x['classification']=='REJECTED' for x in r['candidates'] if int(x['additional_B'] or '0')>0))
                self.assertTrue(any(reason in x['reasons'] for x in r['candidates']))

    def test_source_and_basis_mismatch_are_errors_not_zero_results(self):
        for name in ('review-mismatch-source_id','review-mismatch-basis_id'):
            r=saved(name);self.assertEqual(r['error_type'],'ValueError');self.assertIsNone(r['research'])

    def test_cost_reserve_receivable_and_wait_are_distinct(self):
        for name,available in [('cost-cannot-be-free','21'),('receivable-not-spendable','0')]:
            r=saved(name)['research'];buys=[x for x in r['candidates'] if x['plan'] and x['plan']['targets']['A']=='100' and x['plan']['targets']['B']=='1']
            self.assertEqual(len(buys),1);self.assertEqual(buys[0]['classification'],'REJECTED')
            self.assertEqual(buys[0]['core_evaluation']['available_settled_cash'],available)
        r=saved('wait-sale-settlement')['research']
        x=next(x for x in r['candidates'] if x['plan'] and x['plan']['targets']['A']=='95')
        self.assertEqual(x['classification'],'WAIT_SETTLEMENT_REASSESSMENT')

    def test_liquidity_common_risk_and_locked_shares(self):
        for name,reason in [('liquidity-limit','ENTRY_LIQUIDITY_LIMIT:B'),('common-risk-limit','RISK_LIMIT_EXCEEDED'),('sell-locked-A','SELLABLE_SHARES_RESERVED_OR_UNAVAILABLE:A')]:
            self.assertTrue(any(reason in x['reasons'] for x in saved(name)['research']['candidates']))

    def test_existing_buy_is_not_cancelled_reissued_or_double_reserved(self):
        r=saved('existing-B-order')['research'];original=saved('existing-B-order','input')['decision_input']['account']['pending_orders']
        self.assertEqual(r['original_pending_B_orders'],original)
        self.assertTrue(all(x['classification']=='NOT_IMPLEMENTED' for x in r['candidates'] if int(x.get('additional_B') or '0')>0))
        self.assertTrue(all(x['core_evaluation']['available_settled_cash']=='878' for x in r['candidates'] if x['core_evaluation']))

    def test_non_monotone_and_both_search_limits(self):
        r=saved('non-monotone')['research']
        observed={x['plan']['targets']['B']:x['classification'] for x in r['candidates'] if x['plan'] and x['plan']['targets']['A']=='100'}
        self.assertEqual(observed,{'0':'REJECTED','1':'CURRENTLY_FEASIBLE','2':'CURRENTLY_FEASIBLE','3':'REJECTED'})
        for name in ('grid-over-limit','full-over-limit'):
            r=saved(name)['research'];self.assertEqual(r['candidates'],[]);self.assertFalse(r['enumeration_complete'])

    def test_future_path_cannot_change_current_quantities_or_phase(self):
        initial=saved('first-manual-grid')
        for name in ('future-A-wins','future-B-wins','future-both-fall'):
            self.assertEqual(initial['research'],saved(name)['research'])
            self.assertNotEqual(initial['source_integrity_metadata'],saved(name)['source_integrity_metadata'])

    def test_original_capital_rights_latest_and_tokens_remain_bound(self):
        r=saved('additional-after-partial-fill')['research'];request=saved('additional-after-partial-fill','input');cp=request['continuation']['checkpoint']
        self.assertEqual(r['baseline']['continuity']['latest_predecessor_id'],cp['state']['latest_decision_id'])
        self.assertEqual(r['baseline']['continuity']['origin_initial_capital'],cp['state']['origin_initial_capital'])
        self.assertTrue(set(cp['state']['reviewed_evidence_tokens'])<=set(r['baseline']['reviewed_evidence_tokens']))
        self.assertEqual(r['baseline']['reserved_cash'],'100')
        for x in saved('all-A-sale-partial-B')['research']['candidates']:
            if x['plan']:self.assertEqual(x['plan']['targets']['C'],'2')

    def test_new_input_immutability_and_context_provenance(self):
        request=saved('first-manual-grid','input');request['bounds']=dict(sell_A=dict(minimum='1',maximum='1'),additional_B=dict(minimum='1',maximum='1'))
        original=deepcopy(request);generate(request);self.assertEqual(request,original)
        for field,value in [('account_id','wrong'),('basis_id','wrong'),('available_at','2026-01-12T17:00:00+08:00')]:
            bad=deepcopy(request);bad['batch_context'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):generate(bad)
        bad=deepcopy(request);bad['policy']['parameter_source']=''
        with self.assertRaises(ValueError):generate(bad)

    def test_v01_compatibility_only_two_necessary_regressions(self):
        for name in ('legal-grid','shared-volume-trigger'):
            request=json.loads((PRIOR/'cases'/name/'input.json').read_text());expected=json.loads((PRIOR/'after-final'/name/'actual.json').read_text())
            with self.subTest(name=name):self.assertEqual(generate(request),expected)

    def test_no_winner_order_fill_or_formal_qualification(self):
        for name in json.loads((HERE/'intake.json').read_text())['case_names']:
            r=saved(name).get('research')
            if r is None:continue
            self.assertIsNone(r['selected_id']);self.assertIsNone(r['ranking'])
            self.assertEqual(r['order_generation'],'NOT_PERFORMED');self.assertEqual(r['execution'],'NOT_PERFORMED')
            for key in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):self.assertIs(r[key],False)


if __name__=='__main__':unittest.main()
