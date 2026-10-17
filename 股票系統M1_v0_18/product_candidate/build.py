"""Explicit offline RUN: public read-only stores -> separate immutable candidate.

Never called by the browser. Existing numeric engines/schemas are unchanged.
"""
import argparse
from copy import deepcopy
from decimal import localcontext, ROUND_HALF_EVEN
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from contracts import fingerprint, validate_candles, validate_events
from analysis_store import AnalysisStore
from cross_view import catalog
from cross_view_cli import read_config
from cross_view_export import protect
from structure import project_prices
from product_candidate.context import frame_context, VERSION
from product_candidate.macd import macd, PARAMETERS, VERSION as MACD_VERSION


def series_from_saved(saved, alias, background):
    request = saved['request']
    rows = request['candles']
    events = request['corporate_actions']['records']
    validate_candles(rows)
    validate_events(events)
    if not rows:
        raise ValueError('Nonempty saved record required')
    component = saved['result']['components']
    structures, mas = component['structure']['snapshots'], component['daily_ma']['snapshots']
    if len(structures) != len(mas) or len(rows) != len(structures):
        raise ValueError('Snapshot/date count mismatch')
    bases, frame_bases, group_ends = {}, [], {}
    for index, row in enumerate(rows):
        known = [event for event in events if event['effective_date'] <= row['date']]
        key = fingerprint(dict(mode=request['price_mode'], source=request['source']['id'],
                               first_date=rows[0]['date'], known_events=known, producer=VERSION))
        frame_bases.append(key)
        group_ends[key] = index
    for key, end in group_ends.items():
        as_of = rows[end]['date']
        known = [event for event in events if event['effective_date'] <= as_of]
        with localcontext() as ctx:
            ctx.prec = 28
            ctx.rounding = ROUND_HALF_EVEN
            projected = project_prices(rows[:end + 1], known, as_of, request['price_mode'])
        for row in projected:
            row['volume_shares_scaled'] = row.get('volume_shares_scaled')
        resets = sorted({next(i for i, row in enumerate(projected) if row['date'] >= event['effective_date'])
                         for event in known if request['price_mode'] == 'RAW_CANDIDATE'
                         and event['effective_date'] <= projected[-1]['date']})
        bases[key] = dict(bars=projected, moving_averages=deepcopy(mas[end]['curves']),
                          macd=macd([row['close'] for row in projected], resets=resets),
                          price_basis='NEW_OFFLINE_CANDIDATE_PROJECTION_USING_EXISTING_PROJECT_PRICES',
                          known_events=deepcopy(known), anchor=as_of)
    frames = []
    for index, (row, snapshot, ma) in enumerate(zip(rows, structures, mas)):
        prefix = rows[:index + 1]
        if snapshot['as_of'] != row['date'] or snapshot['data_fingerprint'] != fingerprint(prefix):
            raise ValueError('Exact saved prefix mismatch')
        known = [event for event in events if event['effective_date'] <= row['date']]
        if snapshot['effective_events_fingerprint'] != fingerprint(known) or ma['events_fingerprint'] != fingerprint(known):
            raise ValueError('Saved event prefix mismatch')
        key = frame_bases[index]
        base = bases[key]
        if any(values != base['moving_averages'][period][:index + 1] for period, values in ma['curves'].items()):
            raise ValueError('Same-event-basis SMA prefix changed')
        frame = frame_context(request, snapshot, ma, base['bars'][:index + 1], base['macd'][index],
                              previous=frames[-1] if frames else None,
                              prior_indicator=base['macd'][index - 1] if index else None,
                              period=background.get((alias, saved['record_id'], row['date'])))
        frame.pop('frame_id')
        frame.update(chart_base=key, index=index)
        frame['frame_id'] = fingerprint(frame)
        frames.append(frame)
    return dict(key=fingerprint(dict(store=alias, record_id=saved['record_id'], candidate=VERSION)),
                code=request['code'], exchange=request['exchange'], price_mode=request['price_mode'],
                source=deepcopy(request['source']), store=alias, original_record_id=saved['record_id'],
                original_result_fingerprint=fingerprint(saved['result']),
                original_structure_version=saved['result']['component_versions']['structure'],
                available_start=rows[0]['date'], available_end=rows[-1]['date'],
                coverage=request['corporate_actions']['coverage_status'], frames=frames, bases=bases)


