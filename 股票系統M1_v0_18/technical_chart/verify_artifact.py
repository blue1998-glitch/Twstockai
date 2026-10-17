"""Read the actual shipped HTML, compare ALL saved evidence and old numbers."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from technical_chart.build import unpack, audit, selection, publish_immutable
from contracts import fingerprint
from cross_view_cli import read_config
from analysis_store import AnalysisStore


def verify(html, config, reference):
    content=Path(html).read_bytes()
    match=re.search(r'<script type="application/json" id="payload">(.*?)</script>',content.decode(),re.S)
    if not match:raise ValueError('Embedded transport missing')
    payload=unpack(json.loads(match.group(1)))
    # Previous delivered numeric candidate must remain byte-value identical.
    if payload['numbers']!=json.loads(Path(reference).read_text()):
        raise ValueError('Original delivered numbers changed')
    checks=[]
    for s in payload['numbers']['series']:
        saved=AnalysisStore(config['daily_stores'][s['store']]).load(s['original_record_id'])
        if audit(saved)!=payload['coverage'][s['key']]:raise ValueError('Coverage mismatch')
        snaps=saved['result']['components']['structure']['snapshots']
        if len(snaps)!=len(s['frames']):raise ValueError('Frame count mismatch')
        for i,(snap,f,e) in enumerate(zip(snaps,s['frames'],payload['evidence'][s['key']])):
            if e['pivots']!=snap['pivots'] or e['zones']!=snap['zones'] or e['snapshot_id']!=snap['snapshot_id']:
                raise ValueError('Evidence differs from saved source')
            for ordinal,event in enumerate(e['daily_events']):
                if event['original']!=snap['daily_events'][ordinal] or event['id']!=fingerprint(dict(snapshot_id=snap['snapshot_id'],ordinal=ordinal,event=event['original'])):
                    raise ValueError('Event provenance mismatch')
            if any(p['confirmed_at']>f['as_of'] for p in e['pivots']):raise ValueError('Future pivot')
            v=selection(payload,s['key'],f['as_of'])
            if len(v['analysis']['bars'])!=i+1 or v['analysis']['bars'][-1]['date']!=f['as_of']:
                raise ValueError('Replay prefix mismatch')
            if any(x['effective_date']>f['as_of'] for x in v['analysis']['known_events']):raise ValueError('Future action')
        checks.append(dict(code=s['code'],mode=s['price_mode'],frames=len(snaps),status='PASS'))
    return dict(status='PASS',source_html_sha256=hashlib.sha256(content).hexdigest(),
                original_numeric_bundle_exact_equal=True,frames=sum(c['frames'] for c in checks),series=checks,
                physical_android='NOT_TESTED',classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--html',required=True);p.add_argument('--config',required=True);p.add_argument('--reference-candidate',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    result=verify(a.html,read_config(a.config),a.reference_candidate)
    print(publish_immutable(a.report,json.dumps(result,ensure_ascii=False,indent=2).encode()))
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
