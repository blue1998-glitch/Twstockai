"""Verify the actual shipped HTML against244 official captures and original bundle.
Independent streaming prefix checks validate every new frame's left price/volume
facts; interval source highs/lows, close events and review limits are also checked.
"""
from decimal import Decimal,localcontext
import argparse,hashlib,json,re
from pathlib import Path
from pressure_chart.build import load_original
from pressure_chart.history_adapter import validate_intake
from technical_chart.build import unpack
from contracts import fingerprint
from moving_averages import curves
from product_candidate.macd import macd
from product_candidate.build import publish_immutable


def verify(html,history):
    content=Path(html).read_bytes();match=re.search(r'<script type="application/json" id="payload">(.*?)</script>',content.decode(),re.S)
    if match is None:raise ValueError('Actual HTML payload missing')
    p=unpack(json.loads(match.group(1)));old=load_original();intake=validate_intake(history)
    if p['numbers']!=old['numbers']:raise ValueError('Original numeric bundle changed')
    for s in old['numbers']['series']:
        if p['evidence'][s['key']]!=old['evidence'][s['key']]:raise ValueError('Original structure evidence changed')
    checks=[]
    for s in p['history_series']:
        source=next(x for x in intake['series'] if x['code']==s['code']);rows=source['candles'];last_base=s['bases'][s['frames'][-1]['chart_base']]
        if rows!=last_base['bars']:raise ValueError('Actual embedded RAW data differs from official capture')
        ma=curves(rows);resets=sorted({next(i for i,r in enumerate(rows) if r['date']>=e['effective_date']) for e in last_base['known_events'] if e['effective_date']<=rows[-1]['date']})
        indicator=macd([r['close'] for r in rows],resets=resets)
        for b in s['bases'].values():
            if b['bars']!=rows or b['moving_averages']!=ma or b['macd']!=indicator:raise ValueError('RAW or existing SMA/MACD numerical mismatch')
        high=peak=None;high_dates=[];peak_dates=[];volume_sum=Decimal(0);month_frames=0
        for i,(f,w,review) in enumerate(zip(s['frames'],p['wall_frames'][s['key']],p['followup_layers'][s['key']])):
            if i:
                previous=rows[i-1];value=Decimal(previous['high']);volume=Decimal(previous['volume_shares_scaled'])
                if high is None or value>high:high=value;high_dates=[previous['date']]
                elif value==high:high_dates.append(previous['date'])
                if peak is None or volume>peak:peak=volume;peak_dates=[previous['date']]
                elif volume==peak:peak_dates.append(previous['date'])
                volume_sum+=volume
            price=w['price_wall_evidence'];vol=w['volume_wall_evidence'];asof=rows[i]['date']
            if f['index']!=i or f['as_of']!=asof or f['data_fingerprint']!=fingerprint(rows[:i+1]):raise ValueError('Daily frame prefix mismatch')
            if price['highest_supplied_left_high']!=(None if high is None else str(high)) or price['dates']!=high_dates:raise ValueError('Noncausal left highest-high evidence')
            if vol['max_single_day_shares']!=(None if peak is None else str(peak)) or vol['max_single_day_dates']!=peak_dates or Decimal(vol['total_shares'])!=volume_sum:raise ValueError('Noncausal left volume evidence')
            if any(e['effective_date']>asof for e in s['bases'][f['chart_base']]['known_events']):raise ValueError('Future company-action sample leaked')
            if w['interval_detail_status'].startswith('NOT_EXPORTED') and w['monthly_source_slices']:raise ValueError('Unprepared future detail fallback')
            if w['monthly_source_slices']:month_frames+=1
            for region in [*w['monthly_source_slices'],*w['explicit_source_intervals']]:
                a,b=region['from_index'],region['to_index'];part=rows[a:b+1]
                if b>i or region['actual_end']!=rows[b]['date'] or region['high']!=str(max(Decimal(r['high']) for r in part)):raise ValueError('Interval uses wrong high/future source')
                if Decimal(region['volume']['total_shares'])!=sum(Decimal(r['volume_shares_scaled']) for r in part):raise ValueError('Interval total/peak volume confused')
                for event in region['close_events']:
                    body={k:v for k,v in event.items() if k!='event_id'}
                    if event['date']>asof or event['event_id']!=fingerprint(body):raise ValueError('Interval event provenance/future mismatch')
            if review:
                if s['code']!='1101' or asof<'2026-09-30':raise ValueError('Case extrapolated into wrong stock/date')
                if review['post_breakout_bars']!=[r for r in rows[:i+1] if r['date']>'2026-09-30']:raise ValueError('Post-breakout data replaced by prebreakout volume')
                if any(review['volume_expansion'][key] is not None for key in ('baseline','threshold','duration')):raise ValueError('Invented volume threshold')
        checks.append(dict(code=s['code'],frames=len(rows),first=rows[0]['date'],last=rows[-1]['date'],monthly_source_responses=len(source['source_records']),
            exact_date_monthly_detail_frames=month_frames,original_source_days_equal=True,status='PASS'))
    return dict(status='PASS',source_html_sha256=hashlib.sha256(content).hexdigest(),original_numeric_bundle_exact_equal=True,
        original_saved_frames=sum(len(s['frames']) for s in old['numbers']['series']),new_official_raw_frames=sum(c['frames'] for c in checks),
        source_response_files=sum(c['monthly_source_responses'] for c in checks),series=checks,
        full_market_or_lifetime_history='NOT_CLAIMED',full_five_year_actions='UNVERIFIED',physical_android='NOT_TESTED_NEW_BUILD')

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--html',required=True);a.add_argument('--history',required=True);a.add_argument('--report',required=True);p=a.parse_args()
    with localcontext() as ctx:
        ctx.prec=50;r=verify(p.html,p.history)
    print(publish_immutable(p.report,json.dumps(r,ensure_ascii=False,indent=2).encode()));print(json.dumps(r,ensure_ascii=False,indent=2))
