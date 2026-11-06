"""Bounded new source-pair checks; no old producer or suite."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from capital_research.research_choice_source import check_saved
from .fixtures import ROOT, load, materialize, fp


def result(name):
    return load(ROOT/'actual'/name/'result.json')


class SourceTests(unittest.TestCase):
    def test_frozen_expectations_and_qualification_are_separate(self):
        for row in load(ROOT/'input-expected.json'):
            i=row['input'];expected=row['expected'];r=result(i['name'])
            self.assertEqual(fp(materialize(i)),i['materialized_input_id'])
            self.assertEqual(r['check_status'],expected['check_status'])
            self.assertEqual(len(r['columns']),expected['columns'])
            if expected['reason']:
                self.assertIn(expected['reason'],r['reasons'])
            else:
                for key in ('choice_status','candidate_check','candidate_qualification'):
                    self.assertEqual(r[key],expected[key])
        self.assertEqual(result('rejected')['check_status'],'MATCHED')
        self.assertEqual(result('rejected')['choice_status'],'REFUSED')
        self.assertEqual(result('rejected')['candidate_role'],'REJECTED_SNAPSHOT')
        self.assertEqual(result('conditional')['candidate_qualification'],'WAIT_SETTLEMENT_REASSESSMENT')
        self.assertEqual(result('no-snapshot')['candidate_check'],'NO_SAVED_CANDIDATE')
        self.assertIsNone(result('no-snapshot')['candidate_qualification'])

    def test_same_ID_content_membership_and_full_bindings(self):
        good=result('general')['columns'][0]['candidate'];bad=result('rejected')['columns'][1]['candidate']
        self.assertEqual(good['id'],bad['id'])
        self.assertNotEqual(good['classification'],bad['classification'])
        self.assertEqual(result('wrong-source-same-candidate-id')['columns'],[])
        self.assertIn('latest_decision_id',result('wrong-latest')['mismatch_fields'])
        self.assertIn('historical_reviewed_tokens',result('missing-historical-token')['mismatch_fields'])
        self.assertIn('CANDIDATE_SNAPSHOT_MISMATCH',result('snapshot-content-mismatch')['reasons'])
        self.assertIn('CANDIDATE_ID_NOT_UNIQUE',result('duplicate-candidate-id')['reasons'])

    def test_pure_api_never_selects_writes_or_changes_any_input(self):
        for row in load(ROOT/'input-expected.json'):
            request=materialize(row['input']);before=deepcopy(request)
            with patch('builtins.open',side_effect=AssertionError('PURE_IO')), \
                 patch('capital_research.research_choice.choose_saved',side_effect=AssertionError('RESELECT')), \
                 patch('capital_research.quantity_choice_rules.select_candidate',side_effect=AssertionError('RESELECT')):
                actual=check_saved(**request)
            self.assertEqual(actual,result(row['input']['name']))
            self.assertEqual(request,before)
            for key in ('data_qualified','execution_model_qualified','historical_signal_eligible',
                'policy_authorized','live_execution_authorized','execution_authorized'):
                self.assertIs(actual[key],False)
            self.assertIsNone(actual['primary_pressure_id'])
            if actual['check_status']=='MATCHED':
                self.assertEqual(actual['columns'][0]['binding'],actual['columns'][1]['binding'])

    def test_fresh_CLI_and_two_column_display_preserve_originals(self):
        for row in load(ROOT/'input-expected.json'):
            name=row['input']['name'];receipt=load(ROOT/'actual'/name/'cli-json.json')
            self.assertEqual(receipt['exit_code'],row['expected']['exit_code'])
            self.assertEqual(receipt['guard'],'FRESH_NO_ENGINE_NO_RESELECT_NO_SAVE_NO_WRITE_NO_NETWORK')
            preservation=load(ROOT/'actual'/name/'read-preservation.json')
            self.assertEqual(preservation['before'],preservation['after'])
            if receipt['stdout']:
                self.assertEqual(json.loads(receipt['stdout'])['result'],result(name))
        for name in ['general','conditional','rejected','wrong-source-same-candidate-id']:
            text=load(ROOT/'actual'/name/'cli-text.json')
            self.assertEqual(text['stdout'],(ROOT/'actual'/name/'readable.txt').read_text())
            self.assertFalse(text['stderr'])
        self.assertIn('選擇紀錄保存值 | 明示來源保存值',(ROOT/'actual/general/readable.txt').read_text())
        self.assertIn('原研究意圖狀態：REFUSED',(ROOT/'actual/rejected/readable.txt').read_text())

    def test_IO_and_Journal_identity_errors_do_not_fallback_or_write(self):
        actual=load(ROOT/'io-actual.json');expected=load(ROOT/'io-input-expected.json')
        self.assertEqual(actual['before'],actual['after'])
        for row,spec in zip(actual['results'],expected):
            self.assertEqual(row['name'],spec['name'])
            self.assertEqual(row['actual']['exit_code'],2)
            self.assertFalse(row['actual']['stdout'])
            self.assertIn(spec['reason'],row['actual']['stderr'])


if __name__ == '__main__':
    unittest.main()
