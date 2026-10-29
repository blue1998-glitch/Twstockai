"""Targeted assertions over new saved evaluations plus required pure-READ controls."""
from copy import deepcopy
import contextlib
import decimal
from fractions import Fraction
import io
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch
from .freeze import ROOT,PROJECT,REPO,load,save,info
from capital_research.lifecycle import FLAGS,_fp

def request(name):return load(ROOT/'cases'/name/'input.json')
def actual(name):return load(ROOT/'final-corrected'/name/'actual.json')


class SavedActionMetricsTests(unittest.TestCase):
    def test_01_frozen_inputs_sources_and_all_saved_statuses(self):
        intake=load(ROOT/'intake.json')
        for m in load(ROOT/'frozen.json')['files']+intake['protected']+intake['source_originals']+load(ROOT/'final-corrected/source-versions.json')['files']:
            self.assertEqual(info(REPO/m['path']),m)
        for pair in intake['changing_sources']:self.assertEqual(info(REPO/pair['archived']['path']),pair['archived'])
        summary=load(ROOT/'final-corrected/summary.json')
        self.assertTrue(summary['all_statuses_matched']);self.assertTrue(summary['all_inputs_unchanged']);self.assertTrue(summary['all_readbacks_equal'])
        for name in load(ROOT/'case-index.json')['cases']:
            a=actual(name);e=load(ROOT/'cases'/name/'expected.json')
            self.assertEqual(a['status'],e['status'],name)
            self.assertTrue(all(a[k] is False for k in FLAGS));self.assertIsNone(a['primary_pressure_id']);self.assertIsNone(a['ranking'])
            self.assertIsNone(a['selected_strategy']);self.assertFalse(a['strategy_validated'])
            if a['status']=='REFUSED':self.assertIsNone(a['statistics']);self.assertTrue(a['reasons'])
        self.assertEqual(load(ROOT/'before/actual.json')['status'],'REFUSED')
        save(ROOT/'validation-corrected/test-evidence/preservation.json',dict(frozen_and_originals_matched=True,only_source_adapter_and_metrics_extraction_changed=True))

    def test_02_independent_fraction_growth_drawdown_and_recovery_handcheck(self):
        rows=[]
        for name in ('reduce-B3','exit-B7','split-exit','continued-partial','equivalent-utc'):
            e=load(ROOT/'cases'/name/'expected.json');a=actual(name);s=a['statistics']
            ratio=Fraction(e['numerator'])/Fraction(e['denominator'])
            self.assertLess(abs(Fraction(s['period_accrual_growth'])-ratio),Fraction(1,10**45))
            self.assertLess(abs(Fraction(s['maximum_drawdown'])-ratio),Fraction(1,10**45))
            self.assertEqual(Fraction(s['curve'][-1]['equity']),Fraction(e['last_equity']))
            self.assertEqual(s['maximum_drawdown_duration_calendar_days'],7);self.assertEqual(s['ongoing_underwater_calendar_days'],7)
            self.assertTrue(s['recovery_censored']);self.assertIsNone(s['maximum_drawdown_episode']['recovery_date'])
            self.assertEqual(s['maximum_drawdown_episode']['peak_date'],'2026-01-05')
            self.assertEqual(s['maximum_drawdown_episode']['trough_date'],'2026-01-09')
            self.assertEqual(len(s['curve']),e['rows']);self.assertEqual(a['costs']['recorded_fill_fee_tax'],e['fees'])
            rows.append(dict(name=name,manual_fraction=str(ratio),equity=e['last_equity'],recovery_censored=True,calendar_days=7))
        self.assertEqual(actual('exit-B7')['statistics'],actual('equivalent-utc')['statistics'])
        save(ROOT/'validation-corrected/test-evidence/manual-check.json',dict(all_handchecks_matched=True,cases=rows,accounting_replayed=False))

    def test_03_original_capital_full_rights_latest_tokens_and_curve_used_once(self):
        for name in ('reduce-B3','exit-B7','split-exit','continued-partial','v01-hold','v01-independent-B20'):
            q=request(name);bundle=q['saved_result'];r=bundle['action_result']['run'];cp=(bundle['continuation']['result']['checkpoint'] if bundle['continuation'] else r['checkpoint'])
            e=cp['execution_result'];a=actual(name)
            self.assertEqual(a['initial_capital'],'1180');self.assertEqual(a['account']['general_reserved_cash'],'100')
            self.assertEqual(a['account']['saved_row'],cp['state']['row'])
            self.assertEqual(a['account']['reviewed_evidence_tokens'],e['reviewed_evidence_tokens'])
            self.assertEqual(a['account']['latest_decision_id'],e['latest_decision_id'])
            self.assertEqual(a['source']['document_id'],_fp(bundle));self.assertEqual(a['source']['checkpoint_id'],cp['checkpoint_id'])
            self.assertEqual(a['source']['rows_used_once'],len(e['ledger']['daily']))
            self.assertEqual([p['equity'] for p in a['statistics']['curve']],[p['net_accrual_equity'] for p in e['ledger']['daily']])
            for dest,source in [('terminal_net_equity','end_net_equity'),('terminal_net_growth','scenario_net_return')]:
                self.assertEqual(a[dest],e['ledger'][source])
            self.assertEqual(a['costs']['terminal_estimated_exit_cost'],e['ledger']['terminal_estimated_exit_cost'])
            self.assertEqual(a['source']['snapshot_count'],3 if bundle['continuation'] else 2)
        save(ROOT/'validation-corrected/test-evidence/continuous-book.json',dict(initial_capital='1180',reserve='100',full_saved_rights_and_latest_tokens_preserved=True,
            cumulative_curve_used_once=True,terminal_exit_cost_separate=True))

    def test_04_refusal_boundaries_are_saved_and_no_partial_metrics(self):
        guards={'early':'CLOSE_NOT_YET_AVAILABLE','partial-prefix':'LEDGER_RETURN_REFUSED','changed-prefix':'LEDGER_PREFIX_CHANGED',
            'missing-day':'INCOMPLETE_CALENDAR_CURVE','missing-mark':'UNKNOWN_HELD_ASSET_MARK','future-mark':'FUTURE_OR_OUTSIDE_MARK',
            'unknown-rights':'UNKNOWN_CASH_CLAIMS','external-flow':'EXTERNAL_FLOW_NOT_IMPLEMENTED','missing-token':'REVIEWED_TOKEN_HISTORY_CONFLICT',
            'wrong-reserve':'GENERAL_RESERVE_CONFLICT','lost-fact-history':'SAVED_FACT_HISTORY_CONFLICT'}
        for name,guard in guards.items():self.assertEqual(actual(name)['reasons'][0]['reason'],guard)
        for name in ('missing-request','cross-result','changed-origin','wrong-latest-request','missing-resume-history','wrong-resume-root','stopped-action','real-relabel','qualification-upgrade'):
            a=actual(name);self.assertEqual(a['status'],'REFUSED');self.assertIsNone(a['source']);self.assertIsNone(a['statistics'])

    def test_05_self_review_resume_cannot_replace_original_close_proof(self):
        p=ROOT/'diagnostics/resume-close-binding';expected=load(p/'expected.json')
        self.assertEqual(load(p/'before-actual.json')['status'],'EVALUATED')
        a=load(p/'corrected-actual.json');self.assertEqual(a['status'],expected['status']);self.assertEqual(a['reasons'][0]['reason'],expected['reason'])
        self.assertIsNone(a['statistics']);self.assertEqual(info(PROJECT/'capital_research/action_account_metrics.py'),load(p/'corrected-source.json'))
        self.assertEqual(actual('continued-partial')['status'],'EVALUATED')
        p=ROOT/'diagnostics/derived-source-binding';e=load(p/'expected.json');a=load(p/'corrected-actual.json')
        self.assertEqual(load(p/'before-actual.json')['status'],'EVALUATED')
        self.assertEqual(a['status'],e['status']);self.assertEqual(a['reasons'][0]['reason'],e['reason'])
        self.assertIsNone(a['statistics'])

    def test_06_hostile_contexts_caller_default_input_and_no_io(self):
        from capital_research.action_account_metrics import evaluate_saved
        from capital_research.decimal_context_20261027.reproduce import context,snapshot
        specs=[dict(prec=3,rounding='ROUND_DOWN',Emin=-2,Emax=2,capitals=0,clamp=1,traps=['Inexact','Overflow','Clamped'],flags=[]),
            dict(prec=7,rounding='ROUND_UP',Emin=-9,Emax=9,capitals=1,clamp=0,traps=['Rounded'],flags=['Inexact'])]
        save(ROOT/'validation-corrected/controls/context/specifications.json',specs)
        q=request('continued-partial');old=deepcopy(q);default=snapshot(decimal.DefaultContext);rows=[]
        for spec in specs:
            with decimal.localcontext(context(spec)) as caller:
                before=snapshot(caller)
                with patch('builtins.open',side_effect=AssertionError('NO_IO')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):
                    a=evaluate_saved(q)
                row=dict(equal_saved_final=a==actual('continued-partial'),caller_unchanged=snapshot(caller)==before,
                    default_unchanged=snapshot(decimal.DefaultContext)==default,input_unchanged=q==old)
                self.assertTrue(all(row.values()));rows.append(row)
        save(ROOT/'validation-corrected/controls/context/actual.json',rows)

    def test_07_old_quantity_evaluation_exact_and_default_cli_routing(self):
        from capital_research.account_metrics import evaluate_saved,INPUT
        from capital_research import account_metrics_read
        spec=load(ROOT/'legacy.json');q=dict(schema=INPUT,synthetic=True,evaluation_at=spec['evaluation_at'],saved_result=load(PROJECT/spec['saved_source']['path']))
        original=deepcopy(q);a=evaluate_saved(q);expected=load(PROJECT/spec['baseline_expected']['path'])
        self.assertEqual(a,expected);self.assertEqual(q,original);save(ROOT/'validation-corrected/controls/legacy/actual.json',a)
        output=io.StringIO()
        with patch.object(sys,'argv',['account_metrics_read','--source',str(PROJECT/spec['saved_source']['path']),'--evaluation-at',q['evaluation_at'],'--format','json']), \
             patch.object(account_metrics_read,'evaluate_saved',return_value=expected) as api,contextlib.redirect_stdout(output):
            self.assertEqual(account_metrics_read.main(),0)
        self.assertEqual(api.call_args.args[0],q);self.assertEqual(json.loads(output.getvalue())['evaluation'],expected)
        save(ROOT/'validation-corrected/controls/legacy/summary.json',dict(full_old_evaluation_equal=True,default_cli_quantity_route_preserved=True))

    def test_08_fresh_process_forbids_producers_and_explicit_cli_source(self):
        q=request('exit-B7')
        code='''import sys,json,importlib.abc
from pathlib import Path
from unittest.mock import patch
request=json.loads(Path(sys.argv[1]).read_text())
bad=('capital_research.core','capital_research.execution','capital_research.execution_continuation','capital_research.continuity','capital_research.cash_action','capital_research.cash_action_execution','capital_research.quantity_replay','capital_research.quantity_candidates','rotation_research')
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if any(fullname==x or fullname.startswith(x+'.') for x in bad):raise AssertionError('FORBIDDEN_PRODUCER_IMPORT:'+fullname)
sys.meta_path.insert(0,Guard())
from capital_research.action_account_metrics import evaluate_saved
with patch('builtins.open',side_effect=AssertionError('NO_IO')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):
 result=evaluate_saved(request)
print(json.dumps(result,ensure_ascii=False))
'''
        save(ROOT/'validation-corrected/controls/fresh/specification.json',dict(request=str((ROOT/'cases/exit-B7/input.json').relative_to(REPO)),
            forbidden_producers=True,expected_status='EVALUATED',no_io_or_network=True))
        p=subprocess.run([sys.executable,'-c',code,str(ROOT/'cases/exit-B7/input.json')],cwd=PROJECT,capture_output=True,text=True)
        save(ROOT/'validation-corrected/controls/fresh/actual.json',dict(returncode=p.returncode,stderr=p.stderr,stdout=p.stdout))
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),actual('exit-B7'))
        source=ROOT/'validation-corrected/controls/cli/source.json';save(source,q['saved_result'])
        p=subprocess.run([sys.executable,'-m','capital_research.account_metrics_read','--source-kind','action','--source',str(source),
            '--evaluation-at',q['evaluation_at'],'--format','json'],cwd=PROJECT,capture_output=True,text=True)
        save(ROOT/'validation-corrected/controls/cli/actual.json',dict(returncode=p.returncode,stderr=p.stderr,stdout=p.stdout))
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)['evaluation'],actual('exit-B7'))

if __name__=='__main__':unittest.main()
