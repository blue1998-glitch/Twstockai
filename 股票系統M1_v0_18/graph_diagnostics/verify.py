"""Verify shipped transport, unchanged original core, and every diagnostic prefix."""
import argparse
import hashlib
import json
from pathlib import Path
from graph_core.core import analyze,fingerprint
from graph_core_chart.build import display_ids
from product_candidate.build import publish_immutable
from .build import load_html,PARENT,PARENT_SHA,input_for,selection
from .diagnose import diagnose


def verify(html,oracle):
    bundle=load_html(html);old=load_html(PARENT);count=0;details=[]
    if fingerprint({k:v for k,v in bundle.items() if k!='artifact_id'})!=bundle['artifact_id']: raise ValueError('New artifact identity')
    for s,original in zip(bundle['series'],old['series'],strict=True):
        if {k:v for k,v in s.items() if k!='diagnostics'}!=original: raise ValueError('Old series changed')
        p=input_for(s)
        for r in s['results']:
            if analyze(p,as_of=r['as_of'])!=r: raise ValueError('Original core re-execution mismatch')
            d=s['diagnostics'][r['as_of']]
            if diagnose(p,r)!=d: raise ValueError('Diagnostic recomputation mismatch')
            if d['presentation']['selected_ids']!=display_ids(r)['ids']: raise ValueError('UI criterion trace mismatch')
            count+=1
        d=s['diagnostics'][s['results'][-1]['as_of']]
        details.append(dict(code=s['code'],bars=len(s['bars']),prefixes=len(s['results']),latest=d['summary'],
            latest_core_result_id=s['results'][-1]['result_id'],latest_diagnostic_id=d['diagnostic_id']))
        print('Verified',s['code'],flush=True)
    cases=json.loads(Path(oracle).read_text())['cases']
    for c in cases:
        if fingerprint(selection(bundle,c['code'],c['as_of']))!=c['fingerprint']: raise ValueError('Download oracle mismatch')
    return dict(status='PASS',html_sha256=hashlib.sha256(Path(html).read_bytes()).hexdigest(),
        immutable_parent_html_sha256=PARENT_SHA,original_series_all_fields_equal=True,
        core_prefixes_recomputed=count,diagnostic_prefixes_recomputed=count,oracles=len(cases),
        series=details,physical_android='NOT_TESTED_NEW_BUILD',accuracy='NOT_EVALUATED',core_usefulness='NOT_ESTABLISHED')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--html',required=True);p.add_argument('--oracle',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    value=verify(a.html,a.oracle);print(publish_immutable(a.report,json.dumps(value,ensure_ascii=False,indent=2).encode()))
