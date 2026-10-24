"""One validated request, independently versioned numeric engines, aligned snapshots.

This adapter adds provenance and execution integrity, never a combined score.
The legacy jobs.py JSON request contract remains available.
"""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
from contracts import SCHEMA_VERSION, DataError, fingerprint, iso_date
from jobs import run_job
from moving_averages import analyze_daily_ma

REQUEST_SCHEMA='stock-analysis/1.0'
RESULT_SCHEMA='stock-analysis-result/1.0'
VERSION='analysis-job-0.1'


def _preflight(job):
    if not isinstance(job,dict):raise DataError('INVALID_JOB','job','Object required')
    if job.get('schema_version')!=REQUEST_SCHEMA:
        raise DataError('SCHEMA_VERSION','schema_version','Use stock-analysis/1.0 for the combined adapter')
    if job.get('price_mode') not in ('RAW_CANDIDATE','ADJUSTED_CANDIDATE'):
        raise DataError('INVALID_PRICE_MODE','price_mode','Explicit price mode required')
    source=job.get('source')
    if not isinstance(source,dict) or not isinstance(source.get('id'),str) or not source['id'].strip():
        raise DataError('MISSING_SOURCE','source.id','Nonempty source identity string required')
    if 'expected_dates' in job and job['expected_dates'] is not None:
        dates=job['expected_dates']
        if not isinstance(dates,list):raise DataError('INVALID_CALENDAR','expected_dates','List required')
        for i,dt in enumerate(dates):iso_date(dt,f'expected_dates[{i}]')
        if len(set(dates))!=len(dates):raise DataError('INVALID_CALENDAR','expected_dates','Duplicate expected date')
    try:fingerprint(job)
    except (TypeError,ValueError):raise DataError('NON_JSON_VALUE','job','Finite JSON-compatible values required') from None


def _align(structure,ma,job):
    for key,expected in [('code',job['code']),('price_mode',job['price_mode']),
                         ('data_fingerprint',fingerprint(job['candles'])),
                         ('events_fingerprint',fingerprint(job['corporate_actions']['records']))]:
        if structure.get(key)!=expected or ma.get(key)!=expected:
            raise DataError('COMPONENT_ALIGNMENT',key,'Engines do not share the requested input identity')
    a,b=structure.get('snapshots'),ma.get('snapshots')
    if not isinstance(a,list) or not isinstance(b,list) or len(a)!=len(b) or len(a)!=len(job['candles']):
        raise DataError('COMPONENT_ALIGNMENT','snapshots','Snapshot counts differ')
    aligned=[]
    for i,(s,m) in enumerate(zip(a,b)):
        expected=job['candles'][i]['date']
        if (s.get('as_of')!=expected or m.get('as_of')!=expected
            or s.get('data_fingerprint')!=m.get('data_fingerprint')
            or s.get('effective_events_fingerprint')!=m.get('events_fingerprint')
            or s.get('source_id')!=job['source']['id']):
            raise DataError('COMPONENT_ALIGNMENT',f'snapshots[{i}]','Date, data, event anchor or source differs')
        if s.get('action_qualification')!='NOT_EVALUATED':
            raise DataError('UNAUTHORIZED_QUALIFICATION',f'snapshots[{i}]','Trading rules are not enabled')
        pair=dict(as_of=expected,structure_snapshot_id=s['snapshot_id'],daily_ma_snapshot_id=m['snapshot_id'],
                  data_fingerprint=s['data_fingerprint'],effective_events_fingerprint=m['events_fingerprint'],
                  input_quality_fingerprint=fingerprint(s['data_quality']))
        aligned.append(dict(**pair,snapshot_id=fingerprint(dict(schema=RESULT_SCHEMA,**pair)),
                            data_quality=deepcopy(s['data_quality'])))
    if ma.get('action_qualification')!='NOT_EVALUATED':
        raise DataError('UNAUTHORIZED_QUALIFICATION','daily_ma','Trading rules are not enabled')
    return aligned


def run_analysis_job(job):
    _preflight(job)
    request=deepcopy(job)
    legacy=deepcopy(request);legacy['schema_version']=SCHEMA_VERSION
    # Legacy boundary validates all required source/unit/price/action fields.
    structure=run_job(legacy)
    ma=analyze_daily_ma(request['candles'],request['corporate_actions']['records'],
                        code=request['code'],mode=request['price_mode'])
    aligned=_align(structure,ma,request)
    versions=dict(structure=structure['rule_version'],daily_ma=ma['rule_version'])
    params=dict(structure=structure['parameters_fingerprint'],daily_ma=ma['parameters_fingerprint'])
    request_fp=fingerprint(request)
    return dict(schema_version=RESULT_SCHEMA,adapter_version=VERSION,
                status='COMPLETED' if aligned else 'EMPTY_INPUT',
                analysis_id=fingerprint(dict(request=request_fp,versions=versions,parameters=params,adapter=VERSION)),
                request_fingerprint=request_fp,component_versions=versions,
                shared_input=dict(code=request['code'],exchange=request['exchange'],timeframe=request['timeframe'],
                                  price_mode=request['price_mode'],source=deepcopy(request['source']),
                                  corporate_action_coverage=request['corporate_actions']['coverage_status'],
                                  data_fingerprint=structure['data_fingerprint'],events_fingerprint=structure['events_fingerprint'],
                                  data_quality=deepcopy(structure['data_quality']),
                                  calendar_context='SHARED_BOUNDARY_CHECK; component-native reports retained unchanged'),
                components=dict(structure=structure,daily_ma=ma),aligned_snapshots=aligned,
                action_qualification='NOT_EVALUATED',
                limitations=['COMPLETED means computation finished, not classification or trading approval',
                             'Source identity is a caller claim, not independent source authentication',
                             'Official calendar, complete corporate actions and historical publication timing remain unverified'])


def _write_atomic(path,result):
    path=Path(path);tmp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,
                                         prefix=path.name+'.',suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp is not None and tmp.exists():tmp.unlink()


def main(argv=None):
    parser=argparse.ArgumentParser(description='Structure and daily MA from one validated daily input')
    parser.add_argument('--input',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args(argv);inp=Path(args.input);out=Path(args.output)
    if inp.resolve()==out.resolve() or inp.exists() and out.exists() and inp.samefile(out):
        print(json.dumps(DataError('INPUT_OUTPUT_COLLISION','output','Output must not replace the input request').as_dict()),file=sys.stderr)
        return 3
    status=0
    try:result=run_analysis_job(json.loads(inp.read_text(encoding='utf-8-sig')))
    except DataError as e:result=e.as_dict();status=2
    except (OSError,json.JSONDecodeError,UnicodeError) as e:
        result=DataError('INPUT_FILE_ERROR','input',type(e).__name__).as_dict();status=2
    try:_write_atomic(out,result)
    except OSError as e:
        print(json.dumps(DataError('OUTPUT_FILE_ERROR','output',type(e).__name__).as_dict()),file=sys.stderr)
        return 3
    return status


if __name__=='__main__':raise SystemExit(main())
