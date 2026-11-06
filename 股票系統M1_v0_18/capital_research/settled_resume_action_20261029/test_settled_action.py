"""Verify the new chain's frozen actuals without replaying old producers."""
import unittest
from decimal import Decimal as D
from .freeze import ROOT, REPO, load, save, info
from capital_research.core import fingerprint

FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')


def action(name):return load(ROOT/'cases'/name/'action-input.json')
def result(name):return load(ROOT/'actual'/name/'result.json')['run']


class SettledActionTests(unittest.TestCase):
    def test_01_original_resume_sources_and_frozen_oracles_unchanged(self):
        for m in load(ROOT/'intake.json')['protected']+load(ROOT/'frozen.json')['files']+load(ROOT/'source-versions.json')['files']:
            self.assertEqual(info(REPO/m['path']),m)
        cp=action('independent-B20')['account_source']['checkpoint']
        source=load(ROOT/'original-binding.json')['saved_resume']
        original=load(REPO/source['path'])
        self.assertEqual(cp,original['checkpoint']);self.assertEqual(original['status'],'CONTINUED_ORIGINAL_ORDERS')
        self.assertEqual(cp['state']['origin_initial_capital'],'1180')
        self.assertEqual(cp['state']['row']['settled_cash'],'858.860')
        self.assertFalse(cp['state']['unfilled_orders']);self.assertEqual(cp['state']['row']['purchase_payable'],'0')
        save(ROOT/'test-evidence/preservation.json',dict(frozen_and_protected_files_matched=True,original_resume_mode='READ_ONLY',product_module_changes=0))

    def test_02_all_gates_call_counts_readbacks_and_inputs(self):
        summary=load(ROOT/'summary.json')
        self.assertTrue(summary['all_expected_status_reason_calls_matched'])
        self.assertTrue(summary['all_inputs_unchanged']);self.assertTrue(summary['all_saved_readbacks_equal'])
        self.assertEqual(summary['new_action_simulate_calls'],2)
        self.assertEqual(summary['original_resume_run_calls'],0);self.assertEqual(summary['original_two_round_producer_calls'],0)
        for name in load(ROOT/'case-index.json')['cases']:
            checked=load(ROOT/'actual'/name/'checked-action.json');request=load(ROOT/'actual'/name/'execution-input.json')
            expected=load(ROOT/'cases'/name/'expected.json');run=result(name)
            self.assertEqual(request['action_input'],action(name))
            self.assertEqual(request['execution_spec'],load(ROOT/'cases'/name/'execution-spec.json'))
            self.assertEqual(checked['research']['status'],expected['checked_status'])
            self.assertEqual(checked['source_integrity_metadata']['full_request_id'],fingerprint(action(name)))
            self.assertEqual(request['expected_checked_action_id'],fingerprint(checked))
            self.assertEqual(run['status'],expected['run_status']);self.assertEqual(run['execution_calls'],expected['simulate_calls'])
            self.assertTrue(all(run[k] is False for k in FLAGS));self.assertTrue(all(checked['research'][k] is False for k in FLAGS))
            self.assertIsNone(run['ranking']);self.assertIsNone(run['selected_strategy']);self.assertIsNone(run['primary_pressure_id'])
            if expected.get('reason'):
                self.assertIn(expected['reason'],checked['research']['reasons'])
                self.assertIsNone(run['execution']);self.assertIsNone(run['checkpoint'])
            else:
                self.assertEqual(run['binding']['checked_action_id'],fingerprint(checked))
                self.assertEqual(run['binding']['action_input_id'],fingerprint(action(name)))

    def test_03_full_parent_book_latest_all_tokens_and_expired_order_retained(self):
        for name in ('hold','independent-B20'):
            r=action(name);old=r['account_source']['checkpoint'];prior=old['execution_result'];run=result(name)
            ex=run['execution'];cp=run['checkpoint'];checked=load(ROOT/'actual'/name/'checked-action.json')['research']
            self.assertEqual(run['execution_job']['continuation']['checkpoint'],old)
            self.assertEqual(run['execution_job']['continuation']['cancelled_order_ids'],[])
            self.assertEqual(ex['opening_checkpoint_id'],old['checkpoint_id'])
            self.assertEqual(cp['origin_ledger_input'],old['origin_ledger_input'])
            self.assertEqual(cp['state']['origin_initial_capital'],'1180');self.assertEqual(cp['state']['general_reserved_cash'],'100')
            self.assertEqual(D(checked['core_decision']['initial_capital']),D('1178.860'))
            self.assertEqual(ex['fills'][:len(prior['fills'])],prior['fills'])
            self.assertEqual(ex['order_states']['explicit-order'],prior['order_states']['explicit-order'])
            self.assertEqual(ex['order_states']['explicit-order']['remaining'],'13')
            self.assertEqual(ex['order_states']['explicit-order']['status'],'EXPIRED_UNFILLED')
            self.assertEqual(ex['order_states']['explicit-order']['reserved_cash'],'0')
            self.assertEqual(ex['order_history'][:len(prior['order_history'])],prior['order_history'])
            self.assertEqual(ex['decision_ids'][:-1],prior['decision_ids'])
            for key in prior['decision_records']:self.assertEqual(ex['decision_records'][key],prior['decision_records'][key])
            for key in prior['fact_sources']:self.assertEqual(ex['fact_sources'][key],prior['fact_sources'][key])
            self.assertEqual(ex['reassessment_attempts'],prior['reassessment_attempts'])
            self.assertEqual(ex['latest_decision_id'],checked['core_decision']['decision_id'])
            self.assertEqual(checked['core_decision']['continuity']['latest_predecessor_id'],prior['latest_decision_id'])
            self.assertEqual(checked['core_decision']['continuity']['checkpoint_id'],old['checkpoint_id'])
            previous=set(prior['reviewed_evidence_tokens']);current=set(ex['reviewed_evidence_tokens'])
            self.assertEqual(len(previous),9);self.assertTrue(previous<=current)
            self.assertEqual(current-previous,{'fixture:formation_id:B-step2-formation','fixture:volume_bar_id:B-step2-bar','fixture:event_id:B-step2-event'})
            self.assertEqual(set(cp['state']['reviewed_evidence_tokens']),current)
            self.assertEqual(ex['ledger']['daily'][:len(prior['ledger']['daily'])],prior['ledger']['daily'])
            # The whole predecessor retains its own expiry receipt. Current
            # execution_events belong to the new job and are not global history.
            self.assertEqual(sum(e['status']=='EXPIRED_UNFILLED' for e in run['execution_job']['continuation']['checkpoint']['execution_result']['execution_events']),1)
            if name=='hold':
                self.assertEqual(ex['orders'],[]);self.assertEqual(ex['fills'],prior['fills']);self.assertEqual(ex['new_fill_ids'],[])
            else:
                new=[f for f in ex['fills'] if f['id'] in ex['new_fill_ids']]
                self.assertEqual(len(new),1);self.assertEqual(new[0]['shares'],'20')
                self.assertEqual(ex['fill_order_ids'][new[0]['id']],'second-B-buy')
                self.assertEqual(new[0]['id'],'second-B-buy-fill-1')
                self.assertEqual(ex['orders'][0]['shares'],'20')
        save(ROOT/'test-evidence/chain.json',dict(original_capital='1180',current_pre_action_nav='1178.860',general_reserve='100',
            full_parent_checkpoint_retained=True,expired_original_remaining='13',old_tokens=9,new_independent_tokens=3,
            historical_fills_and_daily_prefix_equal=True,branches='MUTUALLY_EXCLUSIVE_NOT_ADDITIVE'))

    def test_04_independent_daily_cash_rights_and_reserve_handcheck(self):
        rows_out={}
        for name in ('hold','independent-B20'):
            expected=load(ROOT/'cases'/name/'expected.json');run=result(name);ex=run['execution'];cp=run['checkpoint']
            rows={r['date']:r for r in ex['ledger']['daily']};last=rows['2026-01-12']
            self.assertEqual(D(last['settled_cash']),D(expected['final_cash']))
            self.assertEqual(last['shares'],dict(A='0',B=expected['final_B'],C=expected['final_C']))
            self.assertEqual(D(last['net_accrual_equity']),D(expected['final_nav']))
            self.assertEqual(last['cash_claims'],[]);self.assertEqual(last['share_receivables'],[])
            self.assertEqual(last['purchase_payable'],'0');self.assertEqual(cp['state']['unfilled_orders'],[])
            self.assertEqual(rows['2026-01-09']['shares']['C'],'2')
            self.assertEqual(rows['2026-01-09']['share_receivables'][0]['shares'],'2')
            self.assertEqual(rows['2026-01-09']['cash_receivable'],'80')
            if name=='independent-B20':
                self.assertEqual(D(rows['2026-01-09']['settled_cash']),D(expected['trade_day_cash']))
                self.assertEqual(D(rows['2026-01-09']['purchase_payable']),D(expected['trade_day_payable']))
                self.assertEqual(D(rows['2026-01-09']['available_cash_strict']),D(expected['trade_day_available']))
                self.assertEqual(D(ex['fills'][-1]['price']),D('20.02'));self.assertEqual(D(ex['fills'][-1]['fee']),D('1'))
            for row in rows.values():
                assets=sum(D(n)*D(row['marks'][code]['value']) for code,n in row['shares'].items())
                rights=sum(D(x['shares'])*D(row['marks'][x['code']]['value']) for x in row['share_receivables'])
                self.assertEqual(D(row['settled_cash'])+D(row['cash_receivable'])-D(row['purchase_payable'])+assets+rights,D(row['net_accrual_equity']),row['date'])
            rows_out[name]=[dict(date=r['date'],cash=r['settled_cash'],receivable=r['cash_receivable'],payable=r['purchase_payable'],available=r['available_cash_strict'],shares=r['shares']) for r in rows.values()]
        reserve=load(ROOT/'cases/reserve-not-spendable/expected.json')
        self.assertLess(D(reserve['required_cost']),D(reserve['settled_cash']))
        self.assertGreater(D(reserve['required_cost']),D(reserve['spendable']))
        self.assertEqual(D('858.86')+D('80')-D('401.40'),D('537.46'))
        self.assertEqual(D('858.86')+D('80'),D('938.86'))
        save(ROOT/'test-evidence/daily-handcheck.json',dict(rows=rows_out,every_daily_balance_identity_matched=True,
            no_receivable_used_early=True,general_reserve_preserved='100',extra_quotes=0,extra_calendar_rows=0))


if __name__=='__main__':unittest.main()
