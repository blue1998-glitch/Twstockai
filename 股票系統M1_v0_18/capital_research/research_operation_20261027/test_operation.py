"""Only the new coordinator, saved-stage integrity and necessary fault boundaries."""
import json
import unittest
from pathlib import Path
from .fixtures import ROOT,load,materialize,fp

ACTUAL=ROOT/'initial'


class OperationTests(unittest.TestCase):
    def test_five_explicit_runs_and_original_inputs(self):
        summary=load(ACTUAL/'summary.json')
        self.assertEqual(len(summary),5)
        self.assertTrue(all(v['status']=='PASS' and v['generator_calls']==1 for v in summary))
        for row in load(ROOT/'input-expected.json'):
            i=row['input'];expected=row['expected'];name=i['name']
            self.assertEqual(fp(materialize(i)),i['materialized_input_id'])
            receipt=load(ACTUAL/'actual'/name/'run.json')
            self.assertEqual(receipt['workflow_status'],expected['workflow_status'])
            self.assertEqual(receipt['observed']['choice_status'],expected['choice_status'])
            self.assertEqual(receipt['observed']['check_status'],expected['check_status'])
            self.assertEqual(receipt['storage']['result'],'SAVED_AND_READ_BACK')
            for k in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized','execution_authorized'):
                self.assertIs(receipt[k],False);self.assertIs(receipt['operation'][k],False)
            self.assertIsNone(receipt['primary_pressure_id'])

    def test_missing_selection_and_rejection_never_advance(self):
        for name,status in [('no-selection','AWAITING_EXPLICIT_SELECTION'),('search-limit','GENERATION_REFUSED')]:
            receipt=load(ACTUAL/'actual'/name/'run.json')
            self.assertEqual(receipt['workflow_status'],status)
            self.assertEqual(receipt['storage']['choice'],'NOT_PERFORMED')
            self.assertIsNone(receipt['operation']['choice_record_id'])
            self.assertIsNone(receipt['operation']['source_check'])
        refused=load(ACTUAL/'actual/old-trigger/run.json')
        self.assertEqual(refused['observed']['choice_status'],'REFUSED')
        self.assertIsNone(refused['operation']['source_check'])
        self.assertEqual(load(ACTUAL/'missing-selection-field.json')['workflow_status'],'INPUT_REFUSED')

    def test_idempotence_conflict_and_public_RUN_scope(self):
        r=load(ACTUAL/'idempotence.json')
        self.assertEqual(r['repeat']['workflow_status'],'OPERATION_EXISTS_READ_REQUIRED')
        self.assertEqual(r['conflict']['workflow_status'],'OPERATION_ID_CONFLICT')
        self.assertEqual(r['before'],r['after'])
        trace=load(ACTUAL/'actual/general/CLI-run.json')
        self.assertEqual(trace['call_counts'],dict(generation=1,choice=1,source_check=1))
        self.assertEqual(trace['guard'],'RUN_ONLY_WRITES_EXPLICIT_STORE_NO_NETWORK')

    def test_unknown_storage_stops_and_explicit_READ_recovers_only_saved_facts(self):
        expected=load(ROOT/'fault-input-expected.json')['rows'];actual=load(ACTUAL/'fault-actual.json')
        self.assertEqual(len(actual),4)
        for row,spec in zip(actual,expected):
            self.assertEqual(row['name'],spec['name'])
            self.assertEqual(row['actual']['workflow_status'],'STOPPED_STORAGE')
            self.assertEqual(row['actual']['storage'][spec['key'][2:]],'UNKNOWN')
            self.assertEqual(row['cached_backend_calls'],spec['expected_calls'])
            self.assertEqual(row['source_check_calls'],1 if spec['key']=='--result' else 0)
            self.assertEqual(row['before_READ'],row['after_READ'])
            self.assertEqual(row['explicit_READ']['workflow_status'],'READ_ONLY' if spec['key']=='--result' else 'INCOMPLETE_SAVED_PREFIX')

    def test_READ_is_engine_free_immutable_and_preserves_original_accounts(self):
        for spec in load(ROOT/'input-expected.json'):
            name=spec['input']['name'];receipt=load(ACTUAL/'actual'/name/'run.json')
            read=load(ACTUAL/'actual'/name/'CLI-read.json')
            self.assertFalse(read['stderr'])
            self.assertEqual(read['guard'],'FRESH_READ_NO_ENGINE_NO_GENERATION_NO_SELECTION_NO_SOURCE_CHECK_NO_SAVE_NO_WRITE_NO_NETWORK')
            self.assertEqual(json.loads(read['stdout'])['operation'],receipt['operation'])
            preservation=load(ACTUAL/'actual'/name/'READ-preservation.json')
            self.assertEqual(preservation['before'],preservation['after'])
            key='demo-'+name;store=ACTUAL/'runs'/name
            generation=load(store/(key+'--generation.json'))['value']
            if generation['adapter']['status']=='GENERATED':
                original=materialize(spec['input'])['generation_input']['checkpoint']['state']
                carried=generation['adapter']['quantity_request']['continuation']['checkpoint']['state']
                self.assertEqual(original,carried)
                self.assertEqual(original['origin_initial_capital'],'1430')
                self.assertEqual(original['general_reserved_cash'],'100')
                self.assertEqual(original['row']['shares'],dict(A='60',B='25',C='2'))
                self.assertEqual(original['row']['settled_cash'],'275.100')

    def test_cross_stage_corruption_is_unreadable_and_not_repaired(self):
        rows=load(ACTUAL/'corruption-actual.json')
        self.assertEqual(len(rows),4)
        for row in rows:
            self.assertEqual(row['actual']['workflow_status'],'UNREADABLE')
            self.assertTrue(row['actual']['reasons'])
            self.assertEqual(row['before'],row['after'])


if __name__=='__main__':unittest.main()
