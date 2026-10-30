"""Only C saved-result READ examples; no old suite or numerical execution."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from capital_research.lifecycle_compare import compare_saved, render_comparison
from .fixtures import ROOT, REPO, load, load_request
from .verify import verify


def actual(name):
    return load(ROOT / 'actual' / name / 'actual.json')


class CComparisonExamples(unittest.TestCase):
    def test_saved_READ_matches_frozen_expectations_and_text(self):
        cases = sorted((ROOT / 'cases').iterdir())
        self.assertEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case=case.name):
                result = actual(case.name)
                verify(load(case / 'expected.json'), result)
                self.assertEqual(render_comparison(result),
                    (ROOT / 'actual' / case.name / 'readable.txt').read_text())

    def test_original_account_order_scope_and_tokens_are_projected_once(self):
        spec = load(ROOT / 'cases/reviewed-versus-unknown-wait/input.json')
        result = actual('reviewed-versus-unknown-wait')
        for item, column in zip(spec['items'], result['columns']):
            source = load(REPO / item['source']['path'])['review']
            state = source['checkpoint']['state']
            account = column['summary']['account']
            self.assertEqual(account['saved_row'], state['row'])
            self.assertEqual(account['reviewed_evidence_tokens'], state['reviewed_evidence_tokens'])
            self.assertEqual(account['latest_decision_id'], state['latest_decision_id'])
            self.assertEqual(account['general_reserved_cash'], '100')
            order = next(o for o in column['summary']['orders'] if o['order_id'] == 'r1-B')
            self.assertEqual(order['original_order'], source['original_approval']['order'])
            self.assertEqual(order['saved_order_state'], source['execution']['order_states']['r1-B'])
            review = order['reviews'][0]
            self.assertEqual(review['same_order_continuation'], source['review_decision']['same_order_continuation'])
            self.assertEqual(review['new_evidence_tokens'], [])
        for source in load(ROOT / 'intake.json')['source_originals']:
            raw = (REPO / source['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])

    def test_API_does_not_mutate_new_C_comparable_or_refused_input(self):
        for name in ('reviewed-versus-unknown-wait', 'capacity-mismatch'):
            with self.subTest(case=name):
                request = load_request(name)
                before = deepcopy(request)
                self.assertEqual(compare_saved(request), actual(name))
                self.assertEqual(request, before)

    def test_fresh_C_CLI_forbids_engines_writes_processes_and_network(self):
        script = r'''
import sys,os,importlib.abc,runpy
allowed={'capital_research.lifecycle','capital_research.lifecycle_compare','capital_research.lifecycle_compare_read'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith(('graph_core','rotation_research')) or (fullname.startswith('capital_research.') and fullname not in allowed):raise RuntimeError('ENGINE_IMPORT:'+fullname)
sys.meta_path.insert(0,Guard())
def audit(event,args):
 if event=='open':
  mode=args[1];flags=args[2]
  if (mode is not None and any(x in mode for x in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):raise RuntimeError('READ_WRITE')
 if event in ('os.remove','os.rename','os.mkdir','subprocess.Popen','socket.connect'):raise RuntimeError('READ_SIDE_EFFECT:'+event)
sys.addaudithook(audit)
sys.argv=['capital_research.lifecycle_compare_read',*sys.argv[1:],'--format','json']
runpy.run_module('capital_research.lifecycle_compare_read',run_name='__main__')
'''
        for name, code in [('reviewed-versus-unknown-wait', 0), ('market-state-mismatch', 2)]:
            with self.subTest(case=name):
                spec = load(ROOT / 'cases' / name / 'input.json')
                args = [v['label'] + '=' + str(REPO / v['source']['path']) for v in spec['items']]
                run = subprocess.run([sys.executable, '-B', '-c', script, *args],
                    cwd=REPO / '股票系統M1_v0_18', text=True, capture_output=True)
                self.assertEqual(run.returncode, code, run.stderr)
                self.assertEqual(json.loads(run.stdout)['comparison'], actual(name))


if __name__ == '__main__':
    unittest.main()
