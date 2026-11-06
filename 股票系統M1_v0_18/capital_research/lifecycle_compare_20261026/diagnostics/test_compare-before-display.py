"""Focused acceptance of the new read-only gate, no numerical producer."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from capital_research.lifecycle_compare import compare_saved, render_comparison
from .fixtures import ROOT, load
from .verify import verify


def actual(name):return json.loads((ROOT/'after-final'/name/'actual.json').read_text())


class ComparisonTests(unittest.TestCase):
    def case(self,name):
        request=load(name);before=deepcopy(request);result=compare_saved(request)
        verify(json.loads((ROOT/'cases'/name/'expected.json').read_text()),result)
        self.assertEqual(request,before);self.assertEqual(result,actual(name))
        return result

    def test_same_opening_different_results_can_be_side_by_side(self):
        r=self.case('wait-versus-reviewed')
        self.assertEqual([c['summary']['account']['origin_initial_capital'] for c in r['columns']],['1330','1330'])
        self.assertEqual([c['summary']['account']['general_reserved_cash'] for c in r['columns']],['100','100'])
        self.assertEqual(r['columns'][0]['summary']['account']['saved_row']['cash_claims'],r['columns'][1]['summary']['account']['saved_row']['cash_claims'])
        self.assertNotEqual(r['columns'][0]['summary']['account']['saved_row']['available_cash_strict'],r['columns'][1]['summary']['account']['saved_row']['available_cash_strict'])

    def test_same_document_is_control_not_independent_sample(self):self.case('same-document-control')

    def test_capacity_state_availability_and_settlement_are_bound(self):
        for name in ('capacity-mismatch','market-state-mismatch','available-time-mismatch','settlement-date-mismatch'):
            with self.subTest(name=name):self.case(name)

    def test_source_basis_unknown_values_and_missing_tape_refuse(self):
        for name in ('source-binding-refused','basis-binding-refused','unknown-capacity-refused','missing-tape-refused'):
            with self.subTest(name=name):self.case(name)

    def test_opening_capital_rights_and_cutoffs_are_bound(self):
        for name in ('opening-capital-mismatch','opening-rights-tamper-refused','observation-cutoff-mismatch','cutoff-binding-refused'):
            with self.subTest(name=name):self.case(name)

    def test_multiround_requires_complete_original_jobs(self):
        r=self.case('multiround-complete-job-control')
        self.assertEqual(len(r['provenance'][0]['saved_job_ids']),2)
        self.case('prior-market-job-missing')

    def test_stopped_history_and_cached_summary_cannot_prove_market(self):
        self.case('stopped-result-refused');self.case('summary-without-market-refused')

    def test_future_tail_integrity_is_separate_from_window_identity(self):
        r=self.case('future-tail-outside-window')
        self.assertNotEqual(r['provenance'][0]['document_id'],r['provenance'][1]['document_id'])
        self.assertEqual(r['provenance'][0]['identity_ids'],r['provenance'][1]['identity_ids'])

    def test_labels_limits_and_diagnostics_never_truncate_the_gate(self):
        self.case('duplicate-label-refused');self.case('resource-limit-refused')
        request=load('capacity-mismatch')
        # Explicit read-only JSON variant. Additional declared row fields matter;
        # exceeding display budget cannot turn a mismatch into COMPARABLE.
        tape=request['items'][1]['saved_result']['review']['execution_job']['tape']
        for i in range(70):tape[0]['diagnostic-extra-'+str(i)]=str(i)
        r=compare_saved(request)
        self.assertEqual(r['status'],'REFUSED');self.assertEqual(r['columns'],[])
        self.assertEqual(len(r['differences']),64);self.assertGreater(r['total_mismatches'],64)
        self.assertTrue(r['details_truncated'])

    def test_text_shows_no_winner_or_zero_for_absent_order(self):
        r=actual('wait-versus-reviewed');text=render_comparison(r)
        self.assertEqual(text,(ROOT/'after-final/wait-versus-reviewed/readable.txt').read_text())
        self.assertIn('r1-B 已成交 | 0 | 20',text)
        self.assertIn('不是可追加金額',text)
        self.assertIn('拒絕同條件並列',render_comparison(actual('capacity-mismatch')))
        # Renderer-only saved summary variant, no approval or comparison run.
        r=deepcopy(r);r['columns'][0]['summary']['orders']=[o for o in r['columns'][0]['summary']['orders'] if o['order_id']!='r1-B']
        self.assertIn('r1-B 已成交 | 無此保存單 | 20',render_comparison(r))

    def test_fresh_cli_cannot_import_engines_write_or_connect(self):
        sources=json.loads((ROOT/'cases/wait-versus-reviewed/input.json').read_text())['items']
        paths=[ROOT.resolve().parents[2]/x['source']['path'] for x in sources]
        before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
        script=r'''
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
sys.argv=['capital_research.lifecycle_compare_read','等待='+sys.argv[1],'原單續用='+sys.argv[2],'--format','json']
runpy.run_module('capital_research.lifecycle_compare_read',run_name='__main__')
'''
        run=subprocess.run([sys.executable,'-B','-c',script,*map(str,paths)],text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['comparison'],actual('wait-versus-reviewed'))
        self.assertEqual(before,[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths])


if __name__=='__main__':unittest.main()
