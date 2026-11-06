"""Finite child-selection, persistence and original-parent invariants."""
import json
import unittest
from pathlib import Path
from capital_research.lifecycle import _fp
from .build import ROOT,PROJECT,load


class SupplementTests(unittest.TestCase):
    def test_frozen_expectations_and_eligibility_separation(self):
        self.assertEqual(len(load(ROOT/'summary.json')),8)
        for row in load(ROOT/'input-expected.json'):
            self.assertEqual(_fp(row['request']),row['input_id'])
            value=load(ROOT/'actual'/row['name']/'select.json')
            self.assertEqual(value['workflow_status'],row['expected']['status'])
            if row['expected']['reason']:self.assertIn(row['expected']['reason'],value['reasons'])
            for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized','execution_authorized'):
                self.assertIs(value[k],False)
            self.assertIsNone(value['primary_pressure_id'])
        general=load(ROOT/'actual/general/select.json')['supplement']
        conditional=load(ROOT/'actual/conditional/select.json')['supplement']
        refused=load(ROOT/'actual/unlisted-quantity/select.json')['supplement']
        self.assertEqual(general['selected_targets'],dict(A='60',B='26',C='2'))
        self.assertEqual(conditional['choice_status'],'RECORDED_CONDITIONAL_RESEARCH_INTENT')
        self.assertEqual(refused['choice_status'],'REFUSED');self.assertIsNone(refused['selected_targets'])
        self.assertIsNone(refused['source_check'])

    def test_parent_unchanged_full_account_and_tokens_preserved(self):
        for spec in load(ROOT/'input-expected.json'):
            proof=load(ROOT/'actual'/spec['name']/'parent-preservation.json')
            self.assertEqual(proof['before'],proof['after'])
        spec=load(ROOT/'input-expected.json')[0];parent=PROJECT/spec['parent_store'];pid=spec['parent_id']
        result=load(parent/(pid+'--result.json'))['value']
        self.assertEqual(result['outcome'],'AWAITING_EXPLICIT_SELECTION');self.assertIsNone(result['choice_record_id'])
        self.assertFalse((parent/(pid+'--choice.json')).exists())
        gen=load(parent/(pid+'--generation.json'))['value'];s=gen['adapter']['quantity_request']['continuation']['checkpoint']['state']
        self.assertEqual(s['origin_initial_capital'],'1430');self.assertEqual(s['general_reserved_cash'],'100')
        self.assertEqual(s['row']['settled_cash'],'275.100');self.assertEqual(s['row']['shares'],dict(A='60',B='25',C='2'))
        self.assertEqual(s['unfilled_orders'],[]);self.assertEqual(s['row']['purchase_payable'],'0')
        for name in ['general','conditional']:
            child=load(ROOT/'actual'/name/'select.json')['supplement']
            self.assertEqual(child['parent_binding']['parent_result_id'],result['result_id'])
            self.assertEqual(child['parent_binding']['generation_id'],result['generation_id'])
            self.assertEqual(child['parent_binding']['source_binding']['historical_reviewed_tokens'],s['reviewed_evidence_tokens'])
            self.assertFalse(any(p.name.endswith('--generation.json') for p in (ROOT/'runs'/name).iterdir()))

    def test_public_SELECT_and_READ_are_generation_free_and_immutable(self):
        for spec in load(ROOT/'input-expected.json'):
            receipt=load(ROOT/'actual'/spec['name']/'CLI-select.json')
            self.assertFalse(receipt['stderr'])
            self.assertEqual(receipt['calls'],dict(generation=0,choice=spec['expected']['choice_calls'],source_check=spec['expected']['check_calls']))
        for name in ['general','conditional','unlisted-quantity']:
            select=load(ROOT/'actual'/name/'select.json')
            read=load(ROOT/'actual'/name/'CLI-read.json');text=load(ROOT/'actual'/name/'CLI-read-text.json')
            self.assertEqual(read['calls'],dict(generation=0,choice=0,source_check=0))
            self.assertFalse(read['stderr']);self.assertFalse(text['stderr'])
            self.assertEqual(json.loads(read['stdout'])['supplement'],select['supplement'])
            self.assertIn('原等待結果留史',text['stdout'])
            proof=load(ROOT/'actual'/name/'child-preservation.json');self.assertEqual(proof['before'],proof['after'])

    def test_same_child_repeat_and_content_conflict_do_not_reselect(self):
        value=load(ROOT/'idempotence.json')
        self.assertEqual(value['repeat']['workflow_status'],'SUPPLEMENT_EXISTS_READ_REQUIRED')
        self.assertEqual(value['conflict']['workflow_status'],'SUPPLEMENT_ID_CONFLICT')
        self.assertEqual(value['before'],value['after'])

    def test_storage_UNKNOWN_halts_and_READ_only_reports_saved_prefix(self):
        rows=load(ROOT/'fault-actual.json');expected=load(ROOT/'fault-input-expected.json')
        self.assertEqual(len(rows),3)
        for row,spec in zip(rows,expected):
            self.assertEqual(row['stage'],spec['stage']);self.assertEqual(row['actual']['workflow_status'],'STOPPED_STORAGE')
            self.assertEqual(row['actual']['storage'][spec['stage']],'UNKNOWN')
            self.assertEqual(row['choice_calls'],spec['expected_select_calls']);self.assertEqual(row['check_calls'],spec['expected_check_calls'])
            self.assertEqual(row['explicit_READ']['workflow_status'],spec['READ_status'])
            self.assertEqual(row['before'],row['after'])

    def test_corruption_and_incomplete_parent_are_refused_without_repair(self):
        rows=load(ROOT/'corruption-actual.json');self.assertEqual(len(rows),4)
        for row in rows:
            self.assertEqual(row['actual']['workflow_status'],'PARENT_REFUSED' if row['name']=='parent-prefix-only' else 'UNREADABLE')
            self.assertEqual(row['before'],row['after']);self.assertTrue(row['actual']['reasons'])


if __name__=='__main__':unittest.main()
