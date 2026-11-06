"""Read-only real-store replay checks and independent browser-download oracle.

These checks establish engineering provenance/causality, not market-label accuracy.
No original analysis run, worker, recovery, or database write is invoked.
The existing price projection helper is used only in the separate candidate.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from analysis_store import AnalysisStore
from contracts import fingerprint
from cross_view_cli import read_config
from product_candidate.build import series_from_saved, selection_payload


def verify(folder, config_path):
    folder = Path(folder)
    payload = json.loads((folder / 'candidate.json').read_text())
    expected_id = payload['bundle_id']
    assert fingerprint({k: v for k, v in payload.items() if k != 'bundle_id'}) == expected_id
    config = read_config(config_path)
    report = dict(status='PASS', bundle_id=expected_id, checks=[], real_examples=[],
                  classification_quality='NOT_VALIDATED', product_acceptance='NOT_ESTABLISHED',
                  interpretation='Observed saved facts and prefix invariance, not retrospectively labelled pattern accuracy')
    oracle = dict(bundle_id=expected_id, cases=[])
    counts = Counter()
    for series in payload['series']:
        saved = AnalysisStore(config['daily_stores'][series['store']]).load(series['original_record_id'])
        assert fingerprint(saved['result']) == series['original_result_fingerprint']
        snapshots = saved['result']['components']['structure']['snapshots']
        ma = saved['result']['components']['daily_ma']['snapshots']
        previous = None
        for i, frame in enumerate(series['frames']):
            assert frame['frame_id'] == fingerprint({k: v for k, v in frame.items() if k != 'frame_id'})
            assert frame['previous_frame_id'] == previous
            assert frame['structure_snapshot_id'] == snapshots[i]['snapshot_id']
            assert frame['ma_snapshot_id'] == ma[i]['snapshot_id']
            assert frame['daily_events'] == snapshots[i]['daily_events']
            assert frame['pending'] == snapshots[i].get('pending', [])
            assert frame['lifecycle']['stage'] == 'UNKNOWN' and frame['action_qualification'] == 'NOT_EVALUATED'
            selected = selection_payload(payload, series['key'], frame['as_of'])
            assert len(selected['bars']) == len(selected['macd']) == i + 1
            assert selected['bars'][-1]['date'] == frame['as_of']
            assert all(e['effective_date'] <= frame['as_of'] for e in selected['known_events'])
            assert [r.get('volume_shares_scaled') for r in selected['bars']] == [
                r.get('volume_shares_scaled') for r in saved['request']['candles'][:i+1]]
            assert selected['moving_averages'] == ma[i]['curves']
            assert frame['momentum']['histogram'] == selected['macd'][-1]['histogram']
            assert frame['momentum']['previous_histogram_same_anchor'] == (
                selected['macd'][-2]['histogram'] if i else None)
            assert all(p['confirmed_at'] <= frame['as_of'] for p in snapshots[i]['pivots'])
            counts[frame['structure']['candidate_state']] += 1
            previous = frame['frame_id']
        # Truncate REAL saved prefixes without rerunning original engines. Reuse
        # only precisely saved period observations; no nearest-date substitution.
        background = {}
        from cross_view import catalog
        existing = catalog(config)
        daily = {d['key']: d for d in existing['daily']}
        periods = {p['key']: p for p in existing['period']}
        for view in existing['views']:
            if view['daily_key'] not in daily or view['period_key'] not in periods:
                continue
            d, p = daily[view['daily_key']], periods[view['period_key']]
            if d['store'] == series['store'] and d['record_id'] == saved['record_id']:
                background[(d['store'], d['record_id'], d['as_of'])] = dict(
                    alignment_status=view['status'], analysis_id=p['analysis_id'],
                    record_fingerprint=p['record']['record_fingerprint'], snapshot=p['record']['result']['snapshot'])
        for n in (91, 151):
            truncated = deepcopy(saved)
            truncated['request']['candles'] = truncated['request']['candles'][:n]
            truncated['result']['components']['structure']['snapshots'] = snapshots[:n]
            truncated['result']['components']['daily_ma']['snapshots'] = ma[:n]
            replay = series_from_saved(truncated, series['store'], background)
            assert replay['frames'] == series['frames'][:n]
            for frame in replay['frames']:
                key, end = frame['chart_base'], frame['index'] + 1
                for field in ('bars', 'macd'):
                    assert replay['bases'][key][field][:end] == series['bases'][key][field][:end]
            report['checks'].append(dict(kind='REAL_SAVED_PREFIX_INVARIANCE', code=series['code'],
                                         mode=series['price_mode'], prefix=n, through=replay['frames'][-1]['as_of']))
        for i in (0, 33, 90, len(series['frames']) - 1):
            frame = series['frames'][i]
            selected = selection_payload(payload, series['key'], frame['as_of'])
            oracle['cases'].append(dict(series=series['key'], as_of=frame['as_of'], frame_id=frame['frame_id'],
                                        selection_fingerprint=fingerprint(selected)))
        latest = series['frames'][-1]
        report['real_examples'].append(dict(code=series['code'], mode=series['price_mode'],
            date=latest['as_of'], frame_id=latest['frame_id'], original_record_id=series['original_record_id'],
            structure_snapshot_id=latest['structure_snapshot_id'], structure=latest['structure'],
            opposing=latest['opposing'], missing=latest['missing']))
    report.update(frames_checked=sum(len(s['frames']) for s in payload['series']),
                  series_checked=len(payload['series']), observed_state_counts=dict(counts), oracle_cases=len(oracle['cases']))
    # Historical baseline is immutable. Known earlier UI/docs changes remain
    # visible as differences; do not certify the whole checkout as baseline.
    manifest = json.loads((ROOT / 'output/交付檔案指紋.json').read_text())
    mismatches, verified = [], []
    for item in manifest['files']:
        path = ROOT / item['file']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            mismatches.append(item['file'])
        else:
            verified.append(item['file'])
    # Those two exporters already differ in the incoming v0.18 annotation
    # commit. Numeric engines, stores and original pages must match baseline;
    # ALL old src files (including the two exporters) must also match Git HEAD.
    earlier_exporters = {'src/cross_view_cli.py', 'src/cross_view_export.py'}
    protected = [f for f in verified + mismatches if (f.startswith('src/') and f not in earlier_exporters)
                 or f.endswith(('.sqlite3', '.html'))]
    assert not set(protected).intersection(mismatches), 'Original engine/database/page changed'
    subprocess.run(['git', 'diff', 'HEAD', '--exit-code', '--', 'src/'], cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    report['historical_manifest'] = dict(entries=len(manifest['files']), exact_matches=len(verified),
        differences=mismatches, protected_engine_database_html_checked=len(protected),
        protected_status='ALL_MATCH', old_src_vs_git_head='ALL_MATCH', compared_git_head=head,
        whole_checkout_baseline='NOT_CLAIMED')
    (folder / 'selection-oracle.json').write_text(json.dumps(oracle, ensure_ascii=False, indent=2))
    (folder / 'saved-replay-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ('real_examples', 'checks')}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-dir', required=True)
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    verify(args.candidate_dir, args.config)
