"""Pure exact-source resolver. Never infer market regime, prices or a fallback."""
from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import re

VERSION = 'manual-analysis-basis/0.1'
MODES = ('RAW_CANDIDATE', 'ADJUSTED_CANDIDATE')
BINDING = ('series_key','code','price_mode','as_of','source_id','price_basis_id','frame_id','adjustment_version')

def fingerprint(value):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return 'sha256:'+hashlib.sha256(raw).hexdigest()

def validate_catalogue(catalogue):
    if not isinstance(catalogue,dict) or not isinstance(catalogue.get('entries'),list): raise ValueError('Invalid catalogue structure')
    if catalogue.get('schema_version') != 'manual-basis-catalogue/0.1': raise ValueError('Unsupported catalogue')
    if catalogue.get('catalogue_id') != fingerprint({k:v for k,v in catalogue.items() if k!='catalogue_id'}): raise ValueError('Catalogue fingerprint mismatch')
    seen=set()
    for row in catalogue['entries']:
        if any(not isinstance(row.get(k),str) or not row[k] for k in BINDING): raise ValueError('Incomplete source binding')
        if row['price_mode'] not in MODES: raise ValueError('Unsupported source mode')
        if date.fromisoformat(row['as_of']).isoformat()!=row['as_of']: raise ValueError('Noncanonical source date')
        key=(row['series_key'],row['as_of'])
        if key in seen: raise ValueError('Ambiguous catalogue row')
        seen.add(key)
    return catalogue

def validate_request(request):
    fields={'schema_version','selection_id','selected_at','code','price_mode','as_of','series_key'}
    if not isinstance(request,dict) or set(request)!=fields or request['schema_version']!='manual-basis-request/0.1': raise ValueError('Explicit request fields required')
    if not isinstance(request['selection_id'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',request['selection_id']): raise ValueError('Invalid selection identity')
    if not isinstance(request['selected_at'],str): raise ValueError('Selection time must be a string')
    try: stamp=datetime.fromisoformat(request['selected_at'].replace('Z','+00:00'))
    except ValueError as exc: raise ValueError('Invalid selection time') from exc
    if stamp.utcoffset() is None: raise ValueError('Selection time needs timezone')
    if not isinstance(request['code'],str) or not request['code']: raise ValueError('Explicit code required')
    if not isinstance(request['as_of'],str): raise ValueError('Exact analysis date required')
    try: canonical=date.fromisoformat(request['as_of']).isoformat()
    except ValueError as exc: raise ValueError('Invalid analysis date') from exc
    if canonical!=request['as_of']: raise ValueError('Exact canonical analysis date required')
    if request['price_mode'] is not None and request['price_mode'] not in MODES: raise ValueError('Unsupported requested mode')
    if request['series_key'] is not None and (not isinstance(request['series_key'],str) or not request['series_key']): raise ValueError('Invalid source selector')
    return request

def resolve(catalogue,request):
    validate_catalogue(catalogue);validate_request(request)
    intent=deepcopy(request);binding=None;available=[]
    if request['price_mode'] is None: status='REQUIRES_MODE'
    else:
        rows=[r for r in catalogue['entries'] if r['code']==request['code'] and r['price_mode']==request['price_mode']]
        if request['series_key'] is not None: rows=[r for r in rows if r['series_key']==request['series_key']]
        available=sorted({r['as_of'] for r in rows})
        exact=[r for r in rows if r['as_of']==request['as_of']]
        if not exact: status='UNAVAILABLE'
        elif len(exact)>1: status='REQUIRES_SOURCE'
        else:
            status='READY_SAVED_RESEARCH';binding={k:exact[0][k] for k in BINDING}
    result=dict(schema_version=VERSION,catalogue_id=catalogue['catalogue_id'],intent=intent,status=status,binding=binding,
                available_dates=available,market_regime_required=False,automatic_fallback=False,
                historical_selection_time=None,historical_signal_eligible=False,
                classification_quality='NOT_VALIDATED',action_qualification='NOT_EVALUATED')
    result['result_id']=fingerprint(result)
    return result

def validate_result(result):
    if result.get('schema_version')!=VERSION or result.get('result_id')!=fingerprint({k:v for k,v in result.items() if k!='result_id'}): raise ValueError('Invalid saved selection result')
    validate_request(result['intent'])
    if result.get('historical_signal_eligible') is not False or result.get('automatic_fallback') is not False: raise ValueError('Invalid eligibility/fallback')
    if result['status']=='READY_SAVED_RESEARCH':
        b=result['binding'];q=result['intent']
        if any(not isinstance(b.get(k),str) or not b[k] for k in BINDING): raise ValueError('Incomplete result binding')
        if any(b[k]!=q[k] for k in ('code','price_mode','as_of')) or q['series_key'] is not None and b['series_key']!=q['series_key']: raise ValueError('Intent/binding mismatch')
    elif result['status'] not in ('REQUIRES_MODE','UNAVAILABLE','REQUIRES_SOURCE') or result['binding'] is not None: raise ValueError('Invalid unresolved binding')
    return result
