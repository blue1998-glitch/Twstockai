"""Bounded read-only smoke test of original saved FM3, no source/core calls."""
import json,os,secrets,signal,sys
from pathlib import Path
from graph_core.market_daily import encode
from graph_core.market_increment import seed,stock_history
from graph_core_chart.mobile_private import create_auth,make_server
root=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
state=json.loads((root/'fm3-continuation.json').read_bytes());batch=seed(root,state['result']['id']);cases=[]
for code in ('1101','2884'):
 row=next(s for s in batch['stocks'] if s['code']==code and s.get('result_key'))
 saved=stock_history(root,row,batch)
 cases.append(dict(code=code,records=len(saved['input']['bars']),saved_result=str(root/'results'/(row['result_key']+'.json'))))
password=secrets.token_urlsafe(32);auth=out/'test-auth.json';create_auth(auth,'retainedtester',password)
server=make_server(state['preview']['path'],auth)
config=dict(origin='http://127.0.0.1:'+str(server.server_port),html=state['preview']['path'],httpCredentials=dict(username='retainedtester',password=password),as_of=batch['as_of'],cases=cases)
p=out/'browser-input.json';p.write_bytes(encode(config));os.chmod(p,0o600)
print(str(p),flush=True)
def stop(*args):
 server.server_close();auth.unlink(missing_ok=True);p.unlink(missing_ok=True);raise SystemExit
signal.signal(signal.SIGTERM,stop)
try:server.serve_forever()
finally:server.server_close();auth.unlink(missing_ok=True);p.unlink(missing_ok=True)
