"""Generate engine-authoritative display-price expectations around cash events."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from structure import project_prices

cases=[]
for code in ['8069','6488']:
    candles=json.loads((ROOT/'data'/f'{code}_candles.json').read_text())
    events=json.loads((ROOT/'data'/f'{code}_events.json').read_text())
    indices={0,len(candles)-1}
    for event in events:
        i=next(i for i,c in enumerate(candles) if c['date']==event['effective_date'])
        indices.update([i-1,i,min(i+1,len(candles)-1)])
    for i in sorted(indices):
        for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
            rows=project_prices(candles,events,candles[i]['date'],mode)
            cases.append(dict(code=code,mode=mode,index=i,as_of=candles[i]['date'],
                              expected=[[r[k] for k in ['open','high','low','close']] for r in rows]))
(ROOT/'data/viewer_price_projection_cases.json').write_text(json.dumps(cases,separators=(',',':')))
print(f'{len(cases)} price-basis cases generated from unchanged numeric engine.')
