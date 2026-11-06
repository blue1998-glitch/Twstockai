"""Explicit before/after F-01 evidence; no HTTP, no historical result rewrites.

Real outputs always remain outside Git; public summaries contain no quote values.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from graph_core.core import analyze, fingerprint, VERSION
from graph_core.finmind_run import _retained_sources, external_path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
BOX_FIELDS = ('pressure_distance_fraction', 'relative_width_to_anchor')
STOP = 'OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP'


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def stable_fingerprint(result):
    """Every value except the exact pre-authorized F-01 delta whitelist."""
    value = deepcopy(result)
    value.pop('schema_version'); value.pop('result_id')
    for box in value['boxes']:
        for key in (*BOX_FIELDS, 'anchor_comparison_reason'): box.pop(key, None)
    for ref in value['reference_candidates']:
        for key in ('distance_to_anchor', 'anchor_comparison_reason'): ref.pop(key, None)
    return fingerprint(value)


def state(result):
    return dict(stable_fingerprint=stable_fingerprint(result),
        boxes=[dict(id=b['id'], usable=b['usable_at_anchor'],
                    **{k: b[k] for k in BOX_FIELDS}) for b in result['boxes']],
        references=[dict(id=r['pivot_id'], stopped=r['path']['last_relation']=='NOT_COMPARABLE_AFTER_GAP',
                         distance_to_anchor=r['distance_to_anchor']) for r in result['reference_candidates']])


def summary(result):
    boxes = [b for b in result['boxes'] if not b['usable_at_anchor']]
    refs = [r for r in result['reference_candidates'] if r['path']['last_relation']=='NOT_COMPARABLE_AFTER_GAP']
    relevant = result['comparison']['relevant_pressure_ids']
    return dict(version=result['schema_version'], as_of=result['as_of'], source_records=result['source_records'],
        incomparable_boxes=len(boxes), stopped_high_references=len(refs),
        non_null_old_box_pressure_distances=sum(b['pressure_distance_fraction'] is not None for b in boxes),
        non_null_old_box_relative_widths=sum(b['relative_width_to_anchor'] is not None for b in boxes),
        non_null_stopped_reference_distances=sum(r['distance_to_anchor'] is not None for r in refs),
        incomparable_boxes_excluded_from_current_pressure=all(b['id'] not in relevant for b in boxes),
        primary_pressure_id=result['comparison']['primary_pressure_id'],
        classification_quality=result['classification_quality'], action_qualification=result['action_qualification'])


def check_after(before, result):
    expected = json.loads((HERE / 'expected.json').read_text())
    assert result['schema_version'] == expected['new_result_version']
    assert stable_fingerprint(result) == before['stable_fingerprint']
    assert [b['id'] for b in result['boxes']] == [b['id'] for b in before['boxes']]
    assert [r['pivot_id'] for r in result['reference_candidates']] == [r['id'] for r in before['references']]
    for old, box in zip(before['boxes'], result['boxes']):
        assert box['anchor_comparison_reason'] == (None if old['usable'] else expected['reason'])
        for field in BOX_FIELDS:
            assert box[field] == (old[field] if old['usable'] else None)
    for old, ref in zip(before['references'], result['reference_candidates']):
        assert ref['anchor_comparison_reason'] == (expected['reason'] if old['stopped'] else None)
        assert ref['distance_to_anchor'] == (None if old['stopped'] else old['distance_to_anchor'])
    assert result['comparison']['primary_pressure_id'] is None
    return dict(all_other_result_values_unchanged=True, all_object_ids_and_order_unchanged=True,
                comparable_numbers_unchanged=True, incomparable_numbers_null=True,
                stop_reasons_retained=True, primary_pressure_id=None)


def official_payload():
    # Reuse retained original source checks only; no FinMind response or API call.
    bars, bindings, warnings = _retained_sources()
    return dict(schema_version='graph-recognition-input/0.1',
                context=dict(code='2884', source_id='RETAINED_TWSE_2884_F01',
                             price_basis_id='TWSE_RAW_ACTION_TYPE_UNKNOWN', price_mode='RAW_CANDIDATE',
                             volume_unit='SHARES_REPORTED', corporate_action_comparability='UNKNOWN'),
                bars=bars, expected_dates=[r['date'] for r in bars],
                basis_break_dates=[w['date'] for w in warnings]), bindings


def capture(phase, private_dir):
    assert phase in ('before', 'after')
    assert VERSION == ('graph-recognition-research/0.1' if phase=='before'
                       else 'graph-recognition-research/0.2')
    private = external_path(private_dir)
    if phase == 'before': private.mkdir(mode=0o700, parents=True, exist_ok=False)
    source = PROJECT / 'graph_core/core.py'
    source_version = dict(version=VERSION, core_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    frozen = json.loads((HERE / 'baseline.json').read_text())
    for name, digest in frozen['frozen'].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest
    before_synthetic = json.loads((HERE/'synthetic-before.json').read_text()) if phase=='after' else None
    synthetic = []
    for index, case in enumerate(json.loads((HERE/'cases.json').read_text())):
        result = analyze(case['input'], as_of=case['as_of']); overview = summary(result)
        assert bool(overview['incomparable_boxes']) == case['expected_stopped']
        assert bool(overview['stopped_high_references']) == case['expected_stopped']
        item = dict(id=case['id'], summary=overview, fields=state(result))
        if phase=='after': item['preservation'] = check_after(before_synthetic['cases'][index]['fields'], result)
        synthetic.append(item)
    write_new(HERE/f'synthetic-{phase}.json', dict(source_kind='SYNTHETIC_ONLY',
              source_version=source_version, cases=synthetic))
    payload, bindings = official_payload()
    real, public = [], []
    old_real = json.loads((private/'official-before.json').read_text()) if phase=='after' else None
    for index, day in enumerate(('2026-07-21', '2026-07-22')):
        result = analyze(payload, as_of=day); overview = summary(result)
        assert overview['incomparable_boxes'] > 0 and overview['stopped_high_references'] > 0
        item = dict(input=payload, as_of=day, result=result)
        if phase=='after':
            assert old_real['cases'][index]['input'] == payload
            overview['preservation'] = check_after(state(old_real['cases'][index]['result']), result)
        real.append(item); public.append(overview)
    write_new(private/f'official-{phase}.json', dict(source_version=source_version,
              source_bindings=bindings, cases=real))
    write_new(HERE/f'official-{phase}-summary.json', dict(source_kind='RETAINED_OFFICIAL_NOT_FINMIND',
              source_version=source_version, raw_or_reconstructable_quotes_published=False,
              historical_available_at='UNKNOWN', corporate_action_type='UNKNOWN',
              data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
              policy_authorized=False, live_execution_authorized=False,
              cases=public))
    if phase=='before':
        with (private/'core-before.py').open('xb') as stream: stream.write(source.read_bytes())
    print(json.dumps(dict(phase=phase, synthetic_cases=len(synthetic),
                         official_non_quote_summary=public), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('before', 'after'))
    parser.add_argument('--private-dir', required=True)
    args = parser.parse_args(); capture(args.phase, args.private_dir)
