"""Bounded common-context, null preservation and READ-only route checks."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from capital_research.supplement_compare import INPUT,compare_read_receipts
from capital_research.supplement_compare_read import read_and_compare
from .prepare import ROOT,PROJECT,BASE,load


def result(name):return load(ROOT/'actual'/name/'result.json')


class CompareTests(unittest.TestCase):
    def test_frozen_comparison_outcomes(self):
        index=load(ROOT/'case-index.json');self.assertEqual(len(index),9)
        for case in index:
            name=case['name'];expected=load(ROOT/'cases'/name/'expected.json');r=result(name)
            self.assertEqual(r['status'],expected['status']);self.assertEqual(len(r['columns']),expected['columns'])
            if expected['reason']:self.assertTrue(any(v['reason']==expected['reason'] for v in r['refusals']))
            for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized','execution_authorized'):
                self.assertIs(r[k],False)
            self.assertIsNone(r['ranking']);self.assertIsNone(r['selected_label']);self.assertIsNone(r['primary_pressure_id'])

    def test_same_parent_ID_different_saved_content_is_refused(self):
        r=result('same-parent-id-different-content')
        trace=load(ROOT/'actual/same-parent-id-different-content/CLI-json.json')['original_READ_trace']
        self.assertEqual([v['status'] for v in trace],['READ_ONLY','READ_ONLY'])
        self.assertEqual(trace[0]['parent_id'],trace[1]['parent_id'])
        self.assertEqual(trace[0]['generation_id'],trace[1]['generation_id'])
        self.assertEqual(trace[0]['account_id'],trace[1]['account_id'])
        self.assertNotEqual(trace[0]['parent_result_id'],trace[1]['parent_result_id'])
        self.assertEqual(r['columns'],[])
        self.assertIn('/parent_binding/parent_result_id',[v['path'] for v in r['differences']])

    def test_conditional_refused_and_missing_values_never_become_allocations(self):
        r=result('with-refusal');general,conditional,refused=r['columns']
        self.assertEqual(conditional['candidate_qualification'],'WAIT_SETTLEMENT_REASSESSMENT')
        self.assertEqual(refused['choice_status'],'REFUSED');self.assertIsNone(refused['selected_targets'])
        self.assertIsNone(refused['estimated_cost']);self.assertIsNone(refused['source_check_status'])
        self.assertNotIn('total_cost',r);self.assertNotIn('combined_targets',r)
        text=(ROOT/'actual/with-refusal/readable.txt').read_text()
        for value in ['未選中','原件未提供','未執行','不加總股數、成本或資金']:self.assertIn(value,text)
        later=result('later-record-time');self.assertEqual(later['status'],'COMPARABLE')
        self.assertNotEqual(later['columns'][0]['recorded_at'],later['columns'][1]['recorded_at'])
        self.assertEqual(later['common_binding']['source_binding']['data_cutoff'],'2026-01-12T16:00:00+08:00')

    def test_pure_comparison_preserves_all_saved_receipts_without_IO(self):
        items=[]
        old=ROOT.parent/'selection_supplement_20261027/actual'
        for label,name in [('一般','general'),('條件','conditional'),('拒絕對照','unlisted-quantity')]:
            items.append(dict(label=label,receipt=json.loads(load(old/name/'CLI-read.json')['stdout'])))
        request=dict(schema=INPUT,synthetic=True,items=items);before=deepcopy(request)
        with patch('builtins.open',side_effect=AssertionError('PURE_IO')):
            actual=compare_read_receipts(request)
        self.assertEqual(actual,result('with-refusal'));self.assertEqual(request,before)

    def test_preflight_label_and_resource_errors_do_not_read_any_sources(self):
        for name in ['duplicate-label','resource-limit']:
            request=load(ROOT/'cases'/name/'input.json');before=deepcopy(request)
            with patch('capital_research.supplement_compare_read.read_supplement',side_effect=AssertionError('PREFLIGHT_IO')) as read:
                actual=read_and_compare(request)
            read.assert_not_called();self.assertEqual(request,before)
            self.assertEqual(actual['comparison'],result(name))

    def test_fresh_READ_routes_and_originals_are_immutable(self):
        proof=load(ROOT/'preservation.json');self.assertEqual(proof['before'],proof['after'])
        for row in load(ROOT/'case-index.json'):
            for name in ['CLI-json.json','CLI-text.json']:
                receipt=load(ROOT/'actual'/row['name']/name)
                self.assertFalse(receipt['stderr'])
                self.assertEqual(receipt['guard'],'FRESH_NO_ENGINE_NO_GENERATION_NO_SELECTION_NO_SOURCE_VERDICT_NO_SAVE_NO_WRITE_NO_NETWORK')
            for item in load(ROOT/'actual'/row['name']/'CLI-json.json')['original_READ_trace'] or []:
                self.assertIn(item['status'],['READ_ONLY','UNREADABLE','INCOMPLETE_SUPPLEMENT_PREFIX'])


if __name__=='__main__':unittest.main()
