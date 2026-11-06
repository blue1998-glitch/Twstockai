"""Versioned request boundary. Invalid inputs return data errors, never signals."""
import argparse
import json
from pathlib import Path
from contracts import SCHEMA_VERSION, DataError, validate_candles, validate_events, fingerprint
from structure import analyze


def run_job(job):
    if not isinstance(job,dict):raise DataError('INVALID_JOB','job','Object required')
    for key in ['schema_version','code','exchange','price_mode','timeframe','source','candles','corporate_actions']:
        if key not in job:raise DataError('MISSING_FIELD',key,'Required job field missing')
    if job['schema_version']!=SCHEMA_VERSION:raise DataError('SCHEMA_VERSION','schema_version','Unsupported input version')
    if job['exchange'] not in ('TWSE','TPEX') or job['timeframe']!='daily':raise DataError('UNSUPPORTED_SCOPE','exchange/timeframe','Only Taiwan exchange daily inputs supported')
    if not isinstance(job['code'],str) or not job['code']:raise DataError('INVALID_CODE','code','Nonempty code required')
    source=job['source']
    if not isinstance(source,dict) or not source.get('id'):raise DataError('MISSING_SOURCE','source','Source identity required')
    if source.get('code')!=job['code'] or source.get('exchange')!=job['exchange']:
        raise DataError('SOURCE_IDENTITY_MISMATCH','source','Source stock/exchange differs from requested stock')
    if source.get('volume_unit') not in ('SHARES_SCALED_FROM_LOTS','SHARES_REPORTED'):raise DataError('UNSUPPORTED_UNIT','source.volume_unit','Explicit reported shares or source lots scaled to shares required')
    validate_candles(job['candles'])
    action=job['corporate_actions']
    if not isinstance(action,dict) or 'records' not in action or action.get('coverage_status') not in ('CASH_ONLY_VERIFIED_SAMPLE','UNVERIFIED'):
        raise DataError('MISSING_EVENT_COVERAGE','corporate_actions','Records and explicit coverage status required')
    validate_events(action['records'])
    result=analyze(job['candles'],action['records'],code=job['code'],mode=job['price_mode'],source_id=source['id'],expected_dates=job.get('expected_dates'),volume_unit=source['volume_unit'])
    result.update(exchange=job['exchange'],timeframe=job['timeframe'],source=source,
                  corporate_action_coverage=action['coverage_status'],request_fingerprint=fingerprint(job))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    status=0
    try:result=run_job(json.loads(Path(args.input).read_text(encoding='utf-8-sig')))
    except DataError as e:result=e.as_dict();status=2
    except (OSError,json.JSONDecodeError) as e:result=DataError('INPUT_FILE_ERROR','input',type(e).__name__).as_dict();status=2
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit(status)
