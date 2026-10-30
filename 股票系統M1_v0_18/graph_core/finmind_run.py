"""Explicit M2-3 local RUN; raw data and results must stay outside Git trees.

No automatic refresh, database, viewer, strategy selection or trading.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Context, Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .finmind_adapter import (IntakeError, analyze_response, assess_integer_lot_display,
                             public_summary)

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parent
ENDPOINT = 'https://api.finmindtrade.com/api/v4/data'
PARAMETERS = dict(dataset='TaiwanStockPrice', data_id='2884',
                  start_date='2026-03-01', end_date='2026-07-22')
AS_OFS = ('2026-07-21', '2026-07-22')


def external_path(value):
    """Refuse this repo and any other enclosing Git tree, including symlinks."""
    path = Path(value).expanduser().resolve()
    if path == REPOSITORY or REPOSITORY in path.parents:
        raise IntakeError('RESTRICTED_DATA_PATH_INSIDE_REPOSITORY')
    if any((parent / '.git').exists() for parent in (path, *path.parents)):
        raise IntakeError('RESTRICTED_DATA_PATH_INSIDE_GIT_TREE')
    return path


def _write(path, data):
    raw = json.dumps(data, ensure_ascii=False, indent=2, default=str, allow_nan=False) + '\n'
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        stream.write(raw)


def _parse(raw):
    # Preserve decimal JSON lexemes. Reject duplicate fields and nonfinite data.
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise IntakeError('DUPLICATE_JSON_FIELD')
            result[k] = v
        return result
    def constant(_):
        raise IntakeError('NONFINITE_JSON')
    return json.loads(raw, parse_float=Decimal, parse_constant=constant, object_pairs_hook=pairs)


def _retained_sources():
    """Reuse original strict TWSE parser; no source capture or old rewrites."""
    sys.path.insert(0, str(PROJECT / 'src'))
    from source_audit import parse_twse_month
    raw_dir = PROJECT / 'pressure_chart/data/history-20261018/raw'
    rows, bindings, warnings = [], [], []
    for month in range(3, 8):
        path = raw_dir / f'2884_2026-{month:02}.json'
        raw = path.read_bytes()
        meta = json.loads(path.with_name(path.stem + '_meta.json').read_text())
        if hashlib.sha256(raw).hexdigest() != meta['sha256']:
            raise IntakeError('RETAINED_SOURCE_HASH_MISMATCH')
        data = json.loads(raw)
        rows.extend(r for r in parse_twse_month(data, code='2884', year=2026, month=month)
                    if PARAMETERS['start_date'] <= r['date'] <= PARAMETERS['end_date'])
        bindings.append(dict(path=str(path.relative_to(REPOSITORY)), sha256=meta['sha256'],
                             fetched_at=meta['fetched_at_utc']))
        if month == 7:
            if not any('不比價' in n for n in data['notes']):
                raise IntakeError('OFFICIAL_WARNING_LEGEND_MISSING')
            marked = [r for r in data['data'] if r[0] == '115/07/01']
            if len(marked) != 1 or not marked[0][data['fields'].index('漲跌價差')].startswith('X'):
                raise IntakeError('OFFICIAL_WARNING_NOT_FOUND')
            warnings.append(dict(date='2026-07-01', kind='NON_COMPARABLE_MARKER_EVENT_TYPE_UNKNOWN',
                                 source_id=meta['sha256']))
    return rows, bindings, warnings


def _volume_precision_8069():
    path = PROJECT / 'pressure_chart/data/history-20261018/raw/8069_2026-07.json'
    raw = path.read_bytes()
    meta = json.loads(path.with_name(path.stem + '_meta.json').read_text())
    if hashlib.sha256(raw).hexdigest() != meta['sha256']:
        raise IntakeError('RETAINED_SOURCE_HASH_MISMATCH')
    data = json.loads(raw)
    if data['code'] != '8069' or data['flagField'] != '張數' or data['stat'].lower() != 'ok':
        raise IntakeError('OFFICIAL_8069_SOURCE_MISMATCH')
    table, results = data['tables'][0], []
    if table['fields'][1] != '成交張數':
        raise IntakeError('OFFICIAL_8069_UNIT_MISMATCH')
    # Only the two authorized existing observations, no historical series adapter.
    for day in AS_OFS:
        roc = '115/' + day[5:].replace('-', '/')
        rows = [r for r in table['data'] if r[0] == roc]
        if len(rows) != 1:
            raise IntakeError('OFFICIAL_8069_EXACT_DATE_MISSING')
        results.append(dict(as_of=day, **assess_integer_lot_display(
            official_unit=table['fields'][1], displayed_value=rows[0][1])))
    return dict(code='8069', acquisition='RETAINED_OFFICIAL_TWO_DAYS_ONLY',
                finmind_prices='WORK_REPORTED_MATCH_NOT_RECHECKED_WITH_UNAVAILABLE_LIBRARY_ORIGINAL',
                observations=results)


def _acquire(out):
    receipt = dict(endpoint=ENDPOINT, parameters=PARAMETERS,
                   requested_at=datetime.now(timezone.utc).isoformat(), attempts=1)
    try:
        with urlopen(Request(ENDPOINT + '?' + urlencode(PARAMETERS)), timeout=40) as source:
            raw = source.read(4000001)
            receipt['http_status'] = source.status
        if len(raw) > 4000000:
            raise IntakeError('RESPONSE_SIZE_LIMIT')
        with (out / 'response.json').open('xb') as stream:
            os.chmod(out / 'response.json', 0o600)
            stream.write(raw)
        receipt['response_sha256'] = hashlib.sha256(raw).hexdigest()
        _write(out / 'acquisition.json', receipt)
        return raw, receipt
    except (HTTPError, URLError, TimeoutError) as exc:
        receipt.update(status='BLOCKED', reason='HTTP_OR_NETWORK_REFUSED',
                       http_status=exc.code if isinstance(exc, HTTPError) else None)
        _write(out / 'acquisition.json', receipt)
        raise IntakeError('HTTP_OR_NETWORK_REFUSED_NO_RETRY') from None


def run(*, output_dir, response_path=None, acquisition_path=None):
    """Single explicit bounded RUN; saved-file mode never re-queries the API."""
    with localcontext(Context(prec=50)):
        return _run(output_dir=output_dir, response_path=response_path,
                    acquisition_path=acquisition_path)


def _run(*, output_dir, response_path=None, acquisition_path=None):
    out = external_path(output_dir)
    if bool(response_path) != bool(acquisition_path):
        raise IntakeError('RESPONSE_AND_ACQUISITION_REQUIRED_TOGETHER')
    # Validate paths before any output creation.
    if response_path:
        response_path = external_path(response_path)
        acquisition_path = external_path(acquisition_path)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        if response_path:
            raw = response_path.read_bytes()
            receipt = json.loads(acquisition_path.read_text())
        else:
            raw, receipt = _acquire(out)
        if (receipt.get('endpoint') != ENDPOINT or receipt.get('parameters') != PARAMETERS or
                receipt.get('http_status') != 200 or
                receipt.get('response_sha256') != hashlib.sha256(raw).hexdigest()):
            raise IntakeError('ACQUISITION_BINDING_MISMATCH')
        response = _parse(raw)
        official, bindings, warnings = _retained_sources()
        request = dict(schema_version='finmind-graph-request/0.1', dataset='TaiwanStockPrice',
                       code='2884', exchange='TWSE', start_date=PARAMETERS['start_date'],
                       end_date=PARAMETERS['end_date'], retrieved_at=receipt['requested_at'],
                       source_id='FinMind:TaiwanStockPrice:2884:RAW',
                       price_basis_id='FinMind:TaiwanStockPrice:RAW_ACTIONS_UNKNOWN',
                       volume_unit='SHARES_REPORTED', historical_available_at='UNKNOWN',
                       expected_dates=[r['date'] for r in official],
                       calendar_source_id='RETAINED_TWSE_SAME_STOCK_OBSERVED_DATES',
                       calendar_completeness='UNKNOWN', basis_warnings=warnings)
        _write(out / 'source-bindings.json', dict(official_sources=bindings,
               response_sha256=hashlib.sha256(raw).hexdigest(), acquisition=receipt))
        results = []
        for day in AS_OFS:
            job = dict(request, as_of=day)
            _write(out / f'input-{day}.json', dict(request=job, response=response))
            result = analyze_response(response, job)
            _write(out / f'result-{day}.json', result)
            results.append(result)
        job = dict(request, as_of=AS_OFS[0])
        short = deepcopy(response)
        short['data'] = [r for r in short['data'] if r['date'] <= AS_OFS[0]]
        prefix_result = analyze_response(short, job)
        changed = deepcopy(response)
        for row in changed['data']:
            if row['date'] > AS_OFS[0]:
                # Explicitly hypothetical future control, never market evidence.
                row.update(open='100', max='101', min='99', close='100', Trading_Volume=1)
        future_result = analyze_response(changed, job)
        same = results[0]['analysis'] == prefix_result['analysis'] == future_result['analysis']
        if not same:
            raise IntakeError('FUTURE_PREFIX_ISOLATION_FAILED')
        _write(out / 'prefix-control.json', dict(short=prefix_result, mutated_future=future_result))
        by_date = {r['date']: r for r in official}
        checks = {}
        for day, result in zip(AS_OFS, results):
            bar = result['graph_input']['bars'][-1]
            checks[day] = {key: Decimal(bar[key]) == Decimal(by_date[day][key])
                           for key in ('open', 'high', 'low', 'close', 'volume_shares_scaled')}
        if not all(all(x.values()) for x in checks.values()):
            raise IntakeError('OFFICIAL_TWO_DAY_COMPARISON_MISMATCH')
        summary = dict(schema_version='m2-3-finmind-acceptance/0.1', status='LIMITED_RESEARCH_COMPLETED',
                       raw_and_reconstructable_data_published=False, source='FinMind Free TaiwanStockPrice',
                       start_date=PARAMETERS['start_date'], end_date=PARAMETERS['end_date'],
                       library_originals='NOT_OBTAINED_NOT_READ',
                       analysis=[public_summary(r) for r in results],
                       official_two_day_field_matches=checks,
                       prefix_control=dict(analysis_equal=same, full_source_integrity_compared_separately=True,
                                           later_date_absent_from_earlier_input=True),
                       precision_8069=_volume_precision_8069())
        _write(out / 'public-summary.json', summary)
        return summary
    except Exception as exc:
        # Do not print response bodies, quotes, caller paths or source exceptions.
        code = str(exc) if isinstance(exc, IntakeError) else 'SOURCE_OR_CORE_VALIDATION_REFUSED'
        _write(out / 'blocked.json', dict(status='BLOCKED', reason=code))
        raise IntakeError(code) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, help='fresh local directory outside any Git tree')
    parser.add_argument('--response', help='reuse locally saved response; no network')
    parser.add_argument('--acquisition', help='matching local acquisition receipt')
    args = parser.parse_args()
    try:
        result = run(output_dir=args.output_dir, response_path=args.response,
                     acquisition_path=args.acquisition)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (IntakeError, FileExistsError) as exc:
        print(json.dumps(dict(status='BLOCKED', reason=str(exc) if isinstance(exc, IntakeError)
                              else 'FRESH_OUTPUT_DIRECTORY_REQUIRED')))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
