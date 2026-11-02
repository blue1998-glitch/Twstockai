"""Synthetic core-produced events; exact production workbench and radar renderer."""
from pathlib import Path
from copy import deepcopy
import json,tempfile
from graph_core.du1_20261102.test_increment import seed_fixture
from graph_core.core import analyze
from graph_core.market_daily import Journal
from graph_core.market_preview import build
HERE=Path(__file__).parent

def fixture(root):
    seed=seed_fixture(root);j=Journal(root/'runs');b=j.read(seed)['value']
    for s in b['stocks']:
        p=deepcopy(Journal(root/'results').read(s['result_key'])['value']['input'])
        for d,v in zip(['2026-10-30','2026-10-31','2026-11-01','2026-11-02'],[16,9,17,8] if s['code']=='A' else [8,16,9,17]):
            p['bars'].append(dict(date=d,open=str(v),high=str(v+1),low=str(v-1),close=str(v),volume_shares_scaled='200'))
        r=analyze(p,as_of='2026-11-02');s.update(as_of='2026-11-02',result_key='obs1-'+s['code']);Journal(root/'results').save(s['result_key'],dict(input=p,result=r))
    b['as_of']='2026-11-02';b['summary']['as_of']=b['as_of']
    original=Journal(root/'results').read(b['stocks'][0]['result_key'])['value']['input']
    for code,short in [('SHORT',True),('NONE',False)]:
        p=deepcopy(original);p['context']['code']=code
        if short:p['bars']=p['bars'][-1:]
        else:
            for i,bar in enumerate(p['bars']):bar.update(open=str(100+i),high=str(101+i),low=str(99+i),close=str(100+i))
        r=analyze(p,as_of=b['as_of']);Journal(root/'results').save('synthetic-'+code,dict(input=p,result=r))
        b['stocks'].append(dict(code=code,name='合成'+code,market='TWSE',identity='TWSE:'+code,as_of=b['as_of'],result_key='synthetic-'+code,status='INSUFFICIENT_HISTORY' if short else 'ANALYZED_FINMIND_HISTORY'))
    b['stocks'].append(dict(code='REFUSED',name='合成來源拒用',market='TPEX',identity='TPEX:REFUSED',as_of=b['as_of'],result_key=None,status='DATA_QUALITY_REFUSED',reason='合成品質反例'))
    b['summary'].update(expected=5,processed=5,synthetic_demo=True,status='SYNTHETIC_ONLY_NOT_MARKET');j.save('obs1-demo',b)
    return 'obs1-demo',b

def make():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);key,b=fixture(root)
        # Explicit view coverage, not a trading interval or hand-written events.
        r=build(root,key,radar_dates=['2026-10-30','2026-10-31','2026-11-01','2026-11-02']);page=Path(r['path']);shell=page.read_text()
        embedded={p.name:p.read_text() for p in page.parent.glob('series-*.json')};raw=json.dumps(embedded,ensure_ascii=False).replace('<','\\u003c')
        shell=shell.replace('<script id="market-state"','<script id="synthetic-demo-series" type="application/json">'+raw+'</script><script id="market-state"')
        shell=shell.replace('<title>','<title>純合成量價事件雷達｜',1);target=HERE/'Twstockai_OBS1_SYNTHETIC_DEMO.html';target.write_text(shell)
        return dict(bytes=target.stat().st_size,path=str(target),synthetic_only=True)
if __name__=='__main__':print(json.dumps(make(),ensure_ascii=False))
