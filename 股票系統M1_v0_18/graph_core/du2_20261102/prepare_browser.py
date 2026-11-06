"""Ephemeral M-MOB1 service: original saved charts + clearly synthetic study batches.
Never deploys. Credentials and decoded expected chart values stay outside Git.
"""
import json,os,secrets,signal,sys,re
from pathlib import Path
from graph_core.market_daily import encode
from graph_core_chart.mobile_private import create_auth,make_server,external
from rotation_research import artifact_codec as c
from technical_chart.interned_json import unpack

study=Path(sys.argv[1]);source=Path(sys.argv[2]);out=external(sys.argv[3]);out.mkdir(parents=True,exist_ok=False)
info=json.loads((study/'STUDY_PRIVATE.json').read_bytes());original=json.loads((source/'fm3-continuation.json').read_bytes());measure=json.loads((study/'compact-measurement-private.json').read_bytes())['measurements'];codes=[x['code'] for x in info['selected'] if x['stratum'] in ('TWSE-0.5','TPEX-0.5')]
pages=[dict(run_id=original['result']['id'],as_of='2026-10-30',**{k:original['preview'][k] for k in ('path','sha256','bytes')},synthetic_new_day=False)]
for i,m in enumerate(measure):pages.append(dict(run_id='SYNTHETIC_STUDY_'+m['id'],as_of=['2026-11-03','2026-11-04'][i],**{k:m['private_preview'][k] for k in ('path','sha256','bytes')},synthetic_new_day=True))
catalogue=out/'study-batches.json';catalogue.write_bytes(encode(dict(schema='private-saved-batches/0.1',batches=list(reversed(pages)))))
auth=out/'test-auth.json';password=secrets.token_urlsafe(32);create_auth(auth,'du2tester',password)
server=make_server(None,auth,batches=catalogue);cases=[]
for i,page in enumerate(pages):
 raw=c.read_bytes(page['path']);state=json.loads(re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)[1]);stocks=[]
 for code in codes:
  row=next(s for s in state['stocks'] if s['code']==code);d=row['preview_series'];p=Path(page['path']).parent/d['path']
  decoded=unpack(json.loads(c.read_bytes(p,expected_bytes=d['bytes'],expected_sha=d['sha256'])))
  expected=out/(str(i)+'-'+code+'-expected-private.json');expected.write_bytes(encode(decoded))
  stocks.append(dict(code=code,expected=str(expected),records=len(decoded['bars'])))
 cases.append(dict(route='/batch-'+page['sha256']+'/'+Path(page['path']).name,as_of=page['as_of'],expected_count=len(state['stocks']),stocks=stocks,synthetic_new_day=page['synthetic_new_day']))
config=dict(origin='http://127.0.0.1:'+str(server.server_port),httpCredentials=dict(username='du2tester',password=password),batches=cases)
p=out/'browser-input.json';p.write_bytes(encode(config));os.chmod(p,0o600);print(str(p),flush=True)
def stop(*args):
 server.server_close();auth.unlink(missing_ok=True);p.unlink(missing_ok=True);raise SystemExit
signal.signal(signal.SIGTERM,stop)
try:server.serve_forever()
finally:server.server_close();auth.unlink(missing_ok=True);p.unlink(missing_ok=True)
