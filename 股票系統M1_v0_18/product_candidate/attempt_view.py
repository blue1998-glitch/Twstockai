"""Opt-in offline adapter: existing attempt core -> new read-only viewer.

Only explicitly labelled synthetic fixtures are enabled here. Real source/basis
authentication and automatic reference selection are not implemented. No old
engine, store, viewer, or core rule is modified or invoked by browser code.
"""
import argparse
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from product_candidate.attempt_evidence import evaluate, VERSION as CORE_VERSION

VERSION = 'attempt-view-adapter/0.1'
DATA_KIND = 'SYNTHETIC_ENGINEERING_FIXTURE'
HTML_NAME = 'M1_v0_19_attempt_candidate.html'


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return sha256(encode(value).encode('utf-8')).hexdigest()


def source_bar(row, *, completed, known_at):
    """Copy supplied cumulative/final OHLC; never reconstruct an intraday path."""
    return dict(date=row['date'], known_at=known_at, is_close=completed,
                open=format(Decimal(row['open']), 'f'), high=format(Decimal(row['high']), 'f'),
                low=format(Decimal(row['low']), 'f'),
                close=format(Decimal(row['close'] if 'close' in row else row['last']), 'f'),
                volume_shares=None if row.get('volume_shares') is None else format(Decimal(row['volume_shares']), 'f'))


def chart_prefix(payload, result):
    rows = [source_bar(r, completed=True, known_at=r['known_at']) for r in payload['history']]
    for observation in payload['observations']:
        row = source_bar(observation, completed=observation['is_close'], known_at=observation['observed_at'])
        if rows[-1]['date'] == row['date']:
            rows[-1] = row
        else:
            rows.append(row)
    current_day = payload['observations'][-1]['date']
    supplied = [r for r in payload['observations'] if r['date'] == current_day]
    has_intraday = any(not r['is_close'] for r in supplied)
    points = [dict(observed_at=r['observed_at'], price=format(Decimal(r['last']), 'f'), is_close=r['is_close'])
              for r in supplied] if has_intraday else []
    refs = result['reference_set']
    return dict(daily=rows, intraday=dict(
        status='SUPPLIED_OBSERVATION_POINTS_NOT_TICKS' if has_intraday else 'INTRADAY_DATA_MISSING',
        points=points),
        near_high=dict(price=format(Decimal(refs['near_high']['price']), 'f'), bar_date=refs['near_high']['bar_date']),
        left_zone=dict(low=format(Decimal(refs['left_zone']['low']), 'f'), high=format(Decimal(refs['left_zone']['high']), 'f'),
                       bar_dates=deepcopy(refs['left_zone']['bar_dates'])),
        volume_benchmark=result['left_zone_max_volume_shares'])


def presentation(result):
    """Explain core facts; do not create additional price/volume criteria."""
    frame = result['frames'][-1]
    supporting, opposing = [], []
    for level in frame['attempt_levels']:
        name = '近期關卡' if level['reference_id'] == 'NEAR_HIGH' else '左區上緣'
        if level['price_attempt_condition'] == 'MET':
            supporting.append(dict(text=name + '的價格子條件成立；不是完整買入資格。',
                                   references=[level['reference_id']]))
    events = {e['id']: e for e in result['events']}
    if frame['volume_lead_evidence_ids']:
        supporting.append(dict(text='在已提供前綴中曾觀察到量先價；歷史支持不等於現在有效、已成功或有校準勝率。',
                               references=deepcopy(frame['volume_lead_evidence_ids'])))
    for event in result['events']:
        if event['kind'] in ('CLOSE_RETURNED_BELOW', 'INTRADAY_RETURNED_BELOW'):
            opposing.append(dict(text=('完成日收盤' if event['confirmed_at'] else '盤中觀察') +
                                 '跌回已選關卡；保留之前越過事實，不產生自動賣出。', references=[event['id']]))
    today = [e for e in result['events'] if e['bar_date'] == frame['bar_date']]
    volume_kinds = [e['kind'] for e in today if e['reference_id'] == 'LEFT_ZONE_VOLUME_MAX']
    if frame['left_zone_max_volume_shares'] is None:
        volume_text = '左區來源量有缺值，最高量與量比較未知；不能採用部分最大值。'
    elif frame['volume_shares'] is None:
        volume_text = '本時點量缺少，當下比較未知；已保存的歷史事件另列。'
    elif 'VOLUME_EXCESS_ORDER_UNKNOWN' in volume_kinds:
        volume_text = '同份資料已見高價越上緣及量超標，先後未知；不標成量先價。'
    elif 'VOLUME_EXCESS_PRICE_ALREADY_PASSED' in volume_kinds:
        volume_text = '已提供窗口中價格先前已越過左區上緣，這次量超標不重命名為新量先價。'
    elif 'VOLUME_LEAD_OBSERVED' in volume_kinds:
        volume_text = '已觀察量先超過指定左區最高量，當時高價仍未越上緣；後續價格進展另看。'
    else:
        volume_text = '此時沒有新增量先價支持；不會因此撤銷近期關卡的價格子條件。'
    missing = ['來源為假想工程例，不是真實股票或績效證據。',
               '歷史只含明列片段；未列日期未知，不宣稱完整市場覆蓋。',
               '自動選區、正式型態／生命階段、趨勢延續分類與校準勝率未建立。',
               '沒有實際持倉或成交資料，未評估完整交易資格。',
               '共同基底與公司行動僅由來源宣告，尚無真實市場認證。']
    if frame['left_zone_max_volume_shares'] is None:
        missing.append('左區來源量缺值。')
    if not any(not r['is_close'] for r in [f['source_observation'] for f in result['frames']]
               if r['date'] == frame['bar_date']):
        missing.append('本日沒有盤中觀察，不能由完成日OHLC推論路徑或量價次序。')
    return dict(supporting=supporting, opposing=opposing, missing=missing, volume_text=volume_text,
                volume_lead_first_observed_at=[events[k]['first_observed_at'] for k in frame['volume_lead_evidence_ids']])


