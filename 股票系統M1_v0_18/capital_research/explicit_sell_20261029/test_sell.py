"""New sell milestone only; assert frozen actuals, accounting and selected regressions."""
import unittest
from decimal import Decimal as D
from .freeze import ROOT, PROJECT, REPO, load, save, info
from capital_research.core import fingerprint

FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')


def req(name):return load(ROOT/'cases'/name/'action-input.json')
def checked(name):return load(ROOT/'initial'/name/'checked-action.json')['research']
def run(name):return load(ROOT/'initial'/name/'result.json')['run']


class SellTests(unittest.TestCase):
    def test_01_frozen_oracles_sources_and_recovery_preserved(self):
        for m in load(ROOT/'frozen.json')['files']+load(ROOT/'intake.json')['protected']+load(ROOT/'initial/source-versions.json')['files']:
            self.assertEqual(info(REPO/m['path']),m)
        for pair in load(ROOT/'intake.json')['changing_sources']:
            self.assertEqual(info(REPO/pair['archived']['path']),pair['archived'])
        self.assertEqual(load(ROOT/'before/actual.json')['research']['status'],'INPUT_ERROR')
        recovery=load(ROOT/'diagnostics/environment-recovery.json')
        self.assertEqual(recovery['frozen_verified'],77);self.assertEqual(recovery['original_changing_sources_exact_before_resume'],2)
        save(ROOT/'test-evidence/preservation.json',dict(all_frozen_oracles_and_protected_sources_matched=True,old_versions_untouched=True,
            original_core_ledger_risk_unchanged=True,recovery_verified_before_edit=True))

    def test_02_all_frozen_status_reasons_versions_and_formal_flags(self):
        summary=load(ROOT/'initial/summary.json')
        self.assertTrue(summary['all_expected_status_reason_calls_matched']);self.assertTrue(summary['all_inputs_unchanged']);self.assertTrue(summary['all_saved_readbacks_equal'])
        self.assertEqual(summary['new_action_simulate_calls'],7)
        for name in load(ROOT/'case-index.json')['cases']:
            e=load(ROOT/'cases'/name/'expected.json');a=run(name);c=checked(name)
            self.assertEqual(c['status'],e['checked_status'],name);self.assertEqual(a['status'],e['run_status'],name)
            self.assertEqual(a['execution_calls'],e['simulate_calls'],name)
            self.assertTrue(all(a[k] is False and c[k] is False for k in FLAGS))
            self.assertIsNone(a['primary_pressure_id']);self.assertIsNone(a['ranking']);self.assertFalse(a['strategy_validated'])
            if e.get('reason'):self.assertIn(e['reason'],c['reasons'])
            if e.get('run_reason'):self.assertIn(e['run_reason'],a['reasons'])
            if e['simulate_calls']==0:self.assertIsNone(a['execution']);self.assertIsNone(a['checkpoint'])
            if name not in ('v01-sell-refused','cross-version'):self.assertEqual(a['schema'],'capital-cash-action-execution/0.2')
        self.assertEqual(checked('v01-sell-refused')['schema'],'capital-cash-action/0.1')

    def test_03_manual_costs_sale_claims_and_every_daily_accounting_identity(self):
        rows_out={}
        for name in ('reduce-B3','exit-B7','split-exit','partial-exit-B20','limit-down','capacity-zero','empty-orders'):
            e=load(ROOT/'cases'/name/'expected.json');a=run(name);ex=a['execution'];cp=a['checkpoint'];row=cp['state']['row']
            self.assertEqual(D(row['settled_cash']),D(e['final_cash']),name)
            self.assertEqual(row['shares']['B'],e['final_B']);self.assertEqual(row['shares']['C'],e['final_C']);self.assertEqual(row['shares']['A'],'0')
            fills=[f for f in ex['fills'] if f['id'] in ex['new_fill_ids']]
            self.assertEqual(len(fills),e['new_fills']);self.assertEqual(sum(int(f['shares']) for f in fills),int(e['new_shares']))
            self.assertTrue(all(f['side']=='SELL' and f['code']=='B' for f in fills))
            self.assertEqual(sum((D(f['fee']) for f in fills),D(0)),D(e['fees']))
            self.assertEqual(sum((D(f['tax']) for f in fills),D(0)),D(e['tax']))
            proceeds=sum((D(f['shares'])*D(f['price'])-D(f['fee'])-D(f['tax']) for f in fills),D(0))
            self.assertEqual(proceeds,D(e['sale_receivable']))
            rows={r['date']:r for r in ex['ledger']['daily']};trade=rows['2026-01-09'];old=req(name)['account_source']['checkpoint']['state']['row']
            self.assertEqual(D(trade['settled_cash']),D(old['settled_cash']))
            self.assertEqual(D(trade['available_cash_strict']),D(old['settled_cash']))
            self.assertEqual(D(trade['cash_receivable']),D('80')+proceeds)
            self.assertEqual(trade['shares']['C'],'2');self.assertEqual(trade['share_receivables'][0]['shares'],'2')
            for r in rows.values():
                assets=sum(D(q)*D(r['marks'][c]['value']) for c,q in r['shares'].items())
                rights=sum(D(x['shares'])*D(r['marks'][x['code']]['value']) for x in r['share_receivables'])
                self.assertEqual(D(r['settled_cash'])+D(r['cash_receivable'])-D(r['purchase_payable'])+assets+rights,D(r['net_accrual_equity']))
            if ex['observed_until'].startswith('2026-01-12'):
                self.assertEqual(row['cash_claims'],[]);self.assertEqual(row['share_receivables'],[])
                self.assertEqual(D(row['settled_cash']),D(old['settled_cash'])+D('80')+proceeds)
            if 'remaining' in e:
                st=ex['order_states']['sell-B-explicit'];self.assertEqual(st['remaining'],e['remaining']);self.assertEqual(st['status'],e['order_status']);self.assertEqual(st['reserved_cash'],'0')
            rows_out[name]=[dict(date=r['date'],cash=r['settled_cash'],receivable=r['cash_receivable'],available=r['available_cash_strict'],shares=r['shares']) for r in rows.values()]
        save(ROOT/'test-evidence/daily-handcheck.json',dict(rows=rows_out,every_daily_identity_matched=True,sale_proceeds_not_spendable_before_settlement=True,
            split_fees_and_tax_counted_per_original_fill_model=True,original_costs_not_recharged=True))

    def test_04_complete_origin_latest_history_tokens_and_untouched_assets(self):
        for name in ('reduce-B3','exit-B7','partial-exit-B20'):
            original=req(name)['account_source']['checkpoint'];old=original['execution_result'];a=run(name);ex=a['execution'];cp=a['checkpoint'];c=checked(name)
            self.assertEqual(a['execution_job']['continuation']['checkpoint'],original)
            self.assertEqual(cp['origin_ledger_input'],original['origin_ledger_input'])
            self.assertEqual(cp['state']['origin_initial_capital'],'1180');self.assertEqual(cp['state']['general_reserved_cash'],'100')
            self.assertEqual(ex['fills'][:len(old['fills'])],old['fills'])
            self.assertEqual(ex['decision_ids'][:-1],old['decision_ids'])
            self.assertEqual(ex['latest_decision_id'],c['core_decision']['decision_id'])
            self.assertEqual(c['core_decision']['continuity']['latest_predecessor_id'],old['latest_decision_id'])
            for key,value in old['decision_records'].items():self.assertEqual(ex['decision_records'][key],value)
            for key,value in old['fact_sources'].items():self.assertEqual(ex['fact_sources'][key],value)
            self.assertEqual(ex['reassessment_attempts'],old['reassessment_attempts'])
            self.assertEqual(ex['reviewed_evidence_tokens'],old['reviewed_evidence_tokens'])
            self.assertEqual(set(cp['state']['reviewed_evidence_tokens']),set(old['reviewed_evidence_tokens']))
            self.assertEqual(ex['opening_unavailable_shares'],old['opening_unavailable_shares'])
            for key,value in old['order_states'].items():self.assertEqual(ex['order_states'][key],value)
            self.assertEqual(ex['ledger']['daily'][:len(old['ledger']['daily'])],old['ledger']['daily'])
            targets=c['intent']['plan']['targets']
            for code in ('A','C'):self.assertEqual(targets[code],original['state']['row']['shares'][code])
            self.assertFalse(c['intent']['account_liquidation_claimed']);self.assertFalse(c['intent']['sale_scope']['account_liquidation_claimed'])
        self.assertEqual(run('exit-B7')['checkpoint']['state']['row']['shares']['C'],'4')
        save(ROOT/'test-evidence/continuous-origin.json',dict(origin_capital='1180',reserve='100',all_parent_fills_records_facts_tokens_preserved=True,
            other_stock_C_rights_preserved=True,specified_stock_exit_not_account_liquidation=True))

    def test_05_full_checked_bindings_and_wrong_order_scope(self):
        for name in ('exit-B7','reduce-B3'):
            r=load(ROOT/'initial'/name/'execution-input.json');a=run(name)
            self.assertEqual(r['expected_checked_action_id'],fingerprint(r['checked_action']))
            self.assertEqual(r['checked_action']['source_integrity_metadata']['full_request_id'],fingerprint(r['action_input']))
            self.assertEqual(a['binding']['checked_action_id'],fingerprint(r['checked_action']))
            self.assertEqual(a['execution_job']['orders'],r['execution_spec']['orders'])
        for name in ('buy-injection','oversplit','tampered-checked','cross-version'):
            self.assertEqual(run(name)['execution_calls'],0);self.assertEqual(run(name)['status'],'INPUT_ERROR')
        a=load(ROOT/'controls/wrong-order-code/actual.json')['run']
        self.assertEqual(a['status'],'INPUT_ERROR');self.assertEqual(a['reasons'],['ORDER_OUTSIDE_CHECKED_ACTION_SCOPE']);self.assertEqual(a['execution_calls'],0)

    def test_06_partial_sale_continuation_settles_once_and_equals_full_path(self):
        a=load(ROOT/'controls/partial/actual.json');self.assertEqual(a['status'],'CONTINUED_ORIGINAL_ORDERS')
        self.assertTrue(all(load(ROOT/'controls/partial/comparison.json').values()))
        prefix=run('partial-exit-B20');ex=a['execution'];row=a['checkpoint']['state']['row']
        self.assertEqual(ex['fills'],prefix['execution']['fills']);self.assertEqual(a['new_fill_ids_this_segment'],[])
        self.assertEqual(row['shares'],dict(A='0',B='13',C='4'));self.assertEqual(D(row['settled_cash']),D('816.460'))
        self.assertEqual(row['cash_claims'],[]);self.assertEqual(row['share_receivables'],[])
        st=ex['order_states']['sell-B-explicit'];self.assertEqual(st['status'],'EXPIRED_UNFILLED');self.assertEqual(st['remaining'],'13')
        self.assertEqual(a['checkpoint']['state']['general_reserved_cash'],'100');self.assertEqual(a['checkpoint']['state']['origin_initial_capital'],'1180')
        for key in ('decision_ids','decision_records','latest_decision_id','fact_sources','reassessment_attempts','reviewed_evidence_tokens'):
            self.assertEqual(ex[key],prefix['execution'][key])

    def test_07_future_isolation_context_purity_and_new_capital_separation(self):
        self.assertTrue(all(load(ROOT/'controls/future/comparison.json').values()))
        for row in load(ROOT/'controls/context/actual.json'):
            self.assertTrue(all(v for k,v in row.items() if k!='context'))
        r=load(ROOT/'controls/not-new-capital-qualified/actual.json')['research']
        self.assertEqual(r['status'],'CURRENTLY_FEASIBLE')
        self.assertFalse(r['core_decision']['layer2']['B']['capital_eligibility']['qualified_for_synthetic_proposal'])
        self.assertTrue(all(r[k] is False for k in FLAGS))

    def test_08_three_v01_results_stay_exact(self):
        for row in load(ROOT/'controls/legacy/summary.json'):self.assertTrue(row['complete_saved_result_equal'],row['name'])
        for name in ('hold','independent-B20','old-trigger'):
            binding=load(ROOT/'controls/legacy'/name/'binding.json')
            for meta in binding.values():self.assertEqual(info(REPO/meta['path']),meta)
            saved=load(REPO/binding['expected']['path'])
            self.assertEqual(load(ROOT/'controls/legacy'/name/'actual.json'),saved)


if __name__=='__main__':unittest.main()
