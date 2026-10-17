"""Explicit calculation worker for three previously unsaved daily cases.

This command is never imported by the read-only comparison/export modules.
"""
import json
import sys
import subprocess
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from analysis_workflow import execute_workflow
from contracts import fingerprint


def main():
    out=ROOT/'cross_view/output';req=ROOT/'cross_view/requests'
    out.mkdir(parents=True,exist_ok=True);req.mkdir(parents=True,exist_ok=True)
    cases=[]
    for case in ('6488_RAW_CANDIDATE','6488_ADJUSTED_CANDIDATE','2884_RAW_CANDIDATE'):
        period=json.loads((ROOT/'period_analysis/requests'/(case+'.json')).read_text())
        job={k:deepcopy(v) for k,v in period.items() if k not in ('as_of','calendar')}
        job['schema_version']='stock-analysis/1.0'
        if period.get('calendar') is not None:job['expected_dates']=period['calendar']['expected_dates']
        evidence=dict(schema_version='analysis-evidence/1.0',code=job['code'],coverage_status='UNVERIFIED',records=[])
        command=dict(schema_version='analysis-workflow/1.0',operation='RUN',job=job,evidence=evidence,
                     reason='v0.16 既有來源日線保存補齊；不新增行情或提升證據認證',as_of='2026-09-30',include_bundle=False)
        (req/(case+'_DAILY_RUN.json')).write_text(json.dumps(command,ensure_ascii=False,indent=2))
        response=execute_workflow(command,out/'補齊日線.sqlite3',create_if_missing=True)
        assert response['commit_status']=='COMMITTED'
        (out/(case+'_DAILY_RESPONSE.json')).write_text(json.dumps(response,ensure_ascii=False,indent=2))
        cases.append(dict(case=case,record_id=response['record_id'],analysis_id=response['analysis_id'],
                          request_fingerprint=fingerprint(job),result_fingerprint=response['result_fingerprint'],
                          evidence_coverage='UNVERIFIED',corporate_action_coverage=job['corporate_actions']['coverage_status']))
    code="""import sys,json;from analysis_store import AnalysisStore;from contracts import fingerprint
s=AnalysisStore(sys.argv[1]);print(json.dumps(dict(stats=s.stats(),records=[dict(record_id=m['record_id'],result_fingerprint=fingerprint(s.load(m['record_id'])['result'])) for m in s.list_records()])))
"""
    check=subprocess.run([sys.executable,'-c',code,str(out/'補齊日線.sqlite3')],env={**__import__('os').environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
    if check.returncode:raise RuntimeError('Independent read verification failed: '+check.stderr)
    fresh=json.loads(check.stdout)
    assert {r['record_id']:r['result_fingerprint'] for r in fresh['records']}=={r['record_id']:r['result_fingerprint'] for r in cases}
    report=dict(status='PASS',explicit_daily_runs=3,cases=cases,independent_read_verification=fresh,source='Existing complete v0.13 period requests; no new market fetch',
                action_qualification='NOT_EVALUATED',classification_quality='NOT_VALIDATED')
    (out/'日線補齊計算.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