def build_case(payload, metadata):
    if metadata.get('data_kind') != DATA_KIND:
        raise ValueError('Real sources are not enabled: source/basis authentication is required first')
    if metadata.get('history_coverage') != 'PARTIAL_SUPPLIED_HISTORY':
        raise ValueError('This engineering fixture adapter must explicitly disclose partial history')
    if not re.fullmatch(r'[a-z0-9_-]+', metadata.get('id', '')):
        raise ValueError('Explicit safe case id required')
    if not isinstance(metadata.get('label'), str) or not metadata['label'].strip():
        raise ValueError('Explicit source label required')
    # Validate the entire supplied source, then call the same core on each
    # prefix. A display adapter never guesses which result fields are causal.
    evaluate(payload)
    info = {k: deepcopy(metadata[k]) for k in ('id', 'label', 'data_kind', 'history_coverage')}
    info['price_mode'] = payload['context']['price_mode']
    info['reference_selection'] = 'EXPLICIT_SOURCE_FILE_SELECTION_NOT_AUTOMATIC'
    views = []
    for n in range(1, len(payload['observations']) + 1):
        prefix = deepcopy(payload)
        prefix['observations'] = prefix['observations'][:n]
        result = evaluate(prefix)
        chart = chart_prefix(prefix, result)
        selected = dict(schema_version='attempt-view-selection/0.1', adapter_version=VERSION,
                        core_version=CORE_VERSION, dataset=info, input_fingerprint=digest(prefix),
                        input=prefix, result=result, chart=chart,
                        classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED')
        # Python creates exact download bytes ahead of time. JS must never
        # round-trip original arbitrary-size integers through JSON.parse.
        selection_text = json.dumps(selected, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        frame = deepcopy(result['frames'][-1])
        frame.pop('source_observation')
        views.append(dict(frame=frame, events=deepcopy(result['events']), chart=chart,
                          presentation=presentation(result),
                          reference_details=encode(result['reference_set']),
                          context_details=encode(result['context']),
                          lineage=encode(dict(input_fingerprint=selected['input_fingerprint'],
                                              history_fingerprint=result['history_fingerprint'],
                                              frame_id=frame['frame_id'], previous_frame_id=frame['previous_frame_id'])),
                          selection_text=selection_text,
                          selection_sha256=sha256(selection_text.encode('utf-8')).hexdigest()))
    return dict(info=info, views=views)


def build_bundle(sources_path):
    sources_path = Path(sources_path).resolve()
    manifest = json.loads(sources_path.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 'attempt-view-sources/0.1' or not manifest.get('cases'):
        raise ValueError('Explicit nonempty attempt-view source manifest required')
    cases, provenance, seen = [], [], set()
    for metadata in manifest['cases']:
        if metadata['id'] in seen:
            raise ValueError('Duplicate source case id')
        seen.add(metadata['id'])
        path = (sources_path.parent / metadata['input']).resolve()
        if not path.is_relative_to(sources_path.parent):
            raise ValueError('Input must be below the explicit source manifest directory')
        raw = path.read_bytes()
        cases.append(build_case(json.loads(raw), metadata))
        provenance.append(dict(case_id=metadata['id'], input=metadata['input'], file_sha256=sha256(raw).hexdigest()))
    result = dict(schema_version='attempt-view-bundle/0.1', adapter_version=VERSION,
                  core_version=CORE_VERSION, data_kind=DATA_KIND, cases=cases, source_files=provenance,
                  classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED',
                  physical_android='NOT_TESTED', core_product_acceptance='NOT_ESTABLISHED')
    result['bundle_id'] = digest(result)
    return result


def render(payload):
    root = Path(__file__).resolve().parent
    raw = encode(payload)
    for char, escaped in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        raw = raw.replace(char, escaped)
    return (root / 'attempt_template.html').read_text(encoding='utf-8').replace(
        '@@STYLE@@', (root / 'attempt_viewer.css').read_text(encoding='utf-8')).replace(
        '@@SCRIPT@@', (root / 'attempt_viewer.js').read_text(encoding='utf-8')).replace('@@DATA@@', raw)


def export(payload, directory):
    directory = Path(directory)
    oracle = dict(bundle_id=payload['bundle_id'], cases=[dict(
        case_id=c['info']['id'], views=[dict(index=i, frame_id=v['frame']['frame_id'],
            observed_at=v['frame']['observed_at'], selection_sha256=v['selection_sha256'])
            for i, v in enumerate(c['views'])]) for c in payload['cases']])
    contents = {'attempt-candidate.json': encode(payload).encode('utf-8'),
                HTML_NAME: render(payload).encode('utf-8'),
                'attempt-selection-oracle.json': encode(oracle).encode('utf-8')}
    for name, data in contents.items():
        path = directory / name
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.read_bytes() != data)):
            raise ValueError('Refusing overwrite; use a new candidate output directory: ' + str(path))
    directory.mkdir(parents=True, exist_ok=True)
    receipt = {}
    for name, data in contents.items():
        path = directory / name
        if path.exists():
            receipt[name] = 'EXISTING'
            continue
        with path.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        receipt[name] = 'CREATED'
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    payload = build_bundle(args.sources)
    print(json.dumps(dict(status='EXPORTED', bundle_id=payload['bundle_id'],
                          cases=len(payload['cases']), views=sum(len(c['views']) for c in payload['cases']),
                          files=export(payload, args.output_dir)), ensure_ascii=False))


if __name__ == '__main__':
    main()
