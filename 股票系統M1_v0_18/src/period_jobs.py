"""Standalone period-analysis JSON boundary; never calls storage or old jobs."""
from copy import deepcopy
import argparse,json,os,sys,tempfile
from pathlib import Path
from contracts import DataError,fingerprint
from period_ma import analyze_period_ma,VERSION

REQUEST_SCHEMA='stock-period-analysis/1.0'
RESULT_SCHEMA='period-analysis-result/1.0'
ADAPTER_VERSION='period-job-0.1'


def run_period_job(job):
    required={'schema_version','code','exchange','timeframe','price_mode','source','candles','corporate_actions','as_of'}
    if not isinstance(job,dict) or not required<=set(job) or set(job)-required-{'calendar'}:
        raise DataError('PERIOD_JOB_FIELDS','job','Fixed period-job fields required; unknown fields rejected')
    if job['schema_version']!=REQUEST_SCHEMA:raise DataError('SCHEMA_VERSION','schema_version','Use stock-period-analysis/1.0')
    if job['exchange'] not in ('TWSE','TPEX') or job['timeframe']!='daily':raise DataError('PERIOD_SCOPE','exchange/timeframe','Taiwan exchange daily source input required')
    source=job['source'];actions=job['corporate_actions']
    if not isinstance(source,dict) or source.get('code')!=job['code'] or source.get('exchange')!=job['exchange']:
        raise DataError('SOURCE_IDENTITY_MISMATCH','source','Source stock and exchange must match')
    if not isinstance(actions,dict) or set(actions)!={'records','coverage_status'} or actions.get('coverage_status') not in ('UNVERIFIED','CASH_ONLY_VERIFIED_SAMPLE'):
        raise DataError('MISSING_EVENT_COVERAGE','corporate_actions','Explicit records and limited coverage required')
    try:request_fp=fingerprint(job)
    except (TypeError,ValueError):raise DataError('NON_JSON_VALUE','job','Finite JSON-compatible values required') from None
    q=deepcopy(job)
    snapshot=analyze_period_ma(q['candles'],q['corporate_actions']['records'],code=q['code'],exchange=q['exchange'],mode=q['price_mode'],as_of=q['as_of'],
                               source_id=source.get('id'),volume_unit=source.get('volume_unit'),calendar=q.get('calendar'))
    return dict(schema_version=RESULT_SCHEMA,adapter_version=ADAPTER_VERSION,request_fingerprint=request_fp,
                analysis_id=fingerprint(dict(request=request_fp,rule_version=VERSION,adapter=ADAPTER_VERSION,snapshot=snapshot['snapshot_id'])),
                status=snapshot['status'],corporate_action_coverage=actions['coverage_status'],source=deepcopy(source),snapshot=snapshot,
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')


def _pairs(pairs):
    obj={}
    for k,v in pairs:
        if k in obj:raise DataError('DUPLICATE_JSON_KEY','input',k)
        obj[k]=v
    return obj


def _write(path,value):
    temp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.period-',delete=False) as f:
            temp=Path(f.name);json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp is not None and temp.exists():temp.unlink()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    inp=Path(a.input);out=Path(a.output)
    if out.is_symlink() or inp.resolve()==out.resolve() or inp.exists() and out.exists() and inp.samefile(out):
        print(json.dumps(DataError('INPUT_OUTPUT_COLLISION','output','Output must not alias input or be a symbolic link').as_dict()),file=sys.stderr);return 3
    status=0
    try:result=run_period_job(json.loads(inp.read_text(encoding='utf-8-sig'),object_pairs_hook=_pairs))
    except DataError as e:result=e.as_dict();status=2
    except (OSError,ValueError,UnicodeError) as e:result=DataError('INPUT_FILE_ERROR','input',str(e)).as_dict();status=2
    try:_write(out,result)
    except OSError as e:
        print(json.dumps(DataError('OUTPUT_FILE_ERROR','output',str(e)).as_dict()),file=sys.stderr);return 3
    print(json.dumps(dict(status=result['status'],process_id=os.getpid(),analysis_id=result.get('analysis_id'),action_qualification='NOT_EVALUATED')))
    return status


if __name__=='__main__':raise SystemExit(main())
