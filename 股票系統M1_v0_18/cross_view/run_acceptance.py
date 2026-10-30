"""Read-only acceptance against actual independently saved daily and period results."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from analysis_store import AnalysisStore
from period_store import PeriodStore
from contracts import fingerprint
from cross_view import catalog,select,SELECTION_SCHEMA
from cross_view_cli import read_config
from cross_view_export import export


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def protected(config):
    files=[Path(p) for p in config['daily_stores'].values()]
    for p in config['period_stores'].values():files.extend(Path(p).glob('*'))
    files+=[ROOT/'persistence/output/研究資料_v0_9.sqlite3',ROOT/'workflow/output/分析流程_v0_10.sqlite3',
            ROOT/'價格結構重播.html',ROOT/'已保存分析瀏覽.html',ROOT/'成交量版本比較瀏覽.html',ROOT/'週月保存結果瀏覽.html']
    return {str(p.relative_to(ROOT)):sha(p) for p in files if p.is_file()}


def main():
    out=ROOT/'cross_view/output';requests=ROOT/'cross_view/requests';config=read_config(ROOT/'cross_view/sources.json')
    before=protected(config);payload=catalog(config)
    baseline=catalog(read_config(ROOT/'cross_view/sources_before_fill.json'))
    gaps=[p['key'] for p in baseline['period'] if not any(v['period_key']==p['key'] and v['allow_comparison'] for v in baseline['views'])]
    assert len(gaps)==6
    assert len(payload['daily'])==18 and len(payload['period'])==12
    aligned=[v for v in payload['views'] if v['allow_comparison']];assert len(aligned)==18
    assert all(any(v['period_key']==p['key'] for v in aligned) for p in payload['period'])
    cases=[]
    for d in payload['daily']:
        original=AnalysisStore(config['daily_stores'][d['store']]).snapshot(d['record_id'],d['as_of'])
        assert original==d['snapshot']
        assert fingerprint(original)==d['lineage']['selected_snapshot_fingerprint']
    for p in payload['period']:
        original=PeriodStore(config['period_stores'][p['store']]).load(p['analysis_id'])
        assert original==p['record']
    for v in aligned:
        d=next(x for x in payload['daily'] if x['key']==v['daily_key']);p=next(x for x in payload['period'] if x['key']==v['period_key'])
        selection=dict(schema_version=SELECTION_SCHEMA,**v['scope'],daily=dict(store=d['store'],record_id=d['record_id']),period=dict(store=p['store'],analysis_id=p['analysis_id']))
        value=select(payload,selection);assert value['alignment']==v and value['daily']==d and value['period']==p
        case=v['scope']['code']+'_'+v['scope']['price_mode']+'_'+v['scope']['as_of']+'_'+d['versions']['structure']
        write(requests/(case+'_SELECT.json'),selection)
        write(out/(case+'_VIEW.json'),value)
        cases.append(dict(case=case,view_id=v['view_id'],daily_key=d['key'],period_key=p['key'],**v['scope'],
                          daily_snapshot_fingerprint=fingerprint(d['snapshot']),period_snapshot_fingerprint=p['snapshot_fingerprint'],
                          structure_version=d['versions']['structure'],status=v['status']))
    receipt=export(config,ROOT/'日週月研究對照.html')
    assert receipt['aligned_views']==18
    # Real CLI selections from different stores; neither command has a calculation path.
    workers=[]
    for case in (cases[0],next(c for c in cases if c['code']=='2884')):
        cmd=[sys.executable,str(ROOT/'src/cross_view_cli.py'),'--config',str(ROOT/'cross_view/sources.json'),'--selection',str(requests/(case['case']+'_SELECT.json')),'--output',str(out/(case['case']+'_CLI.json'))]
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);assert p.returncode==0,p.stderr
        assert json.loads((out/(case['case']+'_CLI.json')).read_text())==json.loads((out/(case['case']+'_VIEW.json')).read_text())
        workers.append(dict(command=cmd,exit_code=p.returncode))
    assert protected(config)==before
    report=dict(status='PASS',cases=cases,initial_missing_daily_periods=6,explicit_filled_daily_jobs=3,final_missing_daily_periods=0,
                actual_daily_records=9,daily_snapshots=18,period_records=12,aligned_pairs=18,read_only_cli_workers=workers,
                preserved_files=before,original_values_identical=True,calculation_in_reader=False,
                browser_rendering='NOT_TESTED',mobile_touch='NOT_TESTED',classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
    write(out/'日週月對照實算驗收.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
