"""Finite new integration evidence; do not replay any historical test suite."""
import decimal
import unittest
from copy import deepcopy
from unittest.mock import patch

from capital_research.cash_action_execution import execute
from capital_research.cash_action import evaluate
from capital_research.core import fingerprint
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .freeze import ROOT,PROJECT,REPO,load,save,info

FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')


def request(name):return load(ROOT/'cases'/name/'input.json')
def actual(name):return load(ROOT/'actual'/name/'result.json')
def expected(name):
    e=load(ROOT/'cases'/name/'expected.json')
    if name=='partial-7-active-13':e.update(load(ROOT/'diagnostics/pretest-cash-role-correction.json')['corrected_expected'])
    return e


class ExecutionTests(unittest.TestCase):
    def test_01_frozen_inputs_original_checked_receipts_and_old_source_unchanged(self):
        for meta in load(ROOT/'frozen.json')['files']+load(ROOT/'intake.json')['protected']:
            self.assertEqual(info(REPO/meta['path']),meta)
        for meta in load(ROOT/'source-versions.json'):
            self.assertEqual(info(REPO/meta['path']),meta)
        # Original mistaken handcalc kept, not edited or hidden.
        self.assertEqual(load(ROOT/'cases/partial-7-active-13/expected.json')['final_cash'],'858.860')
        save(ROOT/'test-evidence/preservation.json',dict(all_frozen_bytes_matched=True,
            all_selected_original_sources_matched=True,old_suites_rerun=0,market_replay_calls=0))

    def test_02_all_saved_results_match_oracles_and_no_execution_on_blocked_receipts(self):
        self.assertTrue(load(ROOT/'summary.json')['all_status_reasons_matched'])
        for name in load(ROOT/'case-index.json')['cases']:
            e=expected(name);r=actual(name)['run']
            self.assertEqual(r['status'],e['status'],name)
            if e['reason']:self.assertIn(e['reason'],r['reasons'])
            self.assertTrue(all(r[k] is False for k in FLAGS));self.assertIsNone(r['primary_pressure_id']);self.assertIsNone(r['ranking'])
            if 'execution_calls' in e:
                self.assertEqual(r['execution_calls'],e['execution_calls']);self.assertIsNone(r['execution']);continue
            self.assertEqual(r['execution_calls'],1)
            cp=r['checkpoint'];ex=r['execution'];row=cp['state']['row'];new=[f for f in ex['fills'] if f['id'] in ex['new_fill_ids']]
            self.assertEqual(sum(int(f['shares']) for f in new),int(e['new_shares']),name)
            self.assertEqual(len(new),e['new_fill_count'])
            self.assertEqual(decimal.Decimal(row['settled_cash']),decimal.Decimal(e['final_cash']))
            self.assertEqual(cp['state']['origin_initial_capital'],e['origin_capital'])
            self.assertEqual(cp['state']['general_reserved_cash'],'100')
            for k in ('purchase_payable','available_cash_strict'):
                if k in e:self.assertEqual(decimal.Decimal(row[k]),decimal.Decimal(e[k]))
            if 'final_A'in e:self.assertEqual(row['shares']['A'],e['final_A'])
            if 'remaining'in e:
                state=ex['order_states']['explicit-order'];self.assertEqual(state['remaining'],e['remaining']);self.assertEqual(state['status'],e['order_status'])
                self.assertEqual(state['reserved_cash'],e['reserved_cash'])
            if 'same_numeric_as'in e:
                other=actual(e['same_numeric_as']);self.assertEqual(r['numeric_result'],other['run']['numeric_result'])
                self.assertNotEqual(actual(name)['source_integrity_metadata']['origin_ledger_input_id'],other['source_integrity_metadata']['origin_ledger_input_id'])

    def test_03_original_book_fills_rights_latest_and_every_token_connect(self):
        for name in ['keep-A-buy-B20','exited-A-buy-B20','new-independent-A-reentry','hold-receivables-to-settlement']:
            src=request(name);checked=src['checked_action']['research'];r=actual(name)['run'];e=r['execution'];cp=r['checkpoint']
            old=src['action_input']['account_source']['checkpoint'];prior=old['execution_result']
            self.assertEqual(cp['origin_ledger_input'],old['origin_ledger_input'])
            self.assertEqual(e['fills'][:len(old['state']['accepted_fills'])],old['state']['accepted_fills'])
            self.assertEqual(e['decision_ids'][:-1],prior['decision_ids'])
            self.assertEqual(e['decision_ids'][-1],checked['core_decision']['decision_id'])
            self.assertEqual(e['decision_records'][e['decision_id']],checked['core_decision'])
            self.assertEqual(e['latest_common_account_id'],checked['core_decision']['common_account_id'])
            self.assertEqual(cp['state']['latest_decision_id'],e['latest_decision_id'])
            self.assertTrue(set(prior['reviewed_evidence_tokens'])<=set(e['reviewed_evidence_tokens']))
            self.assertTrue(set(checked['core_decision']['reviewed_evidence_tokens'])<=set(cp['state']['reviewed_evidence_tokens']))
            for key in prior['fact_sources']:self.assertEqual(e['fact_sources'][key],prior['fact_sources'][key])
            self.assertEqual(e['reassessment_attempts'],prior['reassessment_attempts'])
            for key in prior['order_states']:self.assertEqual(e['order_states'][key],prior['order_states'][key])
            self.assertEqual(r['binding']['checked_action_id'],fingerprint(src['checked_action']))
        # Independently check account state at each meaningful date, not only its endpoint.
        rows={row['date']:row for row in actual('exited-A-buy-B20')['run']['execution']['ledger']['daily']}
        self.assertEqual(decimal.Decimal(rows['2026-01-08']['settled_cash']),decimal.Decimal('1000'))
        self.assertEqual(decimal.Decimal(rows['2026-01-08']['cash_receivable']),decimal.Decimal('1075'))
        self.assertEqual(decimal.Decimal(rows['2026-01-09']['settled_cash']),decimal.Decimal('1000'))
        self.assertEqual(decimal.Decimal(rows['2026-01-09']['purchase_payable']),decimal.Decimal('401.4'))
        self.assertEqual(decimal.Decimal(rows['2026-01-09']['available_cash_strict']),decimal.Decimal('598.6'))
        self.assertEqual(decimal.Decimal(rows['2026-01-12']['settled_cash']),decimal.Decimal('1673.6'))
        self.assertEqual(rows['2026-01-09']['shares']['C'],'2');self.assertEqual(rows['2026-01-09']['share_receivables'][0]['shares'],'2')
        self.assertEqual(rows['2026-01-12']['shares']['C'],'4');self.assertEqual(rows['2026-01-12']['share_receivables'],[])
        self.assertEqual(rows['2026-01-12']['cash_claims'],[]);self.assertEqual(decimal.Decimal(rows['2026-01-12']['purchase_payable']),0)
        for day,row in rows.items():
            # Verification identity only; no posting or second ledger.
            assets=sum(decimal.Decimal(n)*decimal.Decimal(row['marks'][c]['value']) for c,n in row['shares'].items())
            rights=sum(decimal.Decimal(x['shares'])*decimal.Decimal(row['marks'][x['code']]['value']) for x in row['share_receivables'])
            self.assertEqual(decimal.Decimal(row['settled_cash'])+decimal.Decimal(row['cash_receivable'])-decimal.Decimal(row['purchase_payable'])+assets+rights,decimal.Decimal(row['net_accrual_equity']),day)
        save(ROOT/'test-evidence/continuous-book.json',dict(origin_capital='2180',all_prefix_balances_checked=True,
            cash_receivable_before_settlement='1075',buy_payable='401.4',final_settled_cash='1673.6',
            old_fill_order_history_and_all_tokens_preserved=True,no_second_account=True))

    def test_04_partial_unfilled_expiry_cancellation_and_reservations_are_distinct(self):
        active=actual('partial-7-active-13')['run'];cancel=actual('partial-7-cancelled-13')['run'];expiry=actual('partial-7-expired-13')['run']
        self.assertEqual(active['checkpoint']['state']['row']['purchase_payable'],'141.140')
        self.assertEqual(active['checkpoint']['state']['row']['settled_cash'],'1000')
        self.assertEqual(active['checkpoint']['state']['row']['available_cash_strict'],'858.860')
        self.assertEqual(len(active['checkpoint']['state']['unfilled_orders']),1)
        self.assertEqual(active['execution']['order_states']['explicit-order']['reserved_cash'],'261.65039')
        self.assertEqual(cancel['execution']['new_fill_ids'],active['execution']['new_fill_ids'])
        self.assertEqual(cancel['checkpoint']['state']['unfilled_orders'],[]);self.assertEqual(expiry['checkpoint']['state']['unfilled_orders'],[])
        events=[e for e in cancel['execution']['execution_events'] if e['status']=='CANCELLED_EVIDENCE']
        self.assertEqual(len(events),1);self.assertEqual(events[0]['at'],'2026-01-09T12:00:00+08:00')
        self.assertEqual(events[0]['observed_at'],'2026-01-09T13:00:00+08:00')
        for name in ['limit-up-unfilled','zero-capacity-unfilled','no-implicit-order']:
            r=actual(name)['run'];self.assertEqual(r['execution']['new_fill_ids'],[])
            self.assertEqual(r['checkpoint']['state']['general_reserved_cash'],'100')
        self.assertEqual(actual('no-implicit-order')['run']['execution']['orders'],[])

    def test_05_outer_approval_cannot_be_forged_and_never_enters_simulate(self):
        names=['outer-rejected-core-feasible','forged-outer-approval','wrong-full-result-id','different-action-input',
            'tampered-metadata-reserve','split-order-total-exceeds-20','reset-original-capital','changed-close-proof',
            'sell-cannot-bypass-cash-intent','hold-cannot-submit-buy']
        with patch('capital_research.cash_action_execution.simulate',side_effect=AssertionError('MUST_STOP_BEFORE_EXECUTION')):
            for name in names:
                r=request(name);before=deepcopy(r);result=execute(r)
                self.assertEqual(result,actual(name));self.assertEqual(r,before)
        self.assertTrue(request('outer-rejected-core-feasible')['checked_action']['research']['intent']['core_evaluation']['feasible'])
        save(ROOT/'test-evidence/pre-execution-gates.json',dict(cases=names,simulate_calls=0,
            core_snapshot_feasibility_does_not_bypass_outer_gate=True,forged_full_hash_does_not_certify_result=True))

    def test_06_new_closed_checkpoint_reuses_existing_hold_gate_and_active_stays_refused(self):
        for name in ['exited-A-buy-B20','partial-7-active-13']:
            cp=actual(name)['run']['checkpoint'];r=deepcopy(request('hold-receivables-to-settlement')['action_input'])
            t=r['decision_template'];t['data_cutoff']=cp['state']['through_at'];t['decision_at']=cp['state']['through_at'][:10]+'T17:00:00+08:00'
            for c,a in t['assets'].items():
                a['marks']=[dict(a['marks'][0],price=cp['state']['row']['marks'][c]['value'],occurred_at=t['data_cutoff'],available_at=t['data_cutoff'])]
                a['capital_eligibility'].update(assessed_at=t['decision_at'],available_at=t['decision_at'],data_cutoff=t['data_cutoff'])
            r['policy']['available_at']=t['decision_at'];r['account_source'].update(checkpoint=deepcopy(cp),expected_checkpoint_id=cp['checkpoint_id'],expected_latest_decision_id=cp['execution_result']['latest_decision_id'])
            save(ROOT/'test-evidence/next-hold'/name/'input.json',r)
            save(ROOT/'test-evidence/next-hold'/name/'expected.json',dict(status='NOT_IMPLEMENTED' if 'active' in name else 'CURRENTLY_FEASIBLE'))
            result=evaluate(r);save(ROOT/'test-evidence/next-hold'/name/'actual.json',result)
            if 'active'in name:
                self.assertEqual(result['research']['status'],'NOT_IMPLEMENTED');self.assertIn('ACTIVE_ORDER_CONTINUATION_NOT_IMPLEMENTED',result['research']['reasons'])
            else:
                self.assertEqual(result['research']['status'],'CURRENTLY_FEASIBLE')
                d=result['source_integrity_metadata']['derived_decision_input'];self.assertEqual(d['account']['settled_cash'],'1673.600')
                self.assertEqual(d['account']['reserved_cash'],'100')
                self.assertEqual(result['research']['core_decision']['continuity']['origin_initial_capital'],'2180')
                self.assertTrue(set(cp['state']['reviewed_evidence_tokens'])<=set(result['research']['core_decision']['reviewed_evidence_tokens']))

    def test_07_context_input_and_no_io_generation_or_market_replay(self):
        r=request('opening-B20');base=actual('opening-B20');original=deepcopy(r)
        preset=load(PROJECT/'capital_research/quantity_context_20261027/test-controls.json')['preset']
        import capital_research.quantity_replay
        from capital_research import quantity_candidates
        default=snapshot(decimal.DefaultContext);rows=[]
        with patch('builtins.open',side_effect=AssertionError('NO_FILE_IO')), \
             patch('socket.socket',side_effect=AssertionError('NO_NETWORK')), \
             patch('capital_research.quantity_replay.replay_sequence',side_effect=AssertionError('NO_QUANTITY_REPLAY')), \
             patch.object(quantity_candidates,'generate',side_effect=AssertionError('NO_QUANTITY_GENERATION')):
            for label,spec in [('normal',None),('hostile',preset)]:
                with decimal.localcontext(context(spec) if spec else decimal.Context(prec=28)) as ctx:
                    before=snapshot(ctx);result=execute(r);after=snapshot(ctx)
                self.assertEqual(result,base);self.assertEqual(before,after);self.assertEqual(r,original)
                rows.append(dict(context=label,full_actual_equal=True,caller_input_unchanged=True))
        self.assertEqual(default,snapshot(decimal.DefaultContext))
        save(ROOT/'test-evidence/pure-context.json',dict(controls=rows,default_context_unchanged=True,io_calls=0,network_calls=0,
            quantity_generation_calls=0,market_replay_calls=0,existing_synthetic_execution_calls=2,
            existing_ledger_verification_calls='REQUIRED_NOT_CLAIMED_ZERO'))


if __name__=='__main__':unittest.main(verbosity=2)
