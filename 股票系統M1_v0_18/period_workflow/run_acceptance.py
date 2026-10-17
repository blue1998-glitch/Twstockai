"""Actual headless RUN/save/read/lookup on twelve existing research requests."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from contracts import fingerprint
from period_store import PeriodStore
from period_viewer import export
from period_workflow import SCHEMA

OUT=ROOT/'period_workflow/output'
COMMANDS=ROOT/'period_workflow/commands'
OLD=ROOT/'period_persistence/output/週月結果庫'
STORE=OUT/'背景流程結果庫'


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def tree(path):return {str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def main():
    OUT.mkdir(parents=True,exist_ok=True);COMMANDS.mkdir(parents=True,exist_ok=True)
    old_before=tree(OLD)
    protected=[ROOT/'workflow/output/分析流程_v0_10.sqlite3',ROOT/'persistence/output/研究資料_v0_9.sqlite3',
               ROOT/'volume_revision/output/單位修正並存_v0_12.sqlite3',ROOT/'價格結構重播.html',
               ROOT/'已保存分析瀏覽.html',ROOT/'成交量版本比較瀏覽.html',ROOT/'週月保存結果瀏覽.html']
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    cases=[];workers=[]

    def cli(command,name,*,create=False,fail_output=False):
        inp=COMMANDS/(name+'.json');output=OUT/(name+'_RESPONSE.json');write(inp,command)
        if fail_output:output=OUT/'故意不存在的輸出目錄'/(name+'.json')
        assert not fail_output or not output.parent.exists()
        args=[sys.executable,str(ROOT/'src/period_workflow_cli.py'),'--store',str(STORE),'--input',str(inp),'--output',str(output)]
        if create:args.append('--create')
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
        if fail_output:
            assert p.returncode==3,(p.stdout,p.stderr)
            error=json.loads(p.stderr);assert error['stage']=='EXPORT' and error['commit_status']=='COMMITTED'
            write(OUT/(name+'_EXPECTED_ERROR.json'),error);workers.append(error);return error
        assert p.returncode==0,(p.stdout,p.stderr)
        receipt=json.loads(p.stdout);workers.append(receipt)
        return json.loads(output.read_text())

    for i,meta in enumerate(PeriodStore(OLD).list()):
        original=PeriodStore(OLD).load(meta['analysis_id']);q=original['request'];r=original['result']
        name=q['code']+'_'+q['price_mode']+'_'+q['as_of']
        command=dict(schema_version=SCHEMA,operation='RUN',job=q,reason=original['reason'],include_bundle=True)
        # Reuse the immutable original reason deliberately: exact record compatibility, no new rule claims.
        if i==0:
            lost=cli(command,name+'_RUN_LOST_RESPONSE',create=True,fail_output=True)
            assert lost['analysis_id']==r['analysis_id']
        else:
            first=cli(command,name+'_RUN',create=False)
            assert first['saved_bundle']==original
        response=cli(command,name+'_RUN_RETRY')
        assert response['store_status']=='DUPLICATE' and response['commit_status']=='COMMITTED'
        assert response['saved_bundle']==original and response['snapshot']==r['snapshot']
        read=cli(dict(schema_version=SCHEMA,operation='READ',analysis_id=r['analysis_id'],include_bundle=True),name+'_READ')
        assert read['commit_status']=='NOT_APPLICABLE' and read['saved_bundle']==original
        filters={k:q[k] for k in ('code','exchange','price_mode','as_of')}
        filters.update(rule_version=r['snapshot']['rule_version'],aggregation_version=r['snapshot']['aggregation_version'],
                       adapter_version=r['adapter_version'],request_fingerprint=fingerprint(q))
        lookup=cli(dict(schema_version=SCHEMA,operation='LOOKUP',filters=filters),name+'_LOOKUP')
        assert lookup['status']=='FOUND' and len(lookup['matches'])==1 and lookup['matches'][0]['analysis_id']==r['analysis_id']
        cases.append(dict(case=name,code=q['code'],exchange=q['exchange'],price_mode=q['price_mode'],as_of=q['as_of'],
                          analysis_id=r['analysis_id'],record_fingerprint=original['record_fingerprint'],result_fingerprint=fingerprint(r),
                          snapshot_fingerprint=fingerprint(r['snapshot'])))
    missing=cli(dict(schema_version=SCHEMA,operation='LOOKUP',filters=dict(code='1101',exchange='TWSE',price_mode='RAW_CANDIDATE',as_of='2026-09-29')),'未保存日_LOOKUP')
    assert missing['status']=='NOT_FOUND' and missing['matches']==[]
    assert len(PeriodStore(STORE).list())==12
    assert tree(STORE)==old_before  # Newly calculated, independently saved files, byte-identical old contract.
    before_export=tree(STORE)
    export(STORE,OUT/'週月背景流程結果瀏覽.html')
    assert (OUT/'週月背景流程結果瀏覽.html').read_bytes()==(ROOT/'週月保存結果瀏覽.html').read_bytes()
    assert tree(STORE)==before_export and tree(OLD)==old_before
    assert {str(p.relative_to(ROOT)):sha(p) for p in protected}==before
    report=dict(status='PASS',cases=cases,explicit_runs=24,duplicate_retries=12,read_workers=12,lookup_workers=13,
                expected_export_failures=1,worker_processes=len(workers),distinct_processes=len({w['process_id'] for w in workers}),
                old_store_unchanged=True,independent_store_records=12,store_files_identical_to_v0_14=True,
                exported_html_identical_to_v0_14=True,read_export_never_write=True,protected_files=before,
                engine_import_block_proof='tests/test_period_workflow.py',browser_rendering='NOT_TESTED',mobile_touch='NOT_TESTED',
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
    write(OUT/'週月背景流程實算驗收.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
