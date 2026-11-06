"""Focused contracts: read saved actuals, then only new boundary controls."""
import decimal
import hashlib
import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from capital_research.cash_action import evaluate
from capital_research.core import fingerprint
from capital_research.continuity import make_checkpoint
from capital_research.decimal_context_20261027.reproduce import context,snapshot
from .freeze import ROOT,PROJECT,REPO,load,save,info

FLAGS=('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized')


def request(name):return load(ROOT/'cases'/name/'input.json')
def actual(name):return load(ROOT/'after-final/actual'/name/'result.json')


class CashActionTests(unittest.TestCase):
    def test_01_frozen_evidence_old_sources_and_manual_original_book(self):
        for meta in load(ROOT/'frozen.json')['files']:
            self.assertEqual(info(REPO/meta['path']),meta)
        for meta in load(ROOT/'intake.json')['protected']:
            self.assertEqual(info(REPO/meta['path']),meta)
        # Independent arithmetic follows the original whole-unit ceiling rule,
        # not the saved engine output. The incorrect draft handcalc remains.
        corrected=load(ROOT/'preconditions/expected-fee-rounding.json')
        self.assertEqual(corrected['exit_net_receivable'],'995.000')
        self.assertEqual(load(ROOT/'preconditions/expected.json')['exit_tax'],'2.997')
        for name,shares,cash in [('holding','100','1000'),('exit-unsettled','0','1000'),('exit-settled','0','2075.000')]:
            cp=load(ROOT/'preconditions'/name/'checkpoint.json')
            self.assertEqual(cp['state']['origin_initial_capital'],'2180')
            self.assertEqual(cp['state']['general_reserved_cash'],'100')
            self.assertEqual(cp['state']['row']['shares']['A'],shares)
            self.assertEqual(cp['state']['row']['settled_cash'],cash)
        cp=load(ROOT/'preconditions/exit-unsettled/checkpoint.json')
        self.assertEqual(cp['state']['row']['cash_claims'][1]['amount'],'995.000')
        self.assertEqual(cp['state']['row']['share_receivables'][0]['shares'],'2')
        self.assertEqual(cp['state']['row']['shares']['C'],'2')
        later=load(ROOT/'preconditions/exit-settled/checkpoint.json')
        self.assertEqual(later['state']['row']['shares']['C'],'4')
        self.assertEqual(later['origin_ledger_input'],cp['origin_ledger_input'])
        self.assertEqual(later['state']['accepted_fills'],cp['state']['accepted_fills'])
        save(ROOT/'test-evidence/preservation.json',dict(old_protected_files=len(load(ROOT/'intake.json')['protected']),
            frozen_files_matched=True,original_opening_unchanged=True,old_price_volume_context_unchanged=True))

    def test_02_all_saved_cases_match_frozen_oracles_and_never_execute(self):
        summary=load(ROOT/'after-final/summary.json');self.assertTrue(summary['all_expected'])
        for name in load(ROOT/'case-index.json')['cases']:
            expected=load(ROOT/'cases'/name/'expected.json');result=actual(name);r=result['research']
            self.assertEqual(r['status'],expected['status'],name)
            if expected['reason']:self.assertIn(expected['reason'],r['reasons'])
            self.assertTrue(all(r[k] is False for k in FLAGS));self.assertIsNone(r['primary_pressure_id'])
            self.assertEqual(r['order_generation'],'NOT_PERFORMED');self.assertEqual(r['execution'],'NOT_PERFORMED')
            self.assertEqual(r['account_posting'],'NOT_PERFORMED')
            if r['status']!='CURRENTLY_FEASIBLE':self.assertEqual(r['research_recommendation']['candidate_ids'],[])
        for k in ('market_replay_calls','action_execution_calls','quantity_generation_calls'):self.assertEqual(summary[k],0)

    def test_03_cash_and_reentry_use_exact_current_account_latest_and_all_tokens(self):
        for name in ['original-cash-no-sale-A','exit-unsettled-first-B-small','exit-settled-first-B','reentry-independent-A']:
            result=actual(name);r=result['research'];d=r['core_decision']
            data=result['source_integrity_metadata']['derived_decision_input'];cp=request(name)['account_source']['checkpoint']
            self.assertEqual(r['status'],'CURRENTLY_FEASIBLE')
            self.assertEqual(data['account']['cash_claims'],cp['state']['row']['cash_claims'])
            self.assertEqual(data['account']['share_claims'],cp['state']['row']['share_receivables'])
            self.assertEqual(data['account']['reserved_cash'],'100')
            self.assertEqual(d['continuity']['origin_initial_capital'],'2180')
            self.assertEqual(d['continuity']['latest_predecessor_id'],cp['execution_result']['latest_decision_id'])
            self.assertEqual(r['account_binding']['accepted_fill_ids'],[f['id'] for f in cp['state']['accepted_fills']])
            self.assertEqual(r['account_binding']['closed_order_states'],cp['state']['order_states'])
            self.assertTrue(set(cp['state']['reviewed_evidence_tokens'])<=set(d['reviewed_evidence_tokens']))
            # No intent posting, new costs only estimates, other holdings untouched.
            target=r['intent']['core_evaluation']['targets'];code=r['intent']['external_action']['code']
            self.assertEqual(target['C'],data['account']['holdings']['C']['shares'])
            for c in target:
                if c!=code:self.assertEqual(target[c],data['account']['holdings'][c]['shares'])
        r=actual('original-cash-no-sale-A')['research'];self.assertEqual(r['intent']['plan']['targets']['A'],'100')
        self.assertEqual(r['intent']['core_evaluation']['purchase_payable_estimate'],'401.4')
        self.assertEqual(r['intent']['core_evaluation']['sale_receivable_estimate'],'0')
        old=actual('exit-settled-first-B')['research']
        self.assertEqual(old['intent']['plan']['family'],'E')
        self.assertEqual(old['core_decision']['layer2']['B']['capital_eligibility']['review']['evidence_ids'],['B-event'])
        self.assertEqual(old['core_decision']['new_evidence_tokens'],[])
        fresh=actual('reentry-independent-A')['research'];self.assertEqual(fresh['intent']['plan']['family'],'C')
        self.assertTrue(fresh['core_decision']['new_evidence_tokens'])

    def test_04_outer_gate_and_budget_rejections_cannot_become_recommendations(self):
        refused=['reentry-old-trigger','reentry-shared-bar','cross-stock-trigger','false-first-after-exit',
            'unknown-phase','unknown-capital-review','revoked-evidence','joint-risk','liquidity',
            'receivable-not-buying-power','reserve-not-spendable','fees-paid-from-original-cash']
        for name in refused:
            r=actual(name)['research'];self.assertEqual(r['status'],'REJECTED',name)
            self.assertFalse(r['intent']['feasible_for_research']);self.assertEqual(r['research_recommendation']['candidate_ids'],[])
        # Unmodified core's snapshot feasibility alone cannot bypass first-entry history.
        r=actual('false-first-after-exit')['research'];self.assertTrue(r['intent']['core_evaluation']['feasible'])
        self.assertIn('FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY',r['intent']['batch_gate_reasons'])
        self.assertEqual(actual('settled-larger-B')['research']['status'],'CURRENTLY_FEASIBLE')

    def test_05_future_prefix_and_complete_decimal_context_isolation(self):
        r=request('opening-cash-first-B');base=actual('opening-cash-first-B');future=actual('future-revocation-prefix')
        self.assertEqual(base['research'],future['research'])
        self.assertNotEqual(base['source_integrity_metadata']['full_request_id'],future['source_integrity_metadata']['full_request_id'])
        preset=load(PROJECT/'capital_research/quantity_context_20261027/test-controls.json')['preset']
        controls=[None,preset];records=[];default=snapshot(decimal.DefaultContext)
        with patch('capital_research.execution.simulate',side_effect=AssertionError('NO_EXECUTION')), \
             patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_GENERATION')):
            for spec in controls:
                with decimal.localcontext(context(spec) if spec else decimal.Context(prec=28)) as ctx:
                    before=snapshot(ctx);original=deepcopy(r);result=evaluate(r);after=snapshot(ctx)
                self.assertEqual(result,base);self.assertEqual(before,after);self.assertEqual(original,r)
                records.append(dict(context='hostile' if spec else 'normal',equal_full_actual=True,caller_unchanged=True,input_unchanged=True))
        self.assertEqual(default,snapshot(decimal.DefaultContext))
        save(ROOT/'test-evidence/prefix-context.json',dict(records=records,future_research_equal=True,full_integrity_separate=True,default_context_unchanged=True))

    def test_06_corrupt_history_and_not_yet_known_close_fail_before_intent(self):
        r=request('exit-unsettled-first-B-small');cases=[]
        for label in ['dropped-token','changed-opening']:
            x=deepcopy(r);cp=x['account_source']['checkpoint']
            if label=='dropped-token':cp['state']['reviewed_evidence_tokens'].pop()
            else:cp['origin_ledger_input']['opening']['cash']='9999'
            save(ROOT/'test-evidence'/label/'input.json',x)
            save(ROOT/'test-evidence'/label/'expected.json',dict(status='INPUT_ERROR',no_recommendation=True))
            result=evaluate(x);save(ROOT/'test-evidence'/label/'actual.json',result)
            self.assertEqual(result['research']['status'],'INPUT_ERROR');self.assertIsNone(result['research']['intent']);cases.append(label)
        cp=deepcopy(r['account_source']['checkpoint']);execution=cp['execution_result']
        execution['ledger_close_proof']['closes']['2026-01-08']['available_at']='2026-01-08T18:00:00+08:00'
        execution['result_id']=fingerprint({k:v for k,v in execution.items() if k!='result_id'})
        later=make_checkpoint(cp['origin_ledger_input'],execution,through_at=cp['state']['through_at'])
        x=deepcopy(r);x['account_source'].update(checkpoint=later,expected_checkpoint_id=later['checkpoint_id'])
        save(ROOT/'test-evidence/close-unavailable/input.json',x)
        save(ROOT/'test-evidence/close-unavailable/expected.json',dict(status='INPUT_ERROR',reason='LEDGER_CLOSE_NOT_YET_AVAILABLE'))
        result=evaluate(x);save(ROOT/'test-evidence/close-unavailable/actual.json',result)
        self.assertEqual(result['research']['reasons'],['LEDGER_CLOSE_NOT_YET_AVAILABLE'])

    def test_07_fresh_call_is_pure_and_does_not_enter_execution_engines(self):
        r=request('opening-cash-first-B');before=deepcopy(r)
        # Modules and fixture bytes loaded before blocking IO.
        import capital_research.quantity_replay
        import rotation_research.action_ledger
        import capital_research.continuity
        with patch('builtins.open',side_effect=AssertionError('NO_FILE_IO')), \
             patch('socket.socket',side_effect=AssertionError('NO_NETWORK')), \
             patch('capital_research.execution.simulate',side_effect=AssertionError('NO_EXECUTION')), \
             patch('capital_research.quantity_replay.replay_sequence',side_effect=AssertionError('NO_REPLAY')), \
             patch('capital_research.quantity_candidates.generate',side_effect=AssertionError('NO_ENUMERATION')), \
             patch('capital_research.continuity.replay',side_effect=AssertionError('NO_OPENING_LEDGER_CALL')):
            result=evaluate(r)
        self.assertEqual(result,actual('opening-cash-first-B'));self.assertEqual(r,before)
        save(ROOT/'test-evidence/pure.json',dict(opening_evaluate_calls=1,execution_calls=0,quantity_generation_calls=0,
            market_replay_calls=0,network_calls=0,file_io_calls=0,input_unchanged=True,
            checkpoint_resume_ledger_verification='EXISTING_ENGINE_CALLS_REQUIRED_NOT_CLAIMED_ZERO'))


if __name__=='__main__':unittest.main(verbosity=2)
