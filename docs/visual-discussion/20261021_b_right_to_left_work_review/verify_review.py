"""Audit saved source, scoped extrema, cutoff, and research-only claims."""
import json,hashlib
from decimal import Decimal as D
from pathlib import Path
from datetime import date
from pypdf import PdfReader
R=Path(__file__).resolve().parent
E=json.loads((R/'evidence.json').read_text());M=json.loads((R/'figure-manifest.json').read_text())
source=Path('/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json')
S=json.loads(source.read_text());bs=S['bars'];cut=E['as_of'];by={b['date']:b for b in bs}
assert hashlib.sha256(source.read_bytes()).hexdigest()==E['source_sha256']
assert len(bs)==len(by)==1213 and list(by)==sorted(by)
checks=[]
for scope in E['scopes'].values():
    a,z=scope['requested_start'],scope['requested_end']
    full=[b for b in bs if a<=b['date']<=z]
    prefix=[b for b in bs if b['date']<=cut and a<=b['date']<=z]
    assert full==prefix and len(full)==scope['saved_bars'] and z<=cut
    for k,fn in [('high',max),('low',min),('volume_shares_scaled',max)]:
        value=fn(D(b[k]) for b in full)
        assert D(scope[k]['value'])==value
        assert scope[k]['dates']==[b['date'] for b in full if D(b[k])==value]
    checks.append('all extrema/ties/counts/cutoff: '+a+'..'+z)
assert E['latest_bar']==by[cut]
v=D(E['latest_bar']['volume_shares_scaled'])
assert D('110000000')<v<D('146711672')<D('280910308')
assert D(E['latest_bar']['close'])<D('33.20')<D('35.40')<D('35.50')
assert E['scopes']['whole_observation']['high']==E['scopes']['whole_start_sensitivity']['high']
assert E['scopes']['whole_observation']['low']==E['scopes']['whole_start_sensitivity']['low']
assert E['scopes']['whole_observation']['volume_shares_scaled']!=E['scopes']['whole_start_sensitivity']['volume_shares_scaled']
trial=E['volume_baseline_trial'];assert trial['formal_baseline'] is None
assert trial['source_bars']==[by[d] for d in ['2025-12-22','2025-12-23','2025-12-24']]
assert all(E[k] is None for k in ['formal_bounds','formal_members','formal_merge'])
assert E['historical_signal_eligible'] is False
for f in M['figures']:
    assert (date.fromisoformat(f['last'])-date.fromisoformat(f['first'])).days>183
    assert f['last']==cut
    assert len([b for b in bs if f['first']<=b['date']<=cut])==f['bars']
    assert hashlib.sha256((R/f['image']).read_bytes()).hexdigest()==f['sha256']
p=R/'output/pdf/b-right-to-left-review.pdf';rd=PdfReader(p)
assert len(rd.pages)==3 and all(len(page.images)==0 for page in rd.pages)
assert hashlib.sha256(p.read_bytes()).hexdigest()==M['pdf_sha256']
out={'status':'PASS_SAVED_EVIDENCE_AND_ARTIFACT_CHECKS_ONLY','checks':checks+['strict price/volume separation','whole-start sensitivity','manual volume-line source exact','formal unknowns remain null','all three chart windows >6 months','three vector pages, no image objects, file hashes'],'builder_runs':1,'verifier_runs':1,'pdf_render_runs':1,'new_market_fetches':0,'core_or_classifier_runs':0,'android':'NOT_TESTED_NEW_BUILD','usefulness':'NOT_ESTABLISHED','classification':'NOT_VALIDATED','historical_signal_eligible':False}
(R/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
