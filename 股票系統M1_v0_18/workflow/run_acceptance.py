"""Three complete real workflows, separate-process reads and reply-loss recovery."""
from copy import deepcopy
from pathlib import Path
import argparse,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'workflow';OUT=HERE/'output';REQ=HERE/'requests'
sys.path.insert(0,str(ROOT/'src'))
from contracts import fingerprint
from analysis_store import AnalysisStore
from analysis_workflow import SCHEMA


def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2))


def main():
    from structure import VERSION as structure_version
    if structure_version != 'structure-0.2-research':
        print(json.dumps(dict(status='HISTORICAL_RUNNER_VERSION_MISMATCH', expected='structure-0.2-research', actual=structure_version, next='Use volume_revision/run_acceptance.py; historical outputs and databases were not touched')))
        return 2
    parser=argparse.ArgumentParser();parser.add_argument('--db',default=str(OUT/'分析流程_v0_10.sqlite3'));args=parser.parse_args()
    db=Path(args.db);OUT.mkdir(exist_ok=True);REQ.mkdir(exist_ok=True);calls=[]
    def invoke(name,payload,output,*,create=False,expected_exit=0):
        inp=REQ/(name+'.json');write(inp,payload)
        cmd=[sys.executable,str(ROOT/'src/workflow_cli.py'),'--input',str(inp),'--db',str(db),'--output',str(output)]
        if create:cmd.append('--create')
        p=subprocess.run(cmd,capture_output=True,text=True)
        try:receipt=json.loads(p.stdout)
        except ValueError:raise RuntimeError(p.stdout+p.stderr) from None
        calls.append(dict(case=name,exit_code=p.returncode,process_id=receipt.get('process_id'),status=receipt.get('status'),
                          commit_status=receipt.get('commit_status'),stage=receipt.get('stage')))
        assert p.returncode==expected_exit,(p.stdout,p.stderr)
        return receipt
    q8069=json.loads((ROOT/'data/8069_analysis_job.json').read_text())
    e8069=json.loads((ROOT/'persistence/fixtures/8069_事件證據.json').read_text())
    q1101=json.loads((ROOT/'data_audit/1101_analysis_job.json').read_text())
    e1101=json.loads((ROOT/'persistence/fixtures/1101_仍待核實事件證據.json').read_text())
    cases=[]
    with tempfile.TemporaryDirectory(prefix='workflow_acceptance_') as tmp:
        temp=Path(tmp)
        for code,mode,q,e,baseline_path in [
            ('8069','ADJUSTED_CANDIDATE',q8069,e8069,ROOT/'output/8069_ADJUSTED_CANDIDATE_ANALYSIS.json'),
            ('8069','RAW_CANDIDATE',q8069,e8069,ROOT/'output/8069_RAW_CANDIDATE_ANALYSIS.json'),
            ('1101','RAW_CANDIDATE',q1101,e1101,ROOT/'data_audit/output/1101_RAW_ANALYSIS.json')]:
            name=code+'_'+mode;q=deepcopy(q);q['price_mode']=mode
            payload=dict(schema_version=SCHEMA,operation='RUN',job=q,evidence=e,reason='v0.10完整工作流程驗收')
            before_inputs=fingerprint(payload);out=OUT/(name+'_流程回覆.json');lost_reply=code=='1101'
            if lost_reply:
                # Save succeeds, but exporting the reply to a missing directory
                # fails. This is a real CLI I/O failure after commit, not a mock.
                missing=temp/'missing-reply-directory'/'reply.json'
                receipt=invoke(name+'_回覆失敗',payload,missing,create=True,expected_exit=3)
                assert receipt['commit_status']=='COMMITTED' and receipt['stage']=='EXPORT'
                lookup=dict(schema_version=SCHEMA,operation='LOOKUP',job=q,evidence=e)
                lookup_out=OUT/(name+'_查回紀錄.json');invoke(name+'_查回',lookup,lookup_out)
                found=json.loads(lookup_out.read_text());assert found['status']=='FOUND'
                assert found['matches'][0]['record_id']==receipt['record_id']
                stats_before=AnalysisStore(db).stats()
                receipt=invoke(name,payload,out,create=True)
                assert receipt['store_status']=='EXISTING' and AnalysisStore(db).stats()==stats_before
            else:receipt=invoke(name,payload,out,create=True)
            reply=json.loads(out.read_text());assert fingerprint(payload)==before_inputs
            assert reply['action_qualification']=='NOT_EVALUATED' and reply['snapshot']['as_of']==q['candles'][-1]['date']
            baseline=json.loads(baseline_path.read_text());read_payload=dict(schema_version=SCHEMA,operation='READ',record_id=reply['record_id'],include_bundle=True)
            read_out=temp/(name+'_read.json');read_receipt=invoke(name+'_讀回',read_payload,read_out)
            saved=json.loads(read_out.read_text())['saved_bundle']
            assert saved['request']==q and saved['result']==baseline and saved['evidence']==e
            assert receipt['process_id']!=read_receipt['process_id']
            # Read a historical, exact date through the same workflow handler.
            i=min(20,len(q['candles'])-1);dt=q['candles'][i]['date']
            historic=dict(schema_version=SCHEMA,operation='READ',record_id=reply['record_id'],as_of=dt)
            hist_out=temp/'historical.json';invoke(name+'_歷史日期',historic,hist_out)
            snap=json.loads(hist_out.read_text())['snapshot']
            assert snap['structure']==baseline['components']['structure']['snapshots'][i]
            assert snap['daily_ma']==baseline['components']['daily_ma']['snapshots'][i]
            if code=='1101':
                assert saved['request']['corporate_actions']['records']==[]
                assert saved['result']['shared_input']['corporate_action_coverage']=='UNVERIFIED'
                assert saved['evidence']['records'][0]['staging']['approved_engine_events']==[]
            cases.append(dict(code=code,price_mode=mode,bars=len(q['candles']),record_id=reply['record_id'],analysis_id=reply['analysis_id'],
                              result_fingerprint=fingerprint(baseline),full_result_same=True,historical_snapshot_same=True,
                              evidence_unchanged=True,writer_process=receipt['process_id'],reader_process=read_receipt['process_id'],
                              export_failure_recovered=lost_reply))
        # An ordinary rerun must also deduplicate, independent of export failure.
        payload=json.loads((REQ/'8069_ADJUSTED_CANDIDATE.json').read_text());before=AnalysisStore(db).stats()
        again=invoke('8069_正常重跑',payload,temp/'repeat.json',create=True)
        assert again['store_status']=='EXISTING' and AnalysisStore(db).stats()==before
        assert again['record_id']==cases[0]['record_id']
    stats=AnalysisStore(db).stats();assert len({x['record_id'] for x in cases})==3
    assert stats['analyses']==3 and stats['records']==3 and stats['snapshots']==745
    report=dict(schema_version='workflow-acceptance/1.0',status='PASS',database=db.name,cases=cases,
                separate_raw_adjusted_records=True,normal_rerun_deduplicated=True,committed_but_unexported_reply_found=True,
                unverified_events_not_promoted=True,stats=stats,calls=calls,
                scope='Local headless workflow; no HTTP service, mobile UI, formal signals or trading qualification')
    write(OUT/'單一分析保存流程驗收.json',report)
    print(json.dumps(dict(status=report['status'],cases=len(cases),distinct_worker_processes=len({c['process_id'] for c in calls}),stats=stats),ensure_ascii=False))

if __name__=='__main__':raise SystemExit(main())
