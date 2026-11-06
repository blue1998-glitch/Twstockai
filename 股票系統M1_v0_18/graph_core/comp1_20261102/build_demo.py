"""Shared production comparison UI with core-computed synthetic sources only."""
import json,tempfile
from copy import deepcopy
from pathlib import Path
from graph_core.obs1_20261102.build_demo import fixture as radar_fixture
from graph_core.market_daily import Journal
from graph_core.core import analyze
from graph_core.market_preview import build
HERE=Path(__file__).parent

def fixture(root):
    _,b=radar_fixture(root);s=deepcopy(b['stocks'][0]);saved=Journal(root/'results').read(s['result_key'])['value'];p=deepcopy(saved['input']);p['context']['code']='DATE';p['bars']=p['bars'][:-1];r=analyze(p,as_of=p['bars'][-1]['date']);Journal(root/'results').save('synthetic-DATE',dict(input=p,result=r));s.update(code='DATE',name='合成不同日期',identity='TWSE:DATE',as_of=r['as_of'],result_key='synthetic-DATE');b['stocks'].append(s);b['summary'].update(expected=6,processed=6);Journal(root/'runs').save('comp1-demo',b);return 'comp1-demo',b

def make():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);key,_=fixture(root);r=build(root,key);page=Path(r['path']);shell=page.read_text();embedded={p.name:p.read_text() for p in page.parent.glob('series-*.json')};raw=json.dumps(embedded,ensure_ascii=False).replace('<','\\u003c');shell=shell.replace('<script id="market-state"','<script id="synthetic-demo-series" type="application/json">'+raw+'</script><script id="market-state"');shell=shell.replace('<title>','<title>純合成多股比較｜',1);target=HERE/'Twstockai_COMP1_SYNTHETIC_DEMO.html';target.write_text(shell);return dict(path=str(target),bytes=target.stat().st_size,synthetic_only=True)
if __name__=='__main__':print(json.dumps(make(),ensure_ascii=False))
