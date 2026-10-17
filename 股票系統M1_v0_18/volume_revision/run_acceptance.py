"""Actual new/old producer versions in an independent research database."""
from copy import deepcopy
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'volume_revision';OUT=HERE/'output'
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(HERE))
from analysis_store import AnalysisStore
from contracts import fingerprint
from compare import compare_results
from saved_viewer import write_html

SOURCE=ROOT/'workflow/output/分析流程_v0_10.sqlite3'


def run(database):
    database=database.resolve()
    originals=[SOURCE,ROOT/'persistence/output/研究資料_v0_9.sqlite3']
    protected=[p for db in originals for p in [db]+[Path(str(db)+s) for s in ['-journal','-wal','-shm']]]
    assert all(database!=p and not (database.exists() and p.exists() and os.path.samefile(database,p)) for p in protected),'Independent database path required'
    assert all(not Path(str(SOURCE)+s).exists() for s in ['-journal','-wal','-shm']),'Source must be a closed, recovered database; never copy active sidecars'
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}
    source=AnalysisStore(SOURCE);legacy=[source.load(row['record_id']) for row in source.list_records()]
    assert len(legacy)==3
    if not database.exists():
        database.parent.mkdir(parents=True,exist_ok=True)
        with SOURCE.open('rb') as src,database.open('xb') as dst:shutil.copyfileobj(src,dst)
    store=AnalysisStore(database)
    assert all(store.load(b['record_id'])==b for b in legacy)
    calls=[];cases=[];pairs=[]
    with tempfile.TemporaryDirectory(prefix='unit-version-acceptance-') as tmp:
        temp=Path(tmp);counter=0
        def workflow(payload):
            nonlocal counter
            counter+=1;inp=temp/f'input-{counter}.json';out=temp/f'output-{counter}.json'
            inp.write_text(json.dumps(payload,ensure_ascii=False))
            cmd=[sys.executable,str(ROOT/'src/workflow_cli.py'),'--db',str(database),'--input',str(inp),'--output',str(out)]
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            assert p.returncode==0,p.stdout+p.stderr
            receipt=json.loads(p.stdout);reply=json.loads(out.read_text())
            calls.append(dict(operation=payload['operation'],process_id=receipt['process_id'],status=reply['status'],store_status=reply.get('store_status')))
            return reply
        for old in legacy:
            req=dict(schema_version='analysis-workflow/1.0',operation='RUN',job=old['request'],evidence=old['evidence'],reason='v0.12成交量來源文字修正；候選策略與數值不變')
            reply=workflow(req)
            saved=workflow(dict(schema_version='analysis-workflow/1.0',operation='READ',record_id=reply['record_id'],include_bundle=True))['saved_bundle']
            comparison=compare_results(old['result'],saved['result'],old['request']['source']['volume_unit'])
            assert old['request']==saved['request'] and old['evidence']==saved['evidence']
            old_read=workflow(dict(schema_version='analysis-workflow/1.0',operation='READ',record_id=old['record_id'],include_bundle=True))['saved_bundle']
            assert old_read==old
            lookup=workflow(dict(schema_version='analysis-workflow/1.0',operation='LOOKUP',job=old['request'],evidence=old['evidence']))
            assert lookup['status']=='MULTIPLE_VERSION_MATCHES'
            assert {m['record_id'] for m in lookup['matches']}=={old['record_id'],saved['record_id']}
            cases.append(comparison);pairs.append(dict(code=old['request']['code'],price_mode=old['request']['price_mode'],old_record_id=old['record_id'],new_record_id=saved['record_id'],lookup_status=lookup['status']))
        # Additional original two-stock Raw/Adjusted cases, without changing
        # the historical source DB or broadening the saved demo universe.
        for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
            q=json.loads((ROOT/'data/6488_analysis_job.json').read_text());q['price_mode']=mode
            baseline=json.loads((ROOT/'output'/f'6488_{mode}_ANALYSIS.json').read_text())
            inp=temp/f'6488-{mode}.json';out=temp/f'6488-{mode}-result.json';inp.write_text(json.dumps(q))
            p=subprocess.run([sys.executable,str(ROOT/'src/analysis_jobs.py'),'--input',str(inp),'--output',str(out)],capture_output=True,text=True,timeout=60)
            assert p.returncode==0,p.stdout+p.stderr
            cases.append(compare_results(baseline,json.loads(out.read_text()),q['source']['volume_unit']))
        before=store.stats()
        duplicate=workflow(dict(schema_version='analysis-workflow/1.0',operation='RUN',job=legacy[-1]['request'],evidence=legacy[-1]['evidence'],reason='v0.12重跑去重驗收'))
        assert duplicate['store_status']=='EXISTING' and store.stats()==before
    assert all(store.load(b['record_id'])==b for b in legacy)
    stats=store.stats();assert (stats['analyses'],stats['records'],stats['snapshots'])==(6,6,1490)
    html=ROOT/'成交量版本比較瀏覽.html';db_hash=hashlib.sha256(database.read_bytes()).hexdigest()
    export=write_html(database,html)
    assert hashlib.sha256(database.read_bytes()).hexdigest()==db_hash
    for rel,digest in hashes.items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest
    return dict(schema_version='volume-origin-revision-acceptance/1.0',status='PASS',producer_before='structure-0.2-research',producer_after='structure-0.3-research',
                numeric_comparisons=cases,compared_snapshots=sum(x['snapshots'] for x in cases),saved_pairs=pairs,old_full_bundles_unchanged=True,
                lookup_requires_explicit_version=True,repeat_deduplicated=True,stats=stats,export=export,export_db_sha256=db_hash,
                historical_database_sha256=hashes,historical_databases_byte_identical=True,calls=calls,
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED',browser_rendering='NOT_TESTED')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=OUT/'單位修正並存_v0_12.sqlite3');a=p.parse_args()
    OUT.mkdir(exist_ok=True)
    result=run(a.db)
    (OUT/'成交量單位與新舊版本驗收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in {'numeric_comparisons','calls'}},ensure_ascii=False))
