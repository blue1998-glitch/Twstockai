"""Saved-fact presentation, not a strategy or a reference-selection engine.
No IO, recognition, indicators, weights, ranking or new numerical thresholds.
"""
from copy import deepcopy
from reaction_facts.core import compare

VERSION='saved-fact-decision-view/0.1'
STOP='OBSERVATION_STOPPED_AT_DATA_OR_BASIS_GAP'
LABELS={
 'CLOSE_CROSS_UP':'突破參照','CLOSE_ABOVE_RESEARCH_RANGE':'突破參照',
 'CLOSE_CROSS_DOWN':'跌破參照','CLOSE_BELOW_RESEARCH_RANGE':'跌破參照',
 'FAILED_UP_AND_CROSSED_BELOW_RANGE':'跌破參照',
 'CLOSE_REENTERED_RANGE':'回到區間','FAILED_UP_RETURN_IN_RANGE':'回到區間',
 'RETURN_IN_RANGE_AFTER_BREAKDOWN':'回到區間',
 'FAILED_UP_RETURN_BELOW':'跌回參照下','RETURN_ABOVE_AFTER_DOWN':'重返參照上',
 'CLOSE_EQUALS_REFERENCE':'收盤等於參照',
}
REASONS={'MISSING_QUOTE':'缺少今日行情','NO_VALID_CLOSE_SUSPENSION_NOT_AUTHENTICATED':'缺少有效收盤',
 'NO_TRADE_REPORTED_ZERO_VOLUME':'今日零成交','DATA_QUALITY_FAILURE':'價量資料不合格',
 'DATA_QUALITY_REFUSED':'價量資料不合格','HISTORY_SOURCE_UNAVAILABLE':'歷史來源不足'}

def empty(stock,reason=None):
    short=stock.get('status')=='INSUFFICIENT_HISTORY'
    return dict(version=VERSION,identity=stock['identity'],as_of=stock['as_of'],
        headline='歷史不足' if short else '今日不可判定',tags=[],key_prices=[],key_caption='未定',
        volume_label='量未知',risk=reason or ('資料不足' if short else REASONS.get(stock.get('status'),'資料不足')),
        can_judge=False,refs=[],binding=None,primary_pressure_id=None,formal_authorized=False,
        volume_confirms_price=None,structural_invalidation=None)

def bind(stock,radar):
    if any(radar.get(k)!=stock.get(k) for k in ('code','market','as_of')):raise ValueError('DECISION_STOCK_OR_DATE_BINDING')
    return {k:radar[k] for k in ('result_id','source_id','price_basis_id','source_prefix_fingerprint')}

def blocked(stock,radar):
    """Explicit saved current reset, not a guess from a historical gap."""
    binding=bind(stock,radar)
    if stock.get('status')=='INSUFFICIENT_HISTORY':
        d=empty(stock);d['binding']=binding;return d
    gaps=radar.get('data_gaps',{})
    if stock['as_of'] in set(gaps.get('basis_resets',[])+gaps.get('missing_expected_dates',[])+gaps.get('missing_price_rows',[])):
        d=empty(stock,'來源中斷');d.update(binding=binding,volume_label='量不可比');return d
    return None

