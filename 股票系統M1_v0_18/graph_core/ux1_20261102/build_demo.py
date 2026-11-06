"""Synthetic demo using production renderer/UI. No real market data or HTTP."""
import json,tempfile
from pathlib import Path
from graph_core.du1_20261102.test_increment import seed_fixture
from graph_core.market_daily import Journal
from graph_core.market_preview import build
HERE=Path(__file__).parent

def make():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);seed=seed_fixture(root);batch=Journal(root/'runs').read(seed)['value']
        for row in batch['stocks']:row.update(as_of=batch['as_of'])
        from graph_core.core import analyze
        row=dict(batch['stocks'][0]);saved=Journal(root/'results').read(row['result_key'])['value'];p=saved['input'];p['context']['code']='SHORT';p['bars']=p['bars'][-1:];r=analyze(p,as_of=batch['as_of'])
        Journal(root/'results').save('demo-short',dict(input=p,result=r));row.update(code='SHORT',identity='TWSE:SHORT',name='合成短歷史',result_key='demo-short',status='INSUFFICIENT_HISTORY');batch['stocks'].append(row)
        for i in range(117):batch['stocks'].append(dict(code='S'+str(i).zfill(3),name='合成拒用樣本'+str(i),market='TWSE' if i%2==0 else 'TPEX',identity='SYNTHETIC:'+str(i),as_of=batch['as_of'],status='DATA_QUALITY_REFUSED',reason='合成品質反例，不補價',result_key=None))
        batch['summary'].update(expected=120,processed=120,synthetic_demo=True,status='SYNTHETIC_ONLY_NOT_MARKET');Journal(root/'runs').save('ux1-demo',batch)
        result=build(root,'ux1-demo');page=Path(result['path']);shell=page.read_text();embedded={p.name:p.read_text() for p in page.parent.glob('series-*.json')}
        raw=json.dumps(embedded,ensure_ascii=False).replace('<','\\u003c')
        shell=shell.replace('<script id="market-state"', '<script id="synthetic-demo-series" type="application/json">'+raw+'</script><script id="market-state"')
        shell=shell.replace('<title>','<title>純合成手機示範｜',1)
        target=HERE/'Twstockai_UX1_SYNTHETIC_DEMO.html';target.write_text(shell)
        return dict(path=str(target),bytes=target.stat().st_size,stocks=120,charts=3,synthetic_only=True)
if __name__=='__main__':print(json.dumps(make(),ensure_ascii=False))
