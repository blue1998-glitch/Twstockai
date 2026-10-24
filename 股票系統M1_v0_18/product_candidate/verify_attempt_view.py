"""Check actual exported viewer bytes against source prefixes and the pure core.

No database/old engine access. The output is engineering evidence, not trading
classification or physical-device acceptance.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from product_candidate.attempt_evidence import evaluate, VERSION as CORE_VERSION
from product_candidate.attempt_view import HTML_NAME, render, digest


def verify(sources_path, directory):
    sources_path, directory = Path(sources_path), Path(directory)
    sources = json.loads(sources_path.read_text())
    bundle = json.loads((directory/'attempt-candidate.json').read_text())
    oracle = json.loads((directory/'attempt-selection-oracle.json').read_text())
    assert bundle['bundle_id'] == digest({k: v for k, v in bundle.items() if k != 'bundle_id'})
    assert bundle['core_version'] == CORE_VERSION
    assert oracle['bundle_id'] == bundle['bundle_id']
    html = (directory/HTML_NAME).read_bytes()
    assert html == render(bundle).encode('utf-8'), 'HTML does not match current source/data'
    assert [c['info']['id'] for c in bundle['cases']] == [c['id'] for c in sources['cases']]
    assert [c['case_id'] for c in oracle['cases']] == [c['id'] for c in sources['cases']]
    checks = []
    for metadata, case, expected_oracle, provenance in zip(sources['cases'], bundle['cases'], oracle['cases'], bundle['source_files']):
        raw = (sources_path.parent/metadata['input']).read_bytes()
        assert sha256(raw).hexdigest() == provenance['file_sha256']
        original = json.loads(raw)
        assert len(case['views']) == len(original['observations']) == len(expected_oracle['views'])
        for i, (view, row) in enumerate(zip(case['views'], expected_oracle['views'])):
            prefix = deepcopy(original); prefix['observations'] = prefix['observations'][:i+1]
            core = evaluate(prefix)
            selected = json.loads(view['selection_text'])
            assert selected['input'] == prefix
            assert selected['input_fingerprint'] == digest(prefix)
            assert selected['result'] == core
            assert view['selection_sha256'] == row['selection_sha256'] == sha256(view['selection_text'].encode('utf-8')).hexdigest()
            assert row['frame_id'] == view['frame']['frame_id'] == core['frames'][-1]['frame_id']
            assert view['events'] == core['events']
            # Independent check of the supplied cumulative/final bars: one row
            # for each actual source date, never a synthetic date or price.
            by_date = {r['date']:r for r in prefix['history']}
            by_date.update({r['date']:r for r in prefix['observations']})
            chart = view['chart']; assert chart == selected['chart']
            assert [r['date'] for r in chart['daily']] == list(by_date)
            for bar in chart['daily']:
                source = by_date[bar['date']]
                for key in ('open','high','low','close'):
                    value = source.get('close',source.get('last')) if key == 'close' else source[key]
                    assert Decimal(bar[key]) == Decimal(value)
                expected_volume = source.get('volume_shares')
                assert (None if expected_volume is None else Decimal(expected_volume)) == (
                    None if bar['volume_shares'] is None else Decimal(bar['volume_shares']))
                assert bar['is_close'] == source.get('is_close',True)
                assert bar['known_at'] == source.get('observed_at',source.get('known_at'))
            today = [r for r in prefix['observations'] if r['date'] == prefix['observations'][-1]['date']]
            expected_points = today if any(not r['is_close'] for r in today) else []
            assert [p['observed_at'] for p in chart['intraday']['points']] == [p['observed_at'] for p in expected_points]
            assert [Decimal(p['price']) for p in chart['intraday']['points']] == [Decimal(p['last']) for p in expected_points]
            assert all(e['observation_index'] <= i for e in core['events'])
            assert all(f['probability_estimate'] is None and f['action_qualification'] == 'NOT_EVALUATED' for f in core['frames'])
            shortened_case_views = case['views'][:i+1]
            for j, earlier in enumerate(shortened_case_views):
                assert json.loads(earlier['selection_text'])['result'] == evaluate(dict(prefix, observations=prefix['observations'][:j+1]))
            checks.append(dict(case_id=metadata['id'], observation_index=i, observed_at=core['frames'][-1]['observed_at'],
                               frame_id=row['frame_id'], selection_sha256=view['selection_sha256'],status='PASS'))
    return dict(status='PASS', verified_at_utc=datetime.now(timezone.utc).isoformat(),
                core_version=CORE_VERSION, bundle_id=bundle['bundle_id'], html_sha256=sha256(html).hexdigest(),
                source_kind='SYNTHETIC_ENGINEERING_FIXTURE', cases=len(bundle['cases']), views=len(checks), checks=checks,
                exact_core_prefixes=True, source_integer_and_decimal_precision_preserved=True,
                fabricated_intraday_points=0, physical_android='NOT_TESTED', classification_quality='NOT_VALIDATED',
                action_qualification='NOT_EVALUATED', core_product_acceptance='NOT_ESTABLISHED')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources',required=True,type=Path)
    parser.add_argument('--candidate-dir',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    args = parser.parse_args()
    report = verify(args.sources,args.candidate_dir)
    with args.report.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
