"""Targeted new nested-root chain assertions, no old producer rerun."""
import unittest
from copy import deepcopy
from decimal import Decimal as D
from .freeze import ROOT, PROJECT, REPO, load, save, info

FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')


def actual(name):return load(ROOT/'actual'/name/'result.json')


class PartialBatchResumeTests(unittest.TestCase):
    def test_01_frozen_models_and_original_sources_preserved(self):
        for m in load(ROOT/'intake.json')['protected']+load(ROOT/'frozen.json')['files']+load(ROOT/'source-versions.json')['files']:
            self.assertEqual(info(REPO/m['path']),m)
        old=load(PROJECT/'capital_research/settled_resume_action_20261029/actual/independent-B20/result.json')['run']
        root=load(ROOT/'root-input.json');expected=deepcopy(old['execution_job']);expected['tape']=root['tape']
        self.assertEqual(root,expected)
        source=load(PROJECT/'capital_research/cash_execution_20261028/cases/partial-7-active-13/input.json')
        self.assertEqual(root['tape'],source['execution_spec']['tape'])
        self.assertEqual(old['execution']['order_states']['second-B-buy']['status'],'FILLED')
        self.assertEqual(old['execution']['fills'][-1]['shares'],'20')
        checks=load(ROOT/'actual/prefix-input-check.json');self.assertTrue(all(checks.values()))
        self.assertEqual(load(ROOT/'actual/prefix-action-result.json')['run']['execution_job'],load(ROOT/'prefix-input.json'))
        self.assertEqual(root['continuation']['checkpoint'],old['execution_job']['continuation']['checkpoint'])
        self.assertEqual(load(ROOT/'path.json')['session_coverage'][-1]['date'],'2026-01-12')
        self.assertEqual(load(ROOT/'path.json')['session_coverage'][-1]['observation_ids'],[])
        self.assertIs(load(ROOT/'path.json')['session_coverage'][-1]['no_other_execution_opportunities'],True)
        save(ROOT/'test-evidence/preservation.json',dict(all_frozen_and_original_bytes_matched=True,old_full_fill_actual_unchanged=True,
            only_new_model_capacity_differs=True,product_module_changes=0,quotes_added=0,calendar_rows_added=0))

    def test_02_partial_payable_rights_reserves_and_every_day_handcheck(self):
        e=load(ROOT/'expected.json');prefix=load(ROOT/'actual/prefix-action-result.json')['run'];cp=prefix['checkpoint'];s=cp['state']
        for field,key in [('settled_cash','prefix_cash'),('purchase_payable','prefix_payable'),('available_cash_strict','prefix_available')]:
            self.assertEqual(D(s['row'][field]),D(e[key]))
        self.assertEqual(s['row']['shares'],dict(A='0',B='14',C='2'))
        self.assertEqual(s['row']['cash_receivable'],'80');self.assertEqual(s['row']['share_receivables'][0]['shares'],'2')
        self.assertEqual(s['origin_initial_capital'],e['origin_capital']);self.assertEqual(s['general_reserved_cash'],e['general_reserve'])
        st=s['order_states']['second-B-buy'];self.assertEqual(st['status'],'PARTIAL');self.assertEqual(st['remaining'],e['remaining']);self.assertEqual(st['reserved_cash'],e['reserved'])
        self.assertEqual(prefix['execution']['fills'][-1]['id'],'second-B-buy-fill-1')
        self.assertEqual(prefix['execution']['fills'][-1]['shares'],'7')
        self.assertEqual(D(prefix['execution']['fills'][-1]['price']),D('20.02'));self.assertEqual(D(prefix['execution']['fills'][-1]['fee']),D('1'))
        mid=actual('to-Jan10')['checkpoint']['state']
        self.assertEqual(D(mid['row']['settled_cash']),D(e['prefix_cash']))
        self.assertEqual(D(mid['row']['purchase_payable']),D(e['prefix_payable']))
        self.assertEqual(mid['order_states']['second-B-buy'],st)
        for name in ('direct','Jan10-to-Jan12'):
            a=actual(name);last=a['checkpoint']['state']['row'];ex=a['execution']
            self.assertEqual(D(last['settled_cash']),D(e['final_cash']))
            self.assertEqual(last['shares'],dict(A='0',B=e['final_B'],C=e['final_C']))
            self.assertEqual(last['purchase_payable'],e['final_payable']);self.assertEqual(D(last['net_accrual_equity']),D(e['final_nav']))
            self.assertEqual(last['cash_claims'],[]);self.assertEqual(last['share_receivables'],[])
            self.assertEqual(a['checkpoint']['state']['unfilled_orders'],[])
            self.assertEqual(ex['order_states']['second-B-buy']['status'],e['final_status'])
            self.assertEqual(ex['order_states']['second-B-buy']['remaining'],e['remaining']);self.assertEqual(ex['order_states']['second-B-buy']['reserved_cash'],'0')
            self.assertEqual(a['new_fill_ids_this_segment'],[]);self.assertEqual(ex['new_fill_ids'],['second-B-buy-fill-1'])
            self.assertEqual(ex['fills'],prefix['execution']['fills']);self.assertEqual(len(ex['fills']),2)
            self.assertEqual(sum(event['status']=='EXPIRED_UNFILLED' for event in ex['execution_events']),1)
            expiry=next(event for event in ex['execution_events'] if event['status']=='EXPIRED_UNFILLED')
            self.assertEqual(expiry['at'],'2026-01-12T12:00:00+08:00');self.assertEqual(expiry['order_id'],'second-B-buy')
        rows=actual('direct')['execution']['ledger']['daily']
        for row in rows:
            assets=sum(D(n)*D(row['marks'][c]['value']) for c,n in row['shares'].items())
            rights=sum(D(x['shares'])*D(row['marks'][x['code']]['value']) for x in row['share_receivables'])
            self.assertEqual(D(row['settled_cash'])+D(row['cash_receivable'])-D(row['purchase_payable'])+assets+rights,D(row['net_accrual_equity']),row['date'])
        self.assertEqual(D('858.86')+D('80')-(D('7')*D('20.02')+D('1')),D('797.72'))
        save(ROOT/'test-evidence/daily-handcheck.json',dict(origin_capital='1180',general_reserve='100',
            rows=[dict(date=r['date'],cash=r['settled_cash'],receivable=r['cash_receivable'],payable=r['purchase_payable'],available=r['available_cash_strict'],shares=r['shares']) for r in rows],
            all_daily_balance_identities_matched=True,settlement_posts_once=True,remaining_new_order_expires_without_fill=True))

    def test_03_one_shot_and_two_segments_complete_state_and_ancestry_equal(self):
        root=load(ROOT/'root-input.json');old=root['continuation']['checkpoint'];prefix=load(ROOT/'actual/prefix-action-result.json')['run']['checkpoint']
        whole=load(ROOT/'control/one-shot-execution.json');whole_cp=load(ROOT/'control/one-shot-checkpoint.json')
        middle=actual('to-Jan10')['checkpoint']
        for name,parent in [('direct',prefix),('to-Jan10',prefix),('Jan10-to-Jan12',middle)]:
            r=load(ROOT/'cases'/name/'input.json');a=actual(name);ex=a['execution']
            self.assertEqual(a['status'],'CONTINUED_ORIGINAL_ORDERS')
            self.assertEqual(r['root_job'],root)
            self.assertEqual(r['root_job']['continuation']['checkpoint'],old)
            self.assertEqual(r['checkpoint'],parent)
            self.assertEqual(a['integrity']['predecessor_checkpoint_id'],parent['checkpoint_id'])
            self.assertEqual(ex['opening_checkpoint_id'],old['checkpoint_id'])
            self.assertEqual(ex['order_states']['explicit-order'],old['state']['order_states']['explicit-order'])
            for key in ('decision_ids','decision_records','latest_decision_id','latest_common_account_id','origin_common_account_id',
                        'fact_sources','reassessment_attempts','reviewed_evidence_tokens','order_history','opening_unavailable_shares'):
                self.assertEqual(ex[key],prefix['execution_result'][key],(name,key))
            self.assertEqual(len(ex['decision_ids']),2);self.assertEqual(len(ex['reviewed_evidence_tokens']),12)
            self.assertEqual(a['checkpoint']['origin_ledger_input'],old['origin_ledger_input'])
            self.assertEqual(a['checkpoint']['state']['general_reserved_cash'],'100')
            self.assertTrue(all(a[k] is False for k in FLAGS))
            self.assertEqual(a['new_fill_ids_this_segment'],[]);self.assertEqual(a['tail_observations_processed'],0)
            if name!='to-Jan10':
                self.assertEqual(ex,whole);self.assertEqual(a['checkpoint'],whole_cp)
                self.assertTrue(all(load(ROOT/'actual'/name/'comparison.json').values()))
        self.assertEqual(actual('direct')['prefix_observation_trace'],load(ROOT/'control/one-shot-observation-trace.json'))
        self.assertEqual(len(actual('direct')['prefix_observation_trace']),3)
        self.assertEqual(middle['execution_result']['ledger']['daily'],[r for r in whole['ledger']['daily'] if r['date']<='2026-01-10'])
        save(ROOT/'test-evidence/chain-equivalence.json',dict(one_shot_equals_direct=True,one_shot_equals_two_segments=True,
            every_common_observation_equal=True,all_daily_rows_equal=True,root_parent_unchanged=True,
            root_parent_through=old['state']['through_at'],resume_predecessor_through=prefix['state']['through_at'],
            second_resume_predecessor_through=middle['state']['through_at'],tokens_unchanged=12,tail_decisions_added=0,tail_fills_added=0))

    def test_04_refusals_before_tail_input_and_saved_readback_invariance(self):
        summary=load(ROOT/'summary.json')
        self.assertTrue(summary['all_expected_status_reason_match']);self.assertTrue(summary['all_inputs_unchanged']);self.assertTrue(summary['all_saved_readbacks_equal'])
        self.assertTrue(all(load(ROOT/'actual/prefix-input-check.json').values()))
        for name,reason in load(ROOT/'negative-specifications.json').items():
            a=actual(name);expected=load(ROOT/'cases'/name/'expected.json')
            self.assertEqual(a['status'],expected['status']);self.assertEqual(a['status'],'REFUSED')
            self.assertEqual(a['refusal_reasons'],[reason]);self.assertFalse(a['tail_processing_started'])
            self.assertEqual(a['tail_observations_processed'],0);self.assertIsNone(a['execution']);self.assertIsNone(a['checkpoint'])
            self.assertTrue(all(a[k] is False for k in FLAGS))
        self.assertEqual(summary['product_module_changes'],0);self.assertEqual(summary['original_saved_resume_runs'],0)
        self.assertEqual(summary['new_quotes'],0);self.assertEqual(summary['new_calendar_rows'],0)


if __name__=='__main__':unittest.main()
