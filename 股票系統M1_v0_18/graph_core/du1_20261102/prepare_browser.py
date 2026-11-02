"""Build two explicitly SYNTHETIC private batches and ephemeral authenticated test service."""
import json,os,secrets,signal,sys,threading
from pathlib import Path
from datetime import datetime,timezone
from graph_core.du1_20261102.test_increment import seed_fixture
from graph_core.fm1_20261101.test_daily import sources
from graph_core.market_daily import import_saved,encode
from graph_core.market_increment import update
from graph_core_chart.mobile_private import create_auth,make_server
from graph_core.market_preview import source_segment_ma
from product_candidate.macd import macd

root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True);private=root/'synthetic-runtime';private.mkdir(exist_ok=True)
input_dir=root/'synthetic-source';input_dir.mkdir(exist_ok=True)
seed=seed_fixture(private);clock=datetime(2026,11,4,tzinfo=timezone.utc)
results=[]
for dt in ('1151030','1151102'):
    sources(input_dir,dt=dt)
    r=update(private,seed_run=seed,capture_id=import_saved(input_dir,private),now=clock)
    if r.get('status')=='BLOCKED':raise ValueError(r['reason'])
    results.append(r)
password=secrets.token_urlsafe(32);auth=root/'test-auth.json';create_auth(auth,'du1tester',password)
server=make_server(None,auth,head=private/'current-increment-run.json')
batches=[]
for r in results:
    batch=json.loads((private/'runs'/(r['id']+'.json')).read_bytes())['value'];cases=[]
    for s in batch['stocks']:
        v=json.loads((private/'results'/(s['result_key']+'.json')).read_bytes())['value'];bars=v['input']['bars'];resets=[i for i,b in enumerate(bars) if b['date'] in v['input']['basis_break_dates']]
        expected=dict(core=v['result'],bars=bars,macd=macd([b['close'] for b in bars],resets=resets),moving_averages=source_segment_ma(bars,resets))
        p=root/(r['summary']['as_of']+'-'+s['code']+'-expected.json');p.write_bytes(encode(expected))
        cases.append(dict(code=s['code'],records=len(bars),expected=str(p)))
    desc=r['private_preview'];route='/batch-'+desc['sha256']+'/'+Path(desc['path']).name
    batches.append(dict(route=route,as_of=batch['as_of'],cases=cases))
config=dict(origin='http://127.0.0.1:'+str(server.server_port),httpCredentials=dict(username='du1tester',password=password),batches=batches)
config_path=root/'browser-input.json';config_path.write_bytes(encode(config));os.chmod(config_path,0o600)
print(str(config_path),flush=True)
def stop(*args):
    server.server_close();auth.unlink(missing_ok=True);config_path.unlink(missing_ok=True);raise SystemExit
signal.signal(signal.SIGTERM,stop)
try:server.serve_forever()
finally:auth.unlink(missing_ok=True);config_path.unlink(missing_ok=True);server.server_close()
