"""Actual process-separated persistence/readback of existing research results.

No web, engine UI or network. Controlled source-label/evidence revisions are
storage tests; they do not claim an official data correction or new strategy.
"""
from copy import deepcopy
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'persistence';OUT=HERE/'output';FIX=HERE/'fixtures'
sys.path.insert(0,str(ROOT/'src'))
from contracts import fingerprint
from analysis_jobs import run_analysis_job


def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2))


def main():
    from structure import VERSION as structure_version
    if structure_version != 'structure-0.2-research':
        print(json.dumps(dict(status='HISTORICAL_RUNNER_VERSION_MISMATCH', expected='structure-0.2-research', actual=structure_version, next='Use volume_revision/run_acceptance.py; historical outputs and databases were not touched')))
        return 2
    parser=argparse.ArgumentParser();parser.add_argument('--db',default=str(OUT/'研究資料_v0_9.sqlite3'));args=parser.parse_args()
    db=Path(args.db);OUT.mkdir(exist_ok=True);FIX.mkdir(exist_ok=True);calls=[]
    def invoke(command,*extra):
        cmd=[sys.executable,str(ROOT/'src/store_cli.py'),command,'--db',str(db),*map(str,extra)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        try:r=json.loads(p.stdout)
        except ValueError:raise RuntimeError(p.stdout+p.stderr) from None
        calls.append(dict(command=command,exit_code=p.returncode,process_id=r.get('process_id'),status=r.get('status')))
        if p.returncode:raise RuntimeError(r)
        return r
    if not db.exists():invoke('init')
    else:invoke('recover')
    q=json.loads((ROOT/'data/8069_analysis_job.json').read_text());r=json.loads((ROOT/'output/8069_ADJUSTED_CANDIDATE_ANALYSIS.json').read_text())
    audit=json.loads((ROOT/'data_audit/output/資料日期與新樣本驗收.json').read_text())
    e=dict(schema_version='analysis-evidence/1.0',code='8069',coverage_status='UNVERIFIED',
           records=[dict(kind='INDIVIDUAL_REVIEWED_CASH_EVENTS',records=q['corporate_actions']['records'],complete_period_coverage='UNVERIFIED'),
                    dict(kind='EXTERNAL_CALENDAR_AUDIT',audit=next(a for a in audit['audits'] if a['code']=='8069'))])
    e1=FIX/'8069_事件證據.json';write(e1,e)
    qpath=ROOT/'data/8069_analysis_job.json';rpath=ROOT/'output/8069_ADJUSTED_CANDIDATE_ANALYSIS.json'
    def save(qf,rf,ef,reason):return invoke('save','--request',qf,'--result',rf,'--evidence',ef,'--reason',reason)
    first=save(qpath,rpath,e1,'v0.9真實研究樣本首次保存')
    before=invoke('stats');repeat=save(qpath,rpath,e1,'重跑去重驗收');after=invoke('stats')
    count_keys=['objects','analyses','records','snapshots'];assert all(before[k]==after[k] for k in count_keys)
    assert repeat['status']=='EXISTING' and repeat['record_id']==first['record_id']
    # Read in a new process, then retain a reusable export with exact JSON meaning.
    loaded_path=OUT/'8069_跨程序讀回.json'
    read_receipt=invoke('load','--record-id',first['record_id'],'--output',loaded_path)
    loaded=json.loads(loaded_path.read_text());assert loaded['request']==q and loaded['result']==r and loaded['evidence']==e
    assert first['process_id']!=read_receipt['process_id']
    # Actual engine re-run, changing only a clearly labeled controlled metadata
    # revision. No quote is invented; this is not an official source correction.
    revised=deepcopy(q);revised['source']['controlled_storage_revision']='SOURCE_LABEL_TEST_1_NOT_OFFICIAL_CORRECTION'
    revised_result=run_analysis_job(revised)
    q2=FIX/'8069_受控來源版本工作單.json';r2=FIX/'8069_受控來源版本結果.json';write(q2,revised);write(r2,revised_result)
    version=save(q2,r2,e1,'受控來源標籤版本測試；未修改行情，非官方修訂')
    assert version['analysis_id']!=first['analysis_id']
    e_new=deepcopy(e);e_new['controlled_evidence_revision']='EVIDENCE_CONTEXT_TEST_2_NO_VERIFICATION_UPGRADE'
    e2=FIX/'8069_補充證據版本.json';write(e2,e_new)
    supplemented=save(qpath,rpath,e2,'證據版本保留測試；不升級驗證狀態')
    assert supplemented['analysis_id']==first['analysis_id'] and supplemented['record_id']!=first['record_id']
    # The unverified new stock must remain unverified after a process restart.
    new_q=ROOT/'data_audit/1101_analysis_job.json';new_r=ROOT/'data_audit/output/1101_RAW_ANALYSIS.json'
    staged=json.loads((ROOT/'event_audit/output/事件證據與啟用檢查.json').read_text())
    item=next(x for x in staged['corporate_actions'] if x['fact']['code']=='1101')
    unknown=dict(schema_version='analysis-evidence/1.0',code='1101',coverage_status='UNVERIFIED',records=[item])
    eu=FIX/'1101_仍待核實事件證據.json';write(eu,unknown)
    unverified=save(new_q,new_r,eu,'保存待核實事件，禁止自動升級')
    pu=OUT/'1101_跨程序讀回.json';ur=invoke('load','--record-id',unverified['record_id'],'--output',pu);u=json.loads(pu.read_text())
    assert u['evidence']==unknown and u['result']==json.loads(new_r.read_text())
    assert u['request']['corporate_actions']['records']==[] and u['result']['shared_input']['corporate_action_coverage']=='UNVERIFIED'
    assert u['evidence']['records'][0]['staging']['approved_engine_events']==[]
    # Old data is read again after both types of revision have been inserted.
    with tempfile.TemporaryDirectory(prefix='store_acceptance_') as tmp:
        path=Path(tmp)/'old.json';invoke('load','--record-id',first['record_id'],'--output',path)
        old=json.loads(path.read_text());assert old==loaded
        dt=q['candles'][-1]['date'];snap_path=Path(tmp)/'snapshot.json'
        invoke('snapshot','--record-id',first['record_id'],'--as-of',dt,'--output',snap_path)
        snap=json.loads(snap_path.read_text());assert snap['structure']==r['components']['structure']['snapshots'][-1]
        assert snap['daily_ma']==r['components']['daily_ma']['snapshots'][-1]
        # Revised run and evidence association are each read by a fresh process.
        for receipt,expected_q,expected_r,expected_e in [(version,revised,revised_result,e),(supplemented,q,r,e_new)]:
            path=Path(tmp)/'version.json';invoke('load','--record-id',receipt['record_id'],'--output',path)
            got=json.loads(path.read_text());assert (got['request'],got['result'],got['evidence'])==(expected_q,expected_r,expected_e)
    stats=invoke('stats');listed=invoke('list','--code','8069')
    assert first['record_id'] in [x['record_id'] for x in listed['records']]
    assert stats['sqlite_integrity']=='ok'
    proof=dict(schema_version='persistence-acceptance/1.0',status='PASS',database=db.name,
               cases=[dict(code='8069',bars=len(q['candles']),record_id=first['record_id'],analysis_id=first['analysis_id'],
                           request_fingerprint=fingerprint(q),result_fingerprint=fingerprint(r),readback_same=True,
                           writer_process=first['process_id'],reader_process=read_receipt['process_id']),
                      dict(code='1101',bars=len(u['request']['candles']),record_id=unverified['record_id'],analysis_id=unverified['analysis_id'],
                           result_fingerprint=fingerprint(u['result']),readback_same=True,coverage='UNVERIFIED',
                           writer_process=unverified['process_id'],reader_process=ur['process_id'])],
               repeated_import_count_unchanged=True,source_label_revision_preserved=True,evidence_revision_preserved=True,old_record_unchanged=True,
               snapshot_readback_same=True,unverified_event_not_promoted=True,stats={k:stats[k] for k in ['schema_version','sqlite_integrity',*count_keys]},
               controlled_revision_notice='Source/evidence revision labels are controlled persistence tests, not new official corrections or strategies',calls=calls,
               scope='Local file prototype; no holdings ledger, formal signal store, cloud synchronization or UI connection')
    write(OUT/'獨立保存與跨程序讀回驗收.json',proof)
    print(json.dumps(dict(status=proof['status'],cases=len(proof['cases']),distinct_worker_processes=len(set(c['process_id'] for c in calls)),stats=proof['stats']),ensure_ascii=False))

if __name__=='__main__':raise SystemExit(main())
