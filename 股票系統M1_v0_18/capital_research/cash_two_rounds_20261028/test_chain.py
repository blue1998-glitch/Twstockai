"""Inspect only the new two-round evidence; no extra execute or old-suite RUN."""
import unittest
from decimal import Decimal
from capital_research.core import fingerprint
from .freeze import ROOT,OLD,REPO,load,save,info

FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')


def request(name):return load(ROOT/'cases'/name/'input.json')
def actual(name):return load(ROOT/'actual'/name/'result.json')


class ChainTests(unittest.TestCase):
    def test_01_first_round_read_only_frozen_inputs_and_old_sources_unchanged(self):
        for row in load(ROOT/'frozen.json')['files']+load(ROOT/'intake.json')['protected']+load(ROOT/'source-versions.json'):
            self.assertEqual(info(REPO/row['path']),row)
        first=load(OLD/'actual/opening-B20/result.json')['run'];cp=first['checkpoint']
        self.assertEqual(cp['state']['through_at'],'2026-01-08T16:00:00+08:00')
        self.assertEqual(cp['state']['unfilled_orders'],[]);self.assertEqual(cp['state']['row']['purchase_payable'],'0')
        self.assertEqual(cp['state']['general_reserved_cash'],'100')
        summary=load(ROOT/'summary.json')
        self.assertTrue(summary['all_status_reasons_calls_matched']);self.assertTrue(summary['all_inputs_unchanged'])
        self.assertEqual(summary['first_round_simulate_calls'],0);self.assertEqual(summary['second_round_simulate_calls'],1)
        self.assertEqual(summary['production_module_changes'],0);self.assertEqual(summary['quote_or_calendar_additions'],0)
        # The old first result is a READ receipt, not a newly generated first execution.
        self.assertFalse(load(ROOT/'first-round-binding.json')['first_execution_this_round'])

    def test_02_exact_origin_first_prefix_fills_latest_and_all_tokens(self):
        r=request('independent-B20');result=actual('independent-B20');run=result['run'];e=run['execution'];cp=run['checkpoint']
        first=load(OLD/'actual/opening-B20/result.json')['run'];prior=first['execution'];old=first['checkpoint'];expected=load(ROOT/'cases/independent-B20/expected.json')
        self.assertEqual(run['status'],'REPLAYED_EXPLICIT_ACTION')
        self.assertEqual(cp['origin_ledger_input'],old['origin_ledger_input'])
        self.assertEqual(run['execution_job']['ledger_input'],old['origin_ledger_input'])
        self.assertEqual(cp['state']['origin_initial_capital'],expected['original_capital'])
        self.assertEqual(cp['state']['general_reserved_cash'],expected['reserve'])
        self.assertEqual(run['execution_job']['decision_input']['account']['settled_cash'],expected['incoming_cash'])
        self.assertEqual(run['numeric_result']['decision']['initial_capital'],expected['current_nav_before_second'])
        self.assertEqual(run['numeric_result']['decision']['continuity']['origin_initial_capital'],'1180')
        self.assertEqual(run['numeric_result']['decision']['continuity']['external_flow'],'0')
        self.assertEqual(e['fills'][:len(prior['fills'])],prior['fills'])
        self.assertEqual(len(e['fills']),2);self.assertEqual(len(e['new_fill_ids']),1)
        self.assertEqual(len({f['id'] for f in e['fills']}),2)
        self.assertEqual(e['new_fill_ids'],['second-B-buy-fill-1'])
        self.assertEqual(e['order_states']['explicit-order'],prior['order_states']['explicit-order'])
        self.assertEqual(e['order_states']['second-B-buy']['remaining'],'0');self.assertEqual(e['order_states']['second-B-buy']['status'],'FILLED')
        self.assertEqual(e['fill_order_ids']['explicit-order-fill-0'],'explicit-order');self.assertEqual(e['fill_order_ids']['second-B-buy-fill-1'],'second-B-buy')
        self.assertEqual(e['ledger']['daily'][:len(prior['ledger']['daily'])],prior['ledger']['daily'])
        self.assertEqual(e['decision_ids'][:-1],prior['decision_ids'])
        self.assertEqual(e['decision_ids'][-1],r['checked_action']['research']['core_decision']['decision_id'])
        self.assertEqual(cp['state']['latest_decision_id'],e['decision_ids'][-1])
        self.assertEqual(e['latest_common_account_id'],r['checked_action']['research']['core_decision']['common_account_id'])
        for key in prior['decision_records']:self.assertEqual(e['decision_records'][key],prior['decision_records'][key])
        for key in prior['fact_sources']:self.assertEqual(e['fact_sources'][key],prior['fact_sources'][key])
        self.assertEqual(e['reassessment_attempts'],prior['reassessment_attempts'])
        old_tokens=set(prior['reviewed_evidence_tokens']);new_tokens={'fixture:event_id:B-step2-event','fixture:formation_id:B-step2-formation','fixture:volume_bar_id:B-step2-bar'}
        self.assertEqual(len(old_tokens),expected['reviewed_old_tokens'])
        self.assertEqual(set(e['reviewed_evidence_tokens']),old_tokens|new_tokens)
        self.assertEqual(len(e['reviewed_evidence_tokens']),expected['reviewed_tokens'])
        self.assertEqual(set(run['numeric_result']['decision']['new_evidence_tokens']),new_tokens)
        self.assertEqual(run['execution_job']['decision_input']['plans'][0]['family'],'C')
        self.assertEqual(run['binding']['account']['latest_predecessor_id'],prior['latest_decision_id'])
        self.assertEqual(run['binding']['account']['checkpoint_id'],old['checkpoint_id'])
        self.assertEqual(run['binding']['checked_action_id'],fingerprint(r['checked_action']))
        self.assertEqual(result['source_integrity_metadata']['full_request_id'],fingerprint(r))
        self.assertTrue(all(run[k] is False for k in FLAGS));self.assertIsNone(run['primary_pressure_id']);self.assertIsNone(run['ranking'])
        self.assertEqual(cp['state']['unfilled_orders'],[])
        save(ROOT/'test-evidence/continuity.json',dict(first_execution_reused_not_rerun=True,old_prefix_rows_exact=True,
            original_opening_unchanged=True,original_capital='1180',current_nav_before_second='1178.600',
            old_fills_preserved=1,new_fills=1,unique_fill_count=2,old_reviewed_tokens=9,new_independent_tokens=3,total_reviewed_tokens=12,
            exact_latest_and_all_fact_sources_preserved=True,reserve='100',product_code_changes=0))

    def test_03_all_counterexamples_stop_before_execution_and_budget_roles_are_separate(self):
        for name in load(ROOT/'case-index.json')['cases'][1:]:
            r=request(name);checked=r['checked_action']['research'];run=actual(name)['run'];expected=load(ROOT/'cases'/name/'expected.json')
            self.assertEqual(checked['status'],expected['checked_status']);self.assertIn(expected['reason'],checked['reasons'])
            self.assertEqual(run['status'],'STOPPED_ACTION_GATE');self.assertEqual(run['execution_calls'],0)
            self.assertIsNone(run['execution']);self.assertIsNone(run['checkpoint']);self.assertIsNone(run['execution_job'])
            self.assertEqual(checked['research_recommendation']['candidate_ids'],[])
            self.assertTrue(all(run[k] is False for k in FLAGS))
        self.assertTrue(request('false-first-entry')['checked_action']['research']['intent']['core_evaluation']['feasible'])
        for name in ['reserve-not-reused','receivable-not-spendable']:
            r=request(name);checked=r['checked_action']['research'];expected=load(ROOT/'cases'/name/'expected.json')
            evaluation=checked['intent']['core_evaluation'];account=r['checked_action']['source_integrity_metadata']['derived_decision_input']['account']
            self.assertEqual(Decimal(evaluation['purchase_payable_estimate']),Decimal(expected['required_cost']))
            self.assertEqual(Decimal(account['settled_cash']),Decimal('598.6'));self.assertEqual(Decimal(account['reserved_cash']),100)
            self.assertEqual(Decimal(evaluation['available_settled_cash']),Decimal('498.6'))
            if name=='reserve-not-reused':self.assertLess(Decimal(evaluation['purchase_payable_estimate']),Decimal(account['settled_cash']))
            else:
                self.assertGreater(Decimal(evaluation['purchase_payable_estimate']),Decimal(account['settled_cash']))
                self.assertLess(Decimal(evaluation['purchase_payable_estimate']),Decimal(account['settled_cash'])+Decimal(account['cash_claims'][0]['amount']))

    def test_04_daily_cash_payables_rights_and_original_window_match_manual_expected(self):
        r=request('independent-B20');run=actual('independent-B20')['run'];cp=run['checkpoint'];rows=run['execution']['ledger']['daily']
        spec=r['execution_spec'];old_tape=load(OLD/'cases/exited-A-buy-B20/input.json')['execution_spec']['tape']
        self.assertEqual(spec['tape'],old_tape);self.assertEqual(spec['origin_ledger'],r['action_input']['account_source']['checkpoint']['origin_ledger_input'])
        self.assertEqual((spec['origin_ledger']['start'],spec['origin_ledger']['end']),('2026-01-05','2026-01-12'))
        self.assertTrue(all('2026-01-08'<o['at'][:10]<='2026-01-12' for o in spec['tape']))
        # Independent stated ledger roles: cash changes on settlement; fees are
        # paid once in each fill. A claim is not a deposit or available balance.
        manual={
            '2026-01-05':('1000','0','1000','0','1180'),
            '2026-01-06':('1000','401.4','598.6','20','1178.6'),
            '2026-01-07':('1000','401.4','598.6','20','1178.6'),
            '2026-01-08':('598.6','0','598.6','20','1178.6'),
            '2026-01-09':('598.6','401.4','197.2','40','1177.2'),
            '2026-01-10':('598.6','401.4','197.2','40','1177.2'),
            '2026-01-11':('598.6','401.4','197.2','40','1177.2'),
            '2026-01-12':('277.2','0','277.2','40','1177.2')}
        for row in rows:
            cash,payable,available,b,nav=manual[row['date']]
            for key,value in [('settled_cash',cash),('purchase_payable',payable),('available_cash_strict',available),('net_accrual_equity',nav)]:
                self.assertEqual(Decimal(row[key]),Decimal(value),row['date']+':'+key)
            self.assertEqual(row['shares']['B'],b)
            if row['date']<'2026-01-12':
                self.assertEqual(row['shares']['C'],'2');self.assertEqual(row['share_receivables'][0]['shares'],'2')
                self.assertEqual(Decimal(row['cash_claims'][0]['amount']),80)
            else:
                self.assertEqual(row['shares']['C'],'4');self.assertEqual(row['share_receivables'],[]);self.assertEqual(row['cash_claims'],[])
        self.assertEqual(cp['state']['row']['purchase_payable'],'0')
        save(ROOT/'test-evidence/daily-balances.json',dict(qualified_only_as='SYNTHETIC_MECHANISM_NOT_MARKET_PERFORMANCE',
            original_capital='1180',final_cash='277.2',final_B='40',final_C='4',final_nav='1177.2',
            first_buy_cost='401.4',second_buy_cost='401.4',opening_cash_claim_received_once='80',general_reserve='100',
            all_daily_rows_match_manual=True,market_quote_and_calendar_additions=0))


if __name__=='__main__':unittest.main(verbosity=2)
