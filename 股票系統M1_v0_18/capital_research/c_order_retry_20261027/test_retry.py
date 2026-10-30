"""Targeted retry entry, history and READ checks; no old suite rerun."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from capital_research.conditional_retry import retry_rejected
from capital_research.lifecycle import summarize_saved
from capital_research.lifecycle_compare import compare_saved, INPUT
from .verify import verify

ROOT = Path(__file__).parent
CAPITAL = ROOT.parent


def load(path):
    return json.loads(path.read_text())


def actual(name):
    folder = 'additional' if name == 'tampered-rejected-history' else 'initial'
    return load(ROOT / folder / name / 'actual.json')


class RetryTests(unittest.TestCase):
    def test_all_frozen_outcomes(self):
        cases = sorted((ROOT / 'cases').iterdir())
        self.assertEqual(len(cases), 17)
        for case in cases:
            with self.subTest(case=case.name):
                verify(load(case / 'input.json'), load(case / 'expected.json'), actual(case.name))

    def test_rejected_receipt_rights_reserve_latest_and_tokens_survive(self):
        request = load(ROOT / 'cases/qualification-restored/input.json')
        previous = request['previous_result']['review']
        r = actual('qualification-restored')['review']
        e = r['execution']
        self.assertEqual(r['prefix_execution'], previous['execution'])
        self.assertEqual(r['prefix_checkpoint'], previous['checkpoint'])
        self.assertEqual(e['reassessment_attempts'][0], previous['execution']['reassessment_attempts'][0])
        self.assertNotEqual(e['reassessment_attempts'][0]['decision']['decision_id'], e['latest_decision_id'])
        self.assertEqual(e['latest_decision_id'], r['review_decision']['decision_id'])
        self.assertEqual(r['review_decision']['continuity']['latest_predecessor_id'], previous['execution']['latest_decision_id'])
        job = r['execution_job']
        self.assertEqual(job['ledger_input'], previous['execution_job']['ledger_input'])
        self.assertEqual(job['ledger_close_proof'], previous['execution_job']['ledger_close_proof'])
        self.assertEqual(job['orders'], previous['execution_job']['orders'])
        self.assertEqual(job['tape'][:len(previous['execution_job']['tape'])], previous['execution_job']['tape'])
        self.assertEqual(job['reassessments'][:-1], previous['execution_job']['reassessments'])
        self.assertEqual(r['checkpoint']['state']['general_reserved_cash'], '100')
        self.assertEqual(r['checkpoint']['state']['origin_initial_capital'], '1430')
        self.assertEqual(r['checkpoint']['state']['row']['cash_claims'], [])
        self.assertEqual(r['checkpoint']['state']['row']['share_receivables'], [])
        self.assertEqual(r['checkpoint']['state']['row']['shares'], dict(A='60', B='25', C='2'))
        self.assertEqual([f['code'] for f in e['fills']], ['A', 'B'])

    def test_tail_does_not_change_cutoff_decision_and_unimplemented_stops(self):
        positive = actual('qualification-restored')['review']
        for name in ('partial-seven', 'limit-up-no-fill'):
            r = actual(name)['review']
            self.assertEqual(r['review_decision'], positive['review_decision'])
            self.assertEqual(r['prefix_execution'], positive['prefix_execution'])
            self.assertNotEqual(r['numeric_result'], positive['numeric_result'])
        stopped = actual('limit-before-activation-unsupported')['review']
        self.assertIsNone(stopped['execution'])
        self.assertIsNotNone(stopped['review_request'])
        self.assertIsNotNone(stopped['review_decision'])
        self.assertTrue(stopped['activation_restrictions'])
        summary = summarize_saved(actual('limit-before-activation-unsupported'))
        self.assertEqual(summary['status'], 'READABLE', summary['reasons'])
        self.assertEqual(summary['source']['view'], 'HISTORICAL_BEFORE_STOP')

    def test_public_entry_is_deterministic_and_input_unchanged(self):
        request = load(ROOT / 'cases/qualification-restored/input.json')
        before = deepcopy(request)
        self.assertEqual(retry_rejected(request), actual('qualification-restored'))
        self.assertEqual(request, before)
        # Re-submission starts from the same saved origin; no extra receipt/fill.
        self.assertEqual(len(actual('qualification-restored')['review']['execution']['reassessment_attempts']), 2)

    def test_new_batch_needs_independent_trigger(self):
        old = load(ROOT / 'new-batch/old-trigger-actual.json')['decision']
        fresh = load(ROOT / 'new-batch/new-trigger-actual.json')['decision']
        p = next(p for p in old['layer3']['alternatives'] if p['id'] == 'new-C-batch-after-retry')
        self.assertIn('NO_NEW_INDEPENDENT_TRIGGER', p['reasons'])
        p = next(p for p in fresh['layer3']['alternatives'] if p['id'] == 'new-C-batch-after-retry')
        self.assertTrue(p['feasible'], p['reasons'])
        self.assertEqual(p['family'], 'C')
        self.assertEqual(fresh['continuity']['origin_initial_capital'], '1430')
        self.assertNotIn('same_order_continuation', fresh)
        self.assertTrue(any('B-new-independent' in token for token in fresh['new_evidence_tokens']))

    def test_new_READ_and_old_C_E_saved_summaries_remain_compatible(self):
        saved = actual('qualification-restored')
        summary = summarize_saved(saved)
        self.assertEqual(summary['status'], 'READABLE', summary['reasons'])
        self.assertEqual(summary['account']['saved_row'], saved['review']['checkpoint']['state']['row'])
        order = next(o for o in summary['orders'] if o['order_id'] == 'r1-B')
        self.assertEqual([v['outcome'] for v in order['reviews']], ['REJECTED', 'ACCEPTED'])
        comparison = compare_saved(dict(schema=INPUT, synthetic=True,
            items=[dict(label='同源一', saved_result=saved), dict(label='同源二', saved_result=deepcopy(saved))]))
        self.assertEqual(comparison['status'], 'COMPARABLE', comparison['refusals'])
        old_c = load(CAPITAL / 'c_order_review_20261026/after-checkpoint-fix/valid-C-same-order/actual.json')
        self.assertEqual(summarize_saved(old_c), load(CAPITAL / 'c_order_review_20261026/readback/valid-C-same-order.json'))
        changed_status = deepcopy(old_c)
        changed_status['review']['status'] = 'REPLAYED_RETRY_NOT_ACTIVATED'
        self.assertIn('UNSUPPORTED_SAVED_STATUS', summarize_saved(changed_status)['reasons'])
        old_e = load(CAPITAL / 'conditional_quantity_review_20261026/after-final/valid-old-fact/actual.json')
        self.assertEqual(summarize_saved(old_e), load(CAPITAL / 'lifecycle_20261026/after-final/full-pending/actual.json'))

    def test_fresh_READ_does_not_import_engines_or_write(self):
        script = r'''
import sys,os,runpy,importlib.abc
allowed={'capital_research.lifecycle','capital_research.lifecycle_read'}
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
sys.argv=['capital_research.lifecycle_read',sys.argv[1],'--format','json']
runpy.run_module('capital_research.lifecycle_read',run_name='__main__')
'''
        path = (ROOT / 'initial/qualification-restored/actual.json').resolve()
        run = subprocess.run([sys.executable, '-B', '-c', script, str(path)], text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['summary'], summarize_saved(actual('qualification-restored')))


if __name__ == '__main__':
    unittest.main()
