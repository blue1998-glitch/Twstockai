"""Compare one supplied Android export with pinned release producer functions.
No application/store mutation, browser execution, or independent source recapture.
"""
import ast
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--html', type=Path, default=HERE / 'M1_v0_19_pressure_chart.html')
p.add_argument('--evidence-dir', type=Path, default=HERE.parent / 'upload')
p.add_argument('--source-root', type=Path, help='Pinned 股票系統M1_v0_18 directory; otherwise use local source_* cache')
args = p.parse_args()
UPLOAD = args.evidence_dir
def source_text(filename):
    if args.source_root:
        relative = {'source_technical_chart_build.py': 'technical_chart/build.py', 'source_pressure_chart_build.py': 'pressure_chart/build.py', 'source_pressure_chart_history_adapter.py': 'pressure_chart/history_adapter.py'}[filename]
        return (args.source_root / relative).read_text()
    return (HERE / filename).read_text()
namespace = {'deepcopy': deepcopy}
for filename, names in [
    ('source_technical_chart_build.py', ['unpack']),
    ('source_pressure_chart_history_adapter.py', ['history_selection']),
    ('source_pressure_chart_build.py', ['selection']),
]:
    tree = ast.parse(source_text(filename))
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(body) == len(names)
    exec(compile(ast.Module(body=body, type_ignores=[]), filename, 'exec'), namespace)

html_bytes = args.html.read_bytes()
assert hashlib.sha256(html_bytes).hexdigest() == '0b66a00c7b72c559973fd37011fee5a39b5ab933d04fc2bcc9347748ec65e430'
transport = json.loads(re.search(r'<script type="application/json" id="payload">(.*?)</script>', html_bytes.decode(), re.S).group(1))
payload = namespace['unpack'](transport)
namespace.update(VERSION=payload['view_version'], FACT_VERSION=payload['facts_version'])
# history_selection's module VERSION differs from the view VERSION; bind its globals separately.
history_ns = {'deepcopy': deepcopy, 'VERSION': 'official-raw-indicator-candidate/0.1'}
tree = ast.parse(source_text('source_pressure_chart_history_adapter.py'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'history_selection'], type_ignores=[]), '<pinned history_selection>', 'exec'), history_ns)
namespace['history_selection'] = history_ns['history_selection']
json_path = UPLOAD / 'M1_1101_RAW_CANDIDATE_2026-10-16.json'
raw = json_path.read_bytes()
actual = json.loads(raw)
series = next(s for s in payload['history_series'] if s['code'] == '1101')
expected = namespace['selection'](payload, series['key'], '2026-10-16')
assert actual == expected, 'Parsed export differs from pinned release selection'
analysis = actual['new_history_analysis']
bars = analysis['bars']
assert len(bars) == 1213 and bars[0]['date'] == '2021-10-18' and bars[-1]['date'] == '2026-10-16'
assert len(analysis['macd']) == 1213 and all(len(v) == 1213 for v in analysis['moving_averages'].values())
assert all(r['date'] <= '2026-10-16' for r in bars)
assert actual['saved_analysis'] is None and actual['retrospective_review'] is None
canonical = json.dumps(actual, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
from decimal import Decimal
high = max(bars, key=lambda r: Decimal(r['high']))
volume = max(bars, key=lambda r: Decimal(r['volume_shares_scaled']))
image_path = UPLOAD / '01-Screenshot_20261018-140856.png'
report = {
    'status': 'PASS_ONE_UPLOADED_EXPORT_PARSED_VALUE_EQUALITY',
    'comparison_scope': 'Full parsed JSON equals exact pinned release producer selection; not byte serialization equality; not independent OHLCV or indicator recomputation',
    'source_commit': '3942950f95f4fe9c8dc81e6dbc3a928be08fb59d',
    'product_baseline': 'b9c38d6fbd56257f41e28657cf5fd6bd88e1ad3b',
    'html_sha256': hashlib.sha256(html_bytes).hexdigest(),
    'upload': {'filename': json_path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'canonical_sha256': hashlib.sha256(canonical).hexdigest()},
    'screenshot': {'filename': image_path.name, 'bytes': image_path.stat().st_size, 'sha256': hashlib.sha256(image_path.read_bytes()).hexdigest()},
    'schema': actual['schema_version'], 'as_of': analysis['frame']['as_of'],
    'series_key': series['key'], 'source_id': analysis['source']['id'],
    'bars': len(bars), 'first': bars[0], 'last': bars[-1],
    'macd_rows': len(analysis['macd']), 'moving_average_rows': {k: len(v) for k,v in analysis['moving_averages'].items()},
    'highest_raw_bar': high, 'highest_daily_volume_bar': volume,
    'all_exported_bars_not_after_analysis_date': True,
    'saved_analysis_null': True, 'retrospective_review_null': True,
    'retrospective_followup_present': actual['retrospective_followup'] is not None,
    'android_overall': 'PARTIAL_EVIDENCE_OBSERVED',
    'not_tested': ['rotation', 'gesture interactions', 'zoom button interactions', 'return recent', 'source locate/evidence interactions', 'stock/basis switch', 'historical replay leakage across other dates', 'performance', 'core analysis acceptance'],
}
(HERE / 'phone-export-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
