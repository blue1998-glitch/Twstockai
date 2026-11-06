"""Six unique targeted methods; saved probes are evidence, not extra tests."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from capital_research.lifecycle import _fp
from .prepare import ROOT,PROJECT,load,save,info
from .reproduce import check_frozen,cases,equal_expected,probe


def child(*args):
    done=subprocess.run([sys.executable,'-B','-m','rotation_research.ledger_context_20261027.guard',*args],
        cwd=PROJECT,capture_output=True,text=True,check=True)
    assert not done.stderr,done.stderr
    return json.loads(done.stdout)


class LedgerContext(unittest.TestCase):
    def test_01_frozen_reproduction_and_complete_results(self):
        check_frozen();before=load(ROOT/'before/summary.json');after=load(ROOT/'after/summary.json')
        self.assertEqual(len(before['api']),13);self.assertEqual(len(after['api']),13)
        errors={(x['case'],x['context']):x['error']['type'] for x in before['api'] if x['error']}
        self.assertEqual(errors,{('cash-net-withholding','narrow-exponents'):'Overflow',
            ('stock-delivery','preset'):'Clamped',('capital-reduction','preset'):'Clamped'})
        for row in after['api']:
            item=next(x for x in cases() if x['name']==row['case']);r=load(ROOT/row['path'])
            self.assertIsNone(r['error']);self.assertTrue(equal_expected(r['actual'],item))
            self.assertTrue(r['input_unchanged']);self.assertTrue(r['caller_context_unchanged']);self.assertTrue(r['default_context_unchanged'])
            self.assertEqual(r['calls'],dict(replay=1,qualify=1,ledger_kernel=int(item['kind']=='EXACT_SAVED_SYNTHETIC'),save=0,simulate=0,generate=0,replay_sequence=0))

    def test_02_cash_share_rights_and_refusals(self):
        for item in cases():
            r=load(ROOT/'after'/item['name']/'normal/actual.json')['actual']
            self.assertFalse(r['policy_authorized']);self.assertFalse(r['historical_signal_eligible'])
            self.assertIsNone(r['actual_realized_investor_return']);self.assertIsNone(r['total_net_return']);self.assertIsNone(r['primary_pressure_id'])
            self.assertEqual(r['source_qualification'],item['input']['qualification'])
            if item['kind']=='SYNTHETIC_REFUSAL':
                self.assertEqual(r['daily'],[]);self.assertEqual(r['journal'],[]);continue
            self.assertEqual(r,item['expected'])  # Every daily balance/right/journal field, not just terminal NAV.
            if item['name']=='cash-net-withholding':
                self.assertEqual((r['initial_equity'],r['end_net_equity'],r['scenario_net_return']),('1000','980.0','-0.02'))
                self.assertEqual([(x['date'],x['type']) for x in r['journal']],
                    [('2026-01-06','DIVIDEND_RECEIVABLE'),('2026-01-09','CASH_RECEIVED')])
                self.assertEqual(r['journal'][0]['net'],'80.0');self.assertEqual(r['journal'][1]['amount'],'80.0')

    def test_03_fresh_context_and_pure_api(self):
        actual=child('pure');save(ROOT/'after/guard/pure.json',actual)
        self.assertTrue(actual['equal_original']);self.assertTrue(actual['input_unchanged'])
        self.assertTrue(actual['caller_context_unchanged']);self.assertTrue(actual['default_context_unchanged'])
        self.assertEqual(actual['forbidden_effects'],[])
        self.assertEqual([x['function'] for x in actual['qualifier_context']],['qualify','_replay'])
        for row in actual['qualifier_context']:
            c=row['context'];self.assertEqual((c['prec'],c['rounding'],c['Emin'],c['Emax'],c['clamp'],c['capitals']),
                (50,'ROUND_HALF_EVEN',-999999,999999,0,1))
            self.assertEqual({k for k,v in c['traps'].items() if v},{'InvalidOperation','DivisionByZero','Overflow'})

    def test_04_explicit_run_and_immutable_read(self):
        bad=load(ROOT/'before/cli/preset/actual.json')
        self.assertEqual(bad['error']['type'],'Clamped');self.assertFalse(bad['saved'])
        self.assertEqual(bad['calls']['save'],0)
        for stage,name in [('before','normal'),('after','normal'),('after','preset')]:
            run=load(ROOT/stage/'cli'/name/'actual.json');self.assertTrue(run['equal_original'])
            self.assertTrue(run['input_file_unchanged']);self.assertTrue(run['caller_context_unchanged']);self.assertTrue(run['default_context_unchanged'])
            self.assertEqual((run['calls']['replay'],run['calls']['save']),(1,1))
            actual=child('read','--record',f'{stage}/cli/{name}/records/cash-probe.json')
            save(ROOT/'after/read'/f'{stage}-{name}.json',actual)
            self.assertEqual(actual['receipt'],run['actual']);self.assertEqual(actual['stdout'],run['stdout'])
            self.assertTrue(actual['record_unchanged']);self.assertTrue(actual['ledger_import_blocked'])
            self.assertEqual(actual['engine_calls'],[]);self.assertEqual(actual['forbidden_effects'],[])
            self.assertTrue(actual['caller_context_unchanged']);self.assertTrue(actual['default_context_unchanged'])

    def test_05_shared_continuation_consumer(self):
        from capital_research.execution_context_20261027.reproduce import case
        from capital_research.execution import simulate
        job,expected,spec=case('continuation');value,record=probe(deepcopy(job),load(ROOT/'controls.json')['preset'],simulate)
        record.update(equal_original=value==expected,expected_id=_fp(expected),actual_id=_fp(value),
            original_reference=load(PROJECT/'capital_research/execution_context_20261027/input.json')['source'],case=spec,
            actual=dict(kind='EXACT_EXISTING_EXECUTION',id=_fp(value)) if value==expected else value)
        save(ROOT/'after/shared-consumer/actual.json',record)
        self.assertIsNone(record['error']);self.assertEqual(value,expected)
        self.assertTrue(record['input_unchanged']);self.assertTrue(record['caller_context_unchanged']);self.assertTrue(record['default_context_unchanged'])
        self.assertEqual(record['calls']['simulate'],1);self.assertGreater(record['calls']['replay'],0)
        self.assertEqual(record['calls']['save'],0);self.assertEqual(record['calls']['generate'],0);self.assertEqual(record['calls']['replay_sequence'],0)

    def test_06_only_numeric_boundary_changed(self):
        before=ast.parse((ROOT/'before/source/action_ledger.py').read_text());after=ast.parse((ROOT.parent/'action_ledger.py').read_text())
        old=next(x for x in before.body if isinstance(x,ast.FunctionDef) and x.name=='replay')
        new=next(x for x in after.body if isinstance(x,ast.FunctionDef) and x.name=='_replay_checked')
        self.assertEqual(ast.dump(old.args),ast.dump(new.args));self.assertEqual([ast.dump(x) for x in old.body],[ast.dump(x) for x in new.body])
        def remainder(tree):
            return [ast.dump(x) for x in tree.body if not
                (isinstance(x,ast.ImportFrom) and x.module=='decimal') and not
                (isinstance(x,ast.FunctionDef) and x.name in ('replay','_replay_checked')) and not
                (isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='IMPLEMENTATION_REVISION' for t in x.targets))]
        self.assertEqual(remainder(before),remainder(after));check_frozen()


if __name__=='__main__':unittest.main()