def project(stock,result):
    """Translate ALL currently comparable same-day saved events. All ties stay.
    A high/low crossing is a close fact, not a confirmed/tradable breakout.
    """
    ctx=result['context'];cutoff=stock['as_of']
    if (ctx['code'],ctx['exchange'],result['as_of'])!=(stock['code'],stock['market'],cutoff):raise ValueError('DECISION_STOCK_OR_DATE_BINDING')
    if result['schema_version']!='graph-recognition-research/0.2' or result['comparison']['primary_pressure_id'] is not None:raise ValueError('UNSUPPORTED_OR_PROMOTED_RESULT')
    binding=dict(result_id=result['result_id'],source_id=ctx['source_id'],price_basis_id=ctx['price_basis_id'],source_prefix_fingerprint=result['source_prefix_fingerprint'])
    stub=dict(code=stock['code'],market=stock['market'],as_of=cutoff,data_gaps=result['data_gaps'],**binding)
    unavailable=blocked(stock,stub)
    if unavailable:return unavailable
    d=empty(stock);d.update(binding=binding,can_judge=True,risk='研究參照')
    refs=[];labels={};stops=0;comparable=0
    pivots={p['id']:p for p in result.get('pivots',[])}
    for collection in ('boxes','reference_candidates'):
        for i,candidate in enumerate(result[collection]):
            events=candidate['path']['events'];cid=candidate.get('id',candidate.get('pivot_id'))
            if candidate['confirmed_at']>cutoff:continue
            is_stopped=any(e['type']==STOP and e['first_observed_at']<=cutoff for e in events)
            if is_stopped:stops+=1;continue
            if collection=='boxes' and not candidate['usable_at_anchor']:continue
            comparable+=1
            for j,event in enumerate(events):
                if event['date']>cutoff or event['first_observed_at']>cutoff:raise ValueError('FUTURE_EVENT_IN_SAVED_RESULT')
                if event['first_observed_at']!=cutoff or event['date']!=cutoff:continue
                kind=event['type'];label=LABELS.get(kind)
                if label is None:continue  # INITIAL is not a crossing; no guessed state.
                labels[label]=labels.get(label,0)+1
                if collection=='reference_candidates':
                    price=candidate['price'];values=[price];origin=pivots.get(cid,{})
                    occurred=origin.get('occurred_at',candidate.get('occurred_at'));role='研究高點'
                else:
                    b=candidate['research_bounds'];values=[b['high']] if kind=='CLOSE_ABOVE_RESEARCH_RANGE' else [b['low']] if kind in ('CLOSE_BELOW_RESEARCH_RANGE','FAILED_UP_AND_CROSSED_BELOW_RANGE') else [b['low'],b['high']]
                    occurred=candidate['start'];role='研究區間'
                for value in values:
                    refs.append(dict(candidate_id=cid,collection=collection,pointer=f'/{collection}/{i}/path/events/{j}',
                        label=label,event_type=kind,price=value,role=role,occurred_at=occurred,
                        confirmed_at=candidate['confirmed_at'],event_date=event['date'],first_observed_at=event['first_observed_at']))
    if not comparable:
        d=empty(stock,'參照已停止比較' if stops else '缺少有效參照');d['binding']=binding;return d
    tags=[dict(label=k,count=v) for k,v in labels.items()]
    d.update(headline=next(iter(labels)) if len(labels)==1 else '多參照分歧' if labels else '今日無新過線',tags=tags,refs=refs)
    # No significance ordering and no unique winner. Numeric strings stay exact.
    d['key_prices']=[]
    for ref in refs:
        if not any(compare(ref['price'],v)['relation']=='EQUAL' for v in d['key_prices']):d['key_prices'].append(ref['price'])
    d['key_caption']=d['key_prices'][0] if len(d['key_prices'])==1 else '多個價位' if d['key_prices'] else '未指定'
    if len(labels)>1:d['risk']='不同參照結果不一'
    elif '跌回參照下' in labels:d['risk']='已跌回參照下'
    ratios=result.get('anchor_volume',{}).get('ratio_to_previous_means',{})
    ratio=ratios.get('1');relation=compare(ratio,'1',reason='MISSING_VOLUME_BASELINE')['relation']
    d['volume_label']={'ABOVE':'量增（較前筆）','BELOW':'量減（較前筆）','EQUAL':'量平（較前筆）'}.get(relation,'量未知')
    d['volume_evidence']=deepcopy(result.get('anchor_volume'))
    return d

def card(decision):
    return {k:deepcopy(decision[k]) for k in ('headline','tags','key_caption','volume_label','risk','can_judge')}
