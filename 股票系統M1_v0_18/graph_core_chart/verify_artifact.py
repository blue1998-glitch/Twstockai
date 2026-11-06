"""Re-read shipped HTML and independently replay every saved recognition prefix."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from graph_core_chart.build import ROOT,selection,input_for
from graph_core.core import analyze,fingerprint
from candle_region_chart.build import load_parent
from technical_chart.build import unpack
from product_candidate.build import publish_immutable


def verify(html,oracle):
    raw=Path(html).read_bytes();bundle=unpack(json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',raw.decode(),re.S).group(1)))
    parent=load_parent();frames=0;source_rows=0;details=[]
    for s in bundle['series']:
        old=next(v for v in parent['history_series'] if v['code']==s['code']);f=old['frames'][-1];base=old['bases'][f['chart_base']]
        for key in ['bars','macd','moving_averages']:
            if s[key]!=base[key]:raise ValueError('Original numeric source changed: '+key)
        inp=input_for(old,f)
        for result in s['results']:
            if analyze(inp,as_of=result['as_of'])!=result:raise ValueError('Saved recognition prefix mismatch')
            original=next(v for v in old['frames'] if v['as_of']==result['as_of'])
            if s['numeric_frame_ids'][result['as_of']]!=original['frame_id']:raise ValueError('Source frame identity mismatch')
            frames+=1
        source_rows+=len(s['bars']);details.append(dict(code=s['code'],bars=len(s['bars']),analysis_frames=len(s['results']),latest_boxes=len(s['results'][-1]['boxes']),
            latest_frontier=len(s['results'][-1]['comparison']['pareto_frontier_ids']),source_id=s['source']['id'],numeric_exact_equal=True))
    cases=json.loads(Path(oracle).read_text())['cases']
    for c in cases:
        if fingerprint(selection(bundle,c['code'],c['as_of']))!=c['fingerprint']:raise ValueError('Download selection oracle mismatch')
    return dict(status='PASS',source_html_sha256=hashlib.sha256(raw).hexdigest(),source_rows=source_rows,recognition_prefixes_recomputed=frames,
        selection_oracles=len(cases),series=details,original_OHLCV_MACD_SMA_and_frame_ids_preserved=True,
        manual_cases_outside_automatic_input=True,accuracy='NOT_EVALUATED',core_usefulness='NOT_ESTABLISHED',physical_android='NOT_TESTED_NEW_BUILD')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--html',required=True);p.add_argument('--oracle',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    report=verify(a.html,a.oracle);print(publish_immutable(a.report,json.dumps(report,ensure_ascii=False,indent=2).encode()));print(json.dumps(report,ensure_ascii=False,indent=2))
