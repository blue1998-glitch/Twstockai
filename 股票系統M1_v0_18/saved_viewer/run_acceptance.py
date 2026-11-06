"""Export real saved records and compare exact snapshots; never calculate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from analysis_store import AnalysisStore
from contracts import fingerprint
from saved_viewer import write_html


def run(database, output):
    store=AnalysisStore(database)
    before=hashlib.sha256(database.read_bytes()).hexdigest(); stats=store.stats()
    receipt=write_html(database,output)
    html=output.read_text(encoding='utf-8')
    data=json.loads(re.search(r'<script id="saved-data" type="application/json">(.*?)</script>',html,re.S).group(1))
    checks=[]; snapshots=[]
    for b in data['records']:
        assert b==store.load(b['record_id'])
        r=b['result'];frames=[]
        for i,a in enumerate(r['aligned_snapshots']):
            f=dict(schema_version=b['schema_version'],record_id=b['record_id'],analysis_id=b['analysis_id'],as_of=a['as_of'],
                   aligned=a,structure=r['components']['structure']['snapshots'][i],daily_ma=r['components']['daily_ma']['snapshots'][i],
                   evidence_coverage=b['evidence']['coverage_status'],corporate_action_coverage=r['shared_input']['corporate_action_coverage'],action_qualification='NOT_EVALUATED')
            frames.append(f)
            snapshots.append(dict(record_id=b['record_id'],as_of=a['as_of'],snapshot_fingerprint=fingerprint(f)))
        selected=sorted({0,len(frames)//2,len(frames)-1}) if frames else []
        for i in selected:assert frames[i]==store.snapshot(b['record_id'],frames[i]['as_of'])
        checks.append(dict(code=r['shared_input']['code'],mode=r['shared_input']['price_mode'],record_id=b['record_id'],
                           bundles_equal=True,snapshots=len(frames),public_snapshot_reads=len(selected)))
    after=hashlib.sha256(database.read_bytes()).hexdigest()
    assert before==after and store.stats()==stats
    result=dict(status='PASS',method='Real saved DB -> HTML -> parsed JSON; complete bundle equality; first/middle/last public snapshot reads',
                export=receipt,records=checks,snapshot_expectations=snapshots,database_sha256_before=before,database_sha256_after=after,
                database_stats=stats,browser_rendering='NOT_TESTED',classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=ROOT/'volume_revision/output/單位修正並存_v0_12.sqlite3')
    p.add_argument('--html',type=Path,default=ROOT/'成交量版本比較瀏覽.html')
    p.add_argument('--report',type=Path,default=ROOT/'volume_revision/output/保存結果完整比對.json')
    a=p.parse_args();result=run(a.db,a.html)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='snapshot_expectations'},ensure_ascii=False))
