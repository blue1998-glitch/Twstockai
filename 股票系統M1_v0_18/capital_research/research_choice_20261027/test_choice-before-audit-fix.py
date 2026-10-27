"""Focused saved-choice and Journal checks. No producer or market replay."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from capital_research.research_choice import choose_saved, validate_record
from capital_research.research_choice_workflow import select_and_save, read_choice
from .fixtures import ROOT, REPO, load, materialize, fp
from .verify import verify


def request(name):
    return materialize(load(ROOT / 'cases' / name / 'input.json'))


def actual(name):
    return load(ROOT / 'after-final' / name / 'actual.json')


class ChoiceTests(unittest.TestCase):
    def test_all_frozen_selection_outcomes(self):
        cases = sorted((ROOT / 'cases').iterdir())
        self.assertEqual(len(cases), 18)
        for folder in cases:
            with self.subTest(case=folder.name):
                spec = load(folder / 'input.json'); value = materialize(spec)
                self.assertEqual(fp(value), spec['materialized_input_id'])
                verify(value, load(folder / 'expected.json'), actual(folder.name))

    def test_same_target_ID_cannot_borrow_another_generation_qualification(self):
        good = actual('grid-new-trigger')['choice']
        old = actual('old-trigger-refused')['choice']
        self.assertEqual(good['selected']['id'], old['rejected_candidate']['id'])
        self.assertNotEqual(good['source_binding']['source_document_id'], old['source_binding']['source_document_id'])
        self.assertIsNone(old['selected'])
        self.assertIn('SOURCE_BINDING_MISMATCH', actual('same-id-cross-generation-refused')['choice']['reasons'])
        self.assertIn('SAVED_CANDIDATE_QUALIFICATION_CONFLICT', actual('contradictory-qualification')['choice']['reasons'])

    def test_shared_matching_is_compatible_with_original_wrapper(self):
        from capital_research.core import quantity
        from capital_research.quantity_replay import _select
        old_tree = ast.parse((ROOT / 'baseline_quantity_replay.py').read_text())
        function = next(n for n in old_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_select')
        namespace = dict(quantity=quantity)
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<frozen-original-select>', 'exec'), namespace)
        original = namespace['_select']
        candidates = request('grid-new-trigger')['saved_result']['adapter']['generation']['research']['candidates']
        vectors = [dict(mode=m, sell_A=None, additional_B=None, reason='COMPATIBILITY') for m in ['HOLD', 'EXIT_A_KEEP_CASH', 'FULL_TRANSFER']]
        vectors += [dict(mode='GRID', sell_A='0', additional_B=n, reason='COMPATIBILITY') for n in ['1', '1.0', '1e0', '99', '-1', '0.5']]
        vectors += [dict(mode='GRID', sell_A='0', additional_B='1', reason=''), dict(mode='BAD', sell_A=None, additional_B=None, reason='X')]
        def run(fn, selection):
            try:
                return ('RESULT', fn(deepcopy(candidates), deepcopy(selection)))
            except Exception as exc:
                return ('ERROR', type(exc).__name__, str(exc))
        for selection in vectors:
            with self.subTest(selection=selection):
                self.assertEqual(run(_select, selection), run(original, selection))

    def test_public_selection_is_pure_and_preserves_entire_source(self):
        value = request('grid-new-trigger'); before = deepcopy(value)
        with patch('builtins.open', side_effect=AssertionError('PURE_CORE_IO')):
            saved = choose_saved(value)
        self.assertEqual(saved, actual('grid-new-trigger'))
        self.assertEqual(value, before)
        self.assertIsNone(value['saved_result']['adapter']['generation']['research']['selected_id'])
        conditional = actual('full-conditional')['choice']
        self.assertEqual(conditional['status'], 'RECORDED_CONDITIONAL_RESEARCH_INTENT')
        self.assertFalse(conditional['execution_authorized'])
        self.assertEqual(conditional['selected']['core_evaluation']['funding'], 'WAIT_SALE_SETTLEMENT_AND_REEVALUATE')

    def test_journal_roundtrip_idempotence_conflict_and_unknown_preserve_files(self):
        with tempfile.TemporaryDirectory() as folder:
            first = select_and_save(folder, 'one', request('grid-new-trigger'))
            path = Path(folder) / 'one.json'; before = path.read_bytes()
            self.assertEqual(first['storage_status'], 'SAVED_AND_READ_BACK')
            self.assertEqual(select_and_save(folder, 'one', request('grid-new-trigger')), first)
            conflict = select_and_save(folder, 'one', request('hold'))
            self.assertEqual(conflict['storage_status'], 'NOT_SAVED')
            self.assertEqual(path.read_bytes(), before)
            with patch('capital_research.research_choice_workflow.choose_saved', side_effect=AssertionError('READ_RESELECT')):
                read = read_choice(folder, 'one')
            self.assertEqual(read['record'], first['record'])
            with patch('rotation_research.store.os.fsync', side_effect=OSError('INJECTED_FSYNC_FAILURE')):
                unknown = select_and_save(folder, 'unknown', request('hold'))
            self.assertEqual(unknown['storage_status'], 'UNKNOWN')
            self.assertTrue((Path(folder) / 'unknown.json').exists())
            self.assertEqual(read_choice(folder, 'unknown')['storage_status'], 'READ_ONLY')
            partial = Path(folder) / 'partial.json'; partial.write_text('{')
            self.assertEqual(select_and_save(folder, 'partial', request('hold'))['storage_status'], 'NOT_SAVED')
            self.assertEqual(partial.read_text(), '{')

    def test_signed_record_READ_refuses_edits_and_never_reselects(self):
        saved = actual('grid-new-trigger'); tampered = deepcopy(saved)
        tampered['choice']['selected']['plan']['targets']['B'] = '27'
        with self.assertRaisesRegex(ValueError, 'RECORD_ID_FINGERPRINT_CONFLICT'):
            validate_record(tampered)
        for folder in (ROOT / 'cases').iterdir():
            with patch('capital_research.research_choice.choose_saved', side_effect=AssertionError('READ_RESELECT')):
                self.assertEqual(validate_record(actual(folder.name)), actual(folder.name))

    def test_fresh_CLI_SELECT_READ_excludes_engines_network_and_READ_writes(self):
        script = r'''
import sys,os,runpy,importlib.abc
allowed={'capital_research.research_choice','capital_research.research_choice_workflow','capital_research.research_choice_cli','capital_research.quantity_choice_rules','capital_research.lifecycle','rotation_research.store'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('graph_core') or (fullname.startswith(('capital_research.','rotation_research.')) and fullname not in allowed):raise RuntimeError('NUMERIC_IMPORT:'+fullname)
sys.meta_path.insert(0,Guard())
operation,store,input_path=sys.argv[1:]
def audit(event,args):
 if event=='open':
  mode=args[1];flags=args[2];writing=(mode is not None and any(x in mode for x in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
  if writing and (operation=='READ' or not (os.path.abspath(str(args[0]))==store or os.path.abspath(str(args[0])).startswith(store+os.sep))):raise RuntimeError('UNAUTHORIZED_WRITE')
 if event=='os.mkdir' and (operation=='READ' or os.path.abspath(args[0])!=store):raise RuntimeError('UNAUTHORIZED_MKDIR')
 if event in ('os.remove','os.rename','subprocess.Popen','socket.connect'):raise RuntimeError('SIDE_EFFECT:'+event)
sys.addaudithook(audit)
sys.argv=['capital_research.research_choice_cli',operation,'--store',store,'--id','fresh']+(['--input',input_path] if operation=='SELECT' else [])
runpy.run_module('capital_research.research_choice_cli',run_name='__main__')
'''
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'input.json'; source.write_text(json.dumps(request('grid-new-trigger'), ensure_ascii=False))
            digest = hashlib.sha256(source.read_bytes()).hexdigest(); store = str(Path(folder) / 'store')
            outputs = []
            for operation in ('SELECT', 'READ'):
                run = subprocess.run([sys.executable, '-B', '-c', script, operation, store, str(source)],
                    cwd=REPO / '股票系統M1_v0_18', text=True, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                outputs.append(json.loads(run.stdout))
            self.assertEqual(outputs[0]['record'], outputs[1]['record'])
            self.assertEqual(outputs[0]['record']['value'], actual('grid-new-trigger'))
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
