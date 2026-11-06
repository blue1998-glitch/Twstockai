"""Explicit synthetic trade-delta units; no market-rule inference or optimizer."""
from .core import fingerprint,timestamp


def validate(request):
    d=request['quantity_domain'];data=request['decision_input'];codes=(request['incumbent'],request['destination'])
    if (not isinstance(d,dict) or set(d)!={'schema','version','parameter_source','available_at','account_id','assets'}
            or d['schema']!='capital-quantity-domain/0.1' or not isinstance(d['version'],str) or not d['version']
            or not isinstance(d['parameter_source'],str) or not d['parameter_source']):
        raise ValueError('EXPLICIT_QUANTITY_DOMAIN_PROVENANCE_REQUIRED')
    if timestamp(d['available_at'])>timestamp(data['decision_at']):raise ValueError('QUANTITY_DOMAIN_NOT_YET_AVAILABLE')
    if d['account_id']!=fingerprint(data['account']):raise ValueError('QUANTITY_DOMAIN_ACCOUNT_CONFLICT')
    if not isinstance(d['assets'],dict) or set(d['assets'])!=set(codes):raise ValueError('EXACT_QUANTITY_DOMAIN_ASSETS_REQUIRED')
    units={}
    for code in codes:
        row=d['assets'][code];asset=data['assets'][code]
        if (not isinstance(row,dict) or set(row)!={'code','channel_id','unit_shares','source_id','basis_id','adjustment_version','available_at'}
                or row['code']!=code or any(row[k]!=asset[k] for k in ('source_id','basis_id','adjustment_version'))):
            raise ValueError('QUANTITY_DOMAIN_ASSET_SOURCE_CONFLICT:'+code)
        if not isinstance(row['channel_id'],str) or not row['channel_id']:raise ValueError('EXPLICIT_QUANTITY_CHANNEL_REQUIRED:'+code)
        if timestamp(row['available_at'])>timestamp(data['decision_at']):raise ValueError('QUANTITY_UNIT_NOT_YET_AVAILABLE:'+code)
        value=row['unit_shares']
        if not isinstance(value,str) or not value.isascii() or not value.isdigit() or int(value)<=0:
            raise ValueError('EXPLICIT_POSITIVE_WHOLE_UNIT_REQUIRED:'+code)
        units[code]=int(value)
    return units


def axis(low,high,unit):
    first=((low+unit-1)//unit)*unit
    count=0 if first>high else (high-first)//unit+1
    return dict(unit_shares=str(unit),count=count,minimum_legal=str(first) if count else None,
        maximum_legal=str(first+(count-1)*unit) if count else None),range(first,high+1,unit)


def reasons(targets,opening,incumbent,destination,units):
    result=[]
    sold=int(opening[incumbent])-int(targets[incumbent]);added=int(targets[destination])-int(opening[destination])
    if sold<0 or sold%units[incumbent]:result.append('SELL_QUANTITY_OUTSIDE_DECLARED_UNIT:'+incumbent)
    if added<0 or added%units[destination]:result.append('BUY_QUANTITY_OUTSIDE_DECLARED_UNIT:'+destination)
    return result
