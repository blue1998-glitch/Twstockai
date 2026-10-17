"""Real saved period-result import/reopen/read/export acceptance; no network."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from contracts import fingerprint
from period_store import PeriodStore
from period_viewer import export

OUT = ROOT/'period_persistence/output'
COMMANDS = ROOT/'period_persistence/commands'
STORE = OUT/'週月結果庫'
REASON = 'v0.14 獨立保存驗收；來源與候選規則沿用 v0.13，未提高認證'


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args):
    p=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return json.loads(p.stdout)


def main():
    OUT.mkdir(parents=True,exist_ok=True);COMMANDS.mkdir(parents=True,exist_ok=True)
    protected=[ROOT/'workflow/output/分析流程_v0_10.sqlite3',ROOT/'persistence/output/研究資料_v0_9.sqlite3',
               ROOT/'volume_revision/output/單位修正並存_v0_12.sqlite3',
               ROOT/'價格結構重播.html',ROOT/'已保存分析瀏覽.html',ROOT/'成交量版本比較瀏覽.html']
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    cases=[];workers=[]
    for path in sorted((ROOT/'period_analysis/requests').glob('*.json')):
        q=json.loads(path.read_text());latest=json.loads((ROOT/'period_analysis/output'/(path.stem+'_PERIOD.json')).read_text())
        for date in ('2026-08-31','2026-09-30'):
            case=path.stem+'_'+date
            if date==q['as_of']:request=q;result=latest
            else:
                request={**q,'as_of':date};request_path=COMMANDS/(case+'_RUN_REQUEST.json');result_path=OUT/(case+'_RUN_RESULT.json')
                write(request_path,request)
                # This is an explicit historical RUN, never a read or viewer calculation.
                receipt=run([ROOT/'src/period_jobs.py','--input',request_path,'--output',result_path]);workers.append(receipt)
                result=json.loads(result_path.read_text())
            command=dict(schema_version='period-store-command/1.0',operation='IMPORT',request=request,result=result,reason=REASON)
            command_path=COMMANDS/(case+'_IMPORT.json');write(command_path,command)
            receipt_path=OUT/(case+'_IMPORT_RECEIPT.json')
            receipt=run([ROOT/'src/period_store_cli.py','--store',STORE,'--input',command_path,'--output',receipt_path]);workers.append(receipt)
            assert receipt['status'] in ('SAVED','DUPLICATE') and receipt['commit_status']=='COMMITTED'
            duplicate=run([ROOT/'src/period_store_cli.py','--store',STORE,'--input',command_path,'--output',receipt_path]);workers.append(duplicate)
            assert duplicate['status']=='DUPLICATE'
            read_command=COMMANDS/(case+'_READ.json');write(read_command,dict(schema_version='period-store-command/1.0',operation='READ',analysis_id=result['analysis_id']))
            read_path=OUT/(case+'_READBACK.json')
            worker=run([ROOT/'src/period_store_cli.py','--store',STORE,'--input',read_command,'--output',read_path]);workers.append(worker)
            read=json.loads(read_path.read_text())['value']
            assert read['request']==request and read['result']==result
            f={k:request[k] for k in ('code','exchange','price_mode','as_of')}
            matches=PeriodStore(STORE).lookup(**f,rule_version=result['snapshot']['rule_version'],
                     aggregation_version=result['snapshot']['aggregation_version'],adapter_version=result['adapter_version'])
            assert len(matches)==1 and matches[0]['analysis_id']==result['analysis_id']
            cases.append(dict(case=case,**f,analysis_id=result['analysis_id'],result_fingerprint=fingerprint(result),
                              snapshot_fingerprint=fingerprint(result['snapshot']),record_fingerprint=read['record_fingerprint']))
    store=PeriodStore(STORE);before_read={p.name:sha(p) for p in STORE.iterdir()}
    assert len(store.list())==12
    assert store.lookup(code='1101',exchange='TWSE',price_mode='RAW_CANDIDATE',as_of='2026-09-29')==[]
    exported=export(STORE,ROOT/'週月保存結果瀏覽.html')
    assert exported['records']==12
    assert {p.name:sha(p) for p in STORE.iterdir()}==before_read
    assert {str(p.relative_to(ROOT)):sha(p) for p in protected}==before
    report=dict(status='PASS',cases=cases,committed_records=12,duplicates_verified=12,reopened_cli_readbacks=12,
                explicit_historical_runs=6,worker_processes=len(workers),distinct_worker_pids=len({w['process_id'] for w in workers}),
                store_files_unchanged_by_read_export=True,old_artifacts_unchanged=before,
                engine_import_block_test='tests/test_period_store.py',browser_rendering='NOT_TESTED',mobile_touch='NOT_TESTED',
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
    write(OUT/'週月保存讀回驗收.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
