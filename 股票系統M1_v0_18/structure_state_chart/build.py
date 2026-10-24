"""Offline P0-3 producer and incremental rendering over manual_basis_chart."""
import argparse
import base64
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from graph_core.core import fingerprint
from manual_basis_chart.build import load_parent, catalogue_from, render as manual_render
from product_candidate.build import publish_immutable
from structure_state.source import prepare
from structure_state.core import evaluate

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).parent
NAME = 'M1_P03_structure_state_v01.html'


def build(out, choice_path=None, data_path=None):
    choice_path = Path(choice_path or ROOT / 'structure_state/examples/retained-case.json').resolve()
    data_path = Path(data_path or ROOT / 'cross_scale_chart/generated/comparison-data.json').resolve()
    original = json.loads(data_path.read_text()); choice = json.loads(choice_path.read_text())
    facts_input, scenario = prepare(original, choice)
    states = evaluate(facts_input, scenario, as_of=choice['display']['analysis_date'])
    html, match, parent = load_parent(); catalogue = catalogue_from(parent)
    candidates = [s for s in [*parent['numbers']['series'], *parent['history_series']]
                  if s['source']['id'] == original['source']['id'] and s['code'] == original['code']]
    matching = []
    for series in candidates:
        frames = [f for f in series['frames'] if f['as_of'] == states['as_of'] and f['chart_base'] == original['price_basis_id']]
        if frames:
            matching.append((series, frames[0]))
    if len(matching) != 1:
        raise ValueError('Explicit P0-3 source has no unique matching existing chart')
    series, frame = matching[0]; base = series['bases'][frame['chart_base']]
    n = frame['index'] + 1
    if (base['bars'][:n] != original['bars'] or base['macd'][:n] != original['macd']
        or {k:v[:n] for k,v in base['moving_averages'].items()} != original['moving_averages']
        or frame['frame_id'] != original['source_frame_id']):
        raise ValueError('Existing chart OHLCV/MA/MACD/frame is not exactly this source')
    frame_map = {}
    for f in series['frames'][:n]:
        if f['chart_base'] == original['price_basis_id']:
            frame_map[f['as_of']] = dict(frame_id=f['frame_id'],
                                         source_prefix_fingerprint=fingerprint(base['bars'][:f['index']+1]))
    artifact = dict(schema_version='p03-existing-chart-layer/0.1', case=choice, result=states,
                    series_key=series['key'], frame_map=frame_map,
                    source_data_path=str(data_path.relative_to(ROOT)) if data_path.is_relative_to(ROOT) else data_path.name,
                    source_data_file_sha256=hashlib.sha256(data_path.read_bytes()).hexdigest(),
                    original_comparison_artifact_id=original['artifact_id'],
                    catalogue_id=catalogue['catalogue_id'], parent_artifact_id=parent['artifact_id'],
                    indicator_values_recomputed=False, original_numeric_tree_changed=False,
                    physical_android='NOT_TESTED_NEW_BUILD')
    artifact['artifact_id'] = fingerprint(artifact)
    # Reuse the complete existing manual mode router and viewer; no second UI.
    rendered = manual_render(html, match, catalogue).decode()
    encoded = base64.b64encode(gzip.compress(json.dumps(artifact,ensure_ascii=False,separators=(',',':')).encode(),mtime=0)).decode()
    patch = "\nconst p03Compressed=Uint8Array.from(atob('"+encoded+"'),x=>x.charCodeAt(0));\n"
    patch += "const p03Data=JSON.parse(await new Response(new Blob([p03Compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).text());\n"
    patch += (HERE/'patch.js').read_text()
    end = rendered.rfind('})().catch(')
    if end < 0:
        raise ValueError('Manual chart extension hook missing')
    rendered = rendered[:end] + patch + '\n' + rendered[end:]
    rendered = rendered.replace('<title>', '<title>P0-3結構狀態｜', 1)
    files = {NAME:rendered.encode(), 'structure-state.json':json.dumps(states,ensure_ascii=False,separators=(',',':')).encode(),
             'chart-layer.json':json.dumps(artifact,ensure_ascii=False,separators=(',',':')).encode(),
             'role-selection.json':choice_path.read_bytes(),
             'facts-input.json':json.dumps(facts_input,ensure_ascii=False,separators=(',',':')).encode(),
             'scenario.json':json.dumps(scenario,ensure_ascii=False,indent=2).encode()}
    report = dict(schema_version='p03-chart-build-verification/0.1', status='PASS',
                  source_series_key=series['key'], source_id=original['source']['id'],
                  price_basis_id=original['price_basis_id'], source_frame_id=original['source_frame_id'],
                  parent_interned_payload_sha256=hashlib.sha256(match.group(1).encode()).hexdigest(),
                  parent_numeric_tree_preserved=True, source_and_indicators_exactly_equal=True,
                  state_records=len(states['records']), events=len(states['events']),
                  state_counts={s:sum(x['state']==s for x in states['records']) for s in ['STRENGTHENING','CONSOLIDATING','WEAKENING','INSUFFICIENT']},
                  real_case_missing_states=[s for s in ['STRENGTHENING','CONSOLIDATING','WEAKENING'] if not any(r['state']==s for r in states['records'])]
                    + ([] if any(r['equal_boundaries'] for r in states['records'] if r['date']>=scenario['post_breakout_return']['known_on']) else ['EQUALITY_BOUNDARY']),
                  role_qualification=states['source_qualification'], full_market_accuracy_tested=False,
                  new_indicators_or_automatic_reference_selection=False, physical_android='NOT_TESTED_NEW_BUILD',
                  files={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in files.items()})
    files['build-verification.json']=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
    for name, body in files.items():
        publish_immutable(out/name,body)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return artifact


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--selection',type=Path);parser.add_argument('--data',type=Path)
    args=parser.parse_args();build(args.output_dir,args.selection,args.data)