def bundle(config, structure_version):
    if structure_version not in ('structure-0.2-research', 'structure-0.3-research'):
        raise ValueError('Explicit supported input producer required')
    # Existing catalog performs exact identity/anchor/content comparisons for the
    # two actually saved period dates. Other dates get no synthetic background.
    existing = catalog(config)
    daily = {row['key']: row for row in existing['daily']}
    periods = {row['key']: row for row in existing['period']}
    background = {}
    for view in existing['views']:
        if view['daily_key'] not in daily or view['period_key'] not in periods:
            continue
        d, p = daily[view['daily_key']], periods[view['period_key']]
        key = (d['store'], d['record_id'], d['as_of'])
        if key in background:
            raise ValueError('Ambiguous period match; do not silently pick a version')
        background[key] = dict(alignment_status=view['status'], analysis_id=p['analysis_id'],
                               record_fingerprint=p['record']['record_fingerprint'],
                               snapshot=deepcopy(p['record']['result']['snapshot']))
    series = []
    for alias, path in config['daily_stores'].items():
        store = AnalysisStore(path)
        for metadata in store.list_records():
            saved = store.load(metadata['record_id'])
            if saved['result']['component_versions']['structure'] == structure_version:
                series.append(series_from_saved(saved, alias, background))
    if not series:
        raise ValueError('No records for the explicitly requested producer')
    output = dict(schema_version='product-candidate-bundle/0.1', producer_version=VERSION,
                  input_structure_version=structure_version, macd_version=MACD_VERSION, macd_parameters=PARAMETERS,
                  status='ENGINEERING_CANDIDATE_NOT_PRODUCT_OR_STRATEGY_APPROVAL', series=series,
                  classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED',
                  limits=['Daily sample only, not full stock lifecycle', 'Historical publication timing unverified',
                          'Lifecycle/pattern/ownership classifications remain unknown',
                          'Each replay frame can read only chart data through its own index',
                          'New candidate projected OHLC/MACD are not fields in original saved daily snapshots'])
    output['bundle_id'] = fingerprint(output)
    return output


def render(payload):
    directory = Path(__file__).resolve().parent
    text = (directory / 'template.html').read_text()
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    for char, escape in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        raw = raw.replace(char, escape)
    return text.replace('@@STYLE@@', (directory / 'viewer.css').read_text()).replace(
        '@@SCRIPT@@', (directory / 'viewer.js').read_text()).replace('@@DATA@@', raw)


def selection_payload(payload, series_key, as_of):
    series = next((s for s in payload['series'] if s['key'] == series_key), None)
    if series is None:
        raise ValueError('Exact series key required')
    frame = next((f for f in series['frames'] if f['as_of'] == as_of), None)
    if frame is None:
        raise ValueError('Exact saved analysis date required')
    base = series['bases'][frame['chart_base']]
    n = frame['index'] + 1
    return deepcopy(dict(schema_version='product-candidate-selection/0.1', bundle_id=payload['bundle_id'],
                         producer_version=payload['producer_version'], macd_version=payload['macd_version'],
                         macd_parameters=payload['macd_parameters'], original_record_id=series['original_record_id'],
                         source=series['source'], frame=frame, bars=base['bars'][:n],
                         moving_averages={k:v[:n] for k,v in base['moving_averages'].items()},
                         macd=base['macd'][:n], price_basis=base['price_basis'], known_events=base['known_events'],
                         classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED'))


def publish_immutable(path, content):
    path = Path(path)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != content:
            raise ValueError('Existing candidate differs; use a new version/output directory: ' + str(path))
        return 'EXISTING'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content)
        stream.flush()
        import os
        os.fsync(stream.fileno())
    return 'CREATED'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--structure-version', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    config = read_config(args.config)
    directory = Path(args.output_dir)
    protected = [Path(__file__), *(Path(__file__).parent.glob('*')), Path(args.config)]
    for name in ('candidate.json', 'M1_v0_19_candidate.html'):
        protect(config, directory / name, protected)
    payload = bundle(config, args.structure_version)
    receipt = {name: publish_immutable(directory / name, data) for name, data in (
        ('candidate.json', json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()),
        ('M1_v0_19_candidate.html', render(payload).encode()))}
    print(json.dumps(dict(status='CANDIDATE_EXPORTED', bundle_id=payload['bundle_id'], files=receipt,
                         series=len(payload['series']), frames=sum(len(s['frames']) for s in payload['series'])), ensure_ascii=False))


if __name__ == '__main__':
    main()
