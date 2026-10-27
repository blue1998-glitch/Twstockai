"""New workflow only: real bounded RUNs, cached fault doubles and pure READ."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from rotation_research.store import Journal
from capital_research.lifecycle import FLAGS,_fp
from capital_research import evaluated_replay as flow
from .prepare import ROOT,PROJECT,load,save,info
from .build import command


def request():return load(ROOT/'cases/complete/input.json')


def actual(case,stage):return load(ROOT/'runs-final'/case/('evaluated-'+case+'--'+stage+'.json'))['value']


def files(root):return {p.name:info(p) if p.is_relative_to(PROJECT) else _fp(p.read_text()) for p in Path(root).glob('*.json')}


def write_value(root,key,value):
    p=Path(root)/(key+'.json');p.write_text(json.dumps(dict(schema='rotation-record/0.1',id=key,value=value),ensure_ascii=False,indent=2)+'\n')


class WorkflowTests(unittest.TestCase):
    def test_three_frozen_new_runs_save_and_refuse_as_expected(self):
        for case in ('complete','incomplete','stopped'):
            expected=load(ROOT/'cases'/case/'expected.json');run=load(ROOT/'actual-final'/case/'run.json')
            self.assertEqual(run['workflow_status'],expected['workflow_status'])
            self.assertEqual(run['observed'],dict(replay_status=expected['replay_status'],evaluation_status=expected['evaluation_status']))
            self.assertTrue(all(s=='SAVED_AND_READ_BACK' for s in run['storage'].values()))
            backend=load(ROOT/'actual-final'/case/'CLI-run.json')['calls']
            self.assertEqual(backend,dict(replay=1,evaluation=1,execution=expected['execution_calls']))
            replay=actual(case,'replay');ev=actual(case,'evaluation');header=actual(case,'request');value=actual(case,'result')
            self.assertEqual(ev['replay_document_id'],_fp(replay));self.assertEqual(ev['header_id'],header['header_id'])
            self.assertEqual(value['evaluation_record_id'],ev['record_id'])
            if expected['reason']:
                self.assertEqual(ev['evaluation']['reasons'][0]['reason'],expected['reason'])
                self.assertIsNone(value['summary']['statistics'])
            else:
                self.assertEqual(value['summary']['terminal_accrual_equity'],expected['terminal_accrual_equity'])
                self.assertEqual(value['summary']['statistics']['period_accrual_growth'],expected['accrual_growth'])
            for record in (value,ev['evaluation'],run):
                for k in FLAGS:self.assertIs(record[k],False)
                self.assertIsNone(record['ranking']);self.assertIsNone(record['primary_pressure_id'])

    def test_backend_order_uses_saved_and_read_back_original_replay(self):
        replay=actual('complete','replay');evaluation=actual('complete','evaluation')['evaluation'];trace=[];r=request();before=deepcopy(r)
        with tempfile.TemporaryDirectory() as root:
            store=Journal(root);identity='ordered'
            def replay_backend(value):
                self.assertEqual(value,r['replay_input']);self.assertEqual(store.read(identity+'--request')['value']['request_id'],_fp(r))
                self.assertFalse(store.path(identity+'--replay').exists());trace.append('REQUEST_SAVED_READ_BEFORE_REPLAY')
                return deepcopy(replay)
            def metrics_backend(value):
                self.assertEqual(store.read(identity+'--replay')['value'],value['saved_result'])
                self.assertEqual(value['saved_result'],replay);trace.append('REPLAY_SAVED_READ_BEFORE_EVALUATION')
                return deepcopy(evaluation)
            with patch.object(flow,'_replay',side_effect=replay_backend) as rp,patch.object(flow,'_evaluate',side_effect=metrics_backend) as ev:
                out=flow.run_evaluated_replay(root,identity,r)
            self.assertEqual(out['workflow_status'],'COMPLETED_EVALUATED');rp.assert_called_once();ev.assert_called_once()
            self.assertEqual(r,before)
        save(ROOT/'test-evidence/ordering.json',dict(trace=trace,backend='CACHED_EXACT_NEW_RUN_RESULT_TEST_DOUBLES_NO_NEW_REPLAY',status=out['workflow_status']))

    def test_account_rights_reserve_latest_tokens_and_original_bytes_preserved(self):
        replay=actual('complete','replay');cp=replay['replay']['historical_checkpoint']['state'];evaluation=actual('complete','evaluation')['evaluation']
        account=evaluation['account'];self.assertEqual(account['saved_row'],cp['row'])
        for k in ('origin_initial_capital','external_flow','general_reserved_cash','latest_decision_id','latest_common_account_id',
                  'reviewed_evidence_tokens','opening_unavailable_shares'):self.assertEqual(account[k],cp[k])
        self.assertEqual(cp['origin_initial_capital'],'2230');self.assertEqual(cp['general_reserved_cash'],'100')
        self.assertEqual(cp['row']['shares'],dict(A='110',B='0',C='2'));self.assertEqual(cp['row']['settled_cash'],'1080')
        self.assertEqual(replay['replay']['last_execution']['fills'],[])
        proof=load(ROOT/'preservation.json');self.assertEqual(proof['before'],proof['after'])
        for v in load(ROOT/'intake.json')['originals']:self.assertEqual(info(PROJECT/v['path']),v)
        for case in ('complete','incomplete','stopped'):
            proof=load(ROOT/'actual-final'/case/'preservation.json');self.assertEqual(proof['before'],proof['after'])
            self.assertEqual(files(ROOT/'runs-final'/case),proof['after'])

    def test_existing_id_and_content_conflicts_do_not_replay_or_rewrite(self):
        root=ROOT/'runs-final/complete';before=files(root);r=request()
        with (patch.object(flow,'_replay',side_effect=AssertionError('REPLAY')),patch.object(flow,'_evaluate',side_effect=AssertionError('EVALUATION')),
             patch.object(Journal,'save',side_effect=AssertionError('SAVE'))):
            same=flow.run_evaluated_replay(root,'evaluated-complete',r)
            r['evaluation_at']='2026-01-12T17:00:00+08:00'
            conflict=flow.run_evaluated_replay(root,'evaluated-complete',r)
        self.assertEqual(same['workflow_status'],'OPERATION_EXISTS_READ_REQUIRED')
        self.assertEqual(conflict['workflow_status'],'OPERATION_ID_CONFLICT');self.assertEqual(before,files(root))
        save(ROOT/'test-evidence/id-reuse.json',dict(same=same,conflict=conflict,before=before,after=files(root)))

    def test_unknown_storage_at_all_four_stages_stops_and_READ_only_reports_saved_prefix(self):
        replay=actual('complete','replay');evaluation=actual('complete','evaluation')['evaluation'];persist=flow._persist;rows=[]
        spec=load(ROOT/'fault-specification.json')
        for stage in spec['stages']:
            with self.subTest(stage),tempfile.TemporaryDirectory() as root:
                def lose_ack(store,key,value):
                    result=persist(store,key,value)
                    return ('UNKNOWN',None,['SIMULATED_ACK_LOSS_AFTER_WRITE']) if key.endswith('--'+stage) else result
                with (patch.object(flow,'_replay',return_value=deepcopy(replay)) as rp,patch.object(flow,'_evaluate',return_value=deepcopy(evaluation)) as ev,
                     patch.object(flow,'_persist',side_effect=lose_ack)):
                    run=flow.run_evaluated_replay(root,'fault',request())
                self.assertEqual(run['workflow_status'],spec['expected_run']);self.assertEqual(run['storage'][stage],'UNKNOWN')
                self.assertEqual((rp.call_count,ev.call_count),((0,0) if stage=='request' else (1,0) if stage=='replay' else (1,1)))
                before=files(root)
                with (patch.object(flow,'_replay',side_effect=AssertionError('READ_REPLAY')),patch.object(flow,'_evaluate',side_effect=AssertionError('READ_EVALUATE')),
                     patch.object(Journal,'save',side_effect=AssertionError('READ_SAVE'))):
                    read=flow.read_evaluated_replay(root,'fault')
                self.assertEqual(read['workflow_status'],spec['read_final'] if stage=='result' else spec['read_prefix'])
                self.assertEqual(before,files(root))
                rows.append(dict(stage=stage,run=run,read=read,before=before,after=files(root),
                    backend='CACHED_TEST_DOUBLES_NO_NEW_REPLAY',calls=dict(replay=rp.call_count,evaluation=ev.call_count)))
        save(ROOT/'test-evidence/storage-unknown.json',rows)

    def test_missing_or_cross_stage_corruption_is_not_recomputed_or_repaired(self):
        rows=[]
        for spec in load(ROOT/'read-counterexamples.json'):
            with self.subTest(spec['name']),tempfile.TemporaryDirectory() as root:
                for p in (ROOT/'runs-final/complete').glob('*.json'):shutil.copyfile(p,Path(root)/p.name)
                keys=flow._keys('evaluated-complete');m=spec['mutation']
                if m=='REMOVE_TEMP_EVALUATION_FILE':(Path(root)/(keys['evaluation']+'.json')).unlink()
                elif m=='REMOVE_TEMP_RESULT_FILE':(Path(root)/(keys['result']+'.json')).unlink()
                elif m=='COPY_DIFFERENT_OPERATION_EVALUATION_VALUE':write_value(root,keys['evaluation'],actual('incomplete','evaluation'))
                elif m=='CHANGE_GROWTH_AND_RESIGN_RESULT_ONLY':
                    v=actual('complete','result');v['summary']['statistics']['period_accrual_growth']='999';v['result_id']=_fp({k:x for k,x in v.items() if k!='result_id'})
                    write_value(root,keys['result'],v)
                elif m=='CHANGE_SAVED_REPLAY_STATUS_WITHOUT_REBINDING':
                    v=actual('complete','replay');v['replay']['status']='STOPPED_CANDIDATE_GATE';write_value(root,keys['replay'],v)
                elif m=='CHANGE_EVALUATION_RECORD_TIME_AND_RESIGN':
                    v=actual('complete','evaluation');v['evaluation_at']='2026-01-12T17:00:00+08:00';v['record_id']=_fp({k:x for k,x in v.items() if k!='record_id'})
                    write_value(root,keys['evaluation'],v)
                before=files(root)
                with (patch.object(flow,'_replay',side_effect=AssertionError('REPLAY')),patch.object(flow,'_evaluate',side_effect=AssertionError('EVALUATE')),
                     patch.object(Journal,'save',side_effect=AssertionError('SAVE'))):
                    out=flow.read_evaluated_replay(root,'evaluated-complete')
                self.assertEqual(out['workflow_status'],spec['expected']);self.assertEqual(before,files(root));self.assertIsNone(out['evaluation'])
                rows.append(dict(name=spec['name'],actual=out,before=before,after=files(root)))
        save(ROOT/'test-evidence/read-refusals.json',rows)

    def test_fresh_READ_never_imports_evaluator_or_engine_and_preserves_refused_status(self):
        for case in ('complete','incomplete','stopped'):
            run=load(ROOT/'actual-final'/case/'run.json')
            for fmt in ('read','text'):
                trace=load(ROOT/'actual-final'/case/('CLI-'+fmt+'.json'))
                self.assertEqual(trace['calls'],dict(replay=0,evaluation=0,execution=0));self.assertFalse(trace['stderr'])
                self.assertEqual(trace['guard'],'FRESH_READ_NO_NUMERIC_NO_WRITE_NO_NETWORK')
            read=json.loads(load(ROOT/'actual-final'/case/'CLI-read.json')['stdout'])
            self.assertEqual(read['workflow_status'],'READ_ONLY');self.assertEqual(read['operation'],run['operation'])
            self.assertEqual(read['evaluation'],run['evaluation']);self.assertEqual(read['observed'],run['observed'])
        refused=command('READ',ROOT/'runs-final/complete','evaluated-complete',ROOT/'cases/complete/input.json')
        self.assertEqual(refused['exit_code'],2);self.assertIn('READ does not accept --input',refused['stderr'])
        self.assertEqual(refused['calls'],dict(replay=0,evaluation=0,execution=0))
        save(ROOT/'test-evidence/read-input-refused.json',refused)

    def test_preflight_rejects_real_source_or_missing_explicit_fields_without_writes(self):
        rows=[]
        for name in ('real-source','missing-time','invalid-id'):
            with tempfile.TemporaryDirectory() as root:
                r=request();identity='preflight'
                if name=='real-source':r['replay_input']['origin_ledger']['sources']['fixture']['kind']='OFFICIAL_ARCHIVE'
                elif name=='missing-time':r.pop('evaluation_at')
                else:identity='../escape'
                before=deepcopy(r)
                with (patch.object(flow,'_replay',side_effect=AssertionError('REPLAY')),patch.object(flow,'_evaluate',side_effect=AssertionError('EVALUATE')),
                     patch.object(Journal,'save',side_effect=AssertionError('SAVE'))):
                    out=flow.run_evaluated_replay(root,identity,r)
                self.assertEqual(out['workflow_status'],'INPUT_REFUSED');self.assertEqual(list(Path(root).iterdir()),[]);self.assertEqual(r,before)
                rows.append(dict(name=name,request_id=_fp(r),actual=out))
        save(ROOT/'test-evidence/preflight.json',rows)


if __name__=='__main__':unittest.main()
