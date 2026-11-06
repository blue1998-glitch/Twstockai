"""Separate retrospective single-event comparison; no product classifier or policy switch."""
import argparse, copy, hashlib, json
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CUTOFF='2026-07-24'
START='2026-01-02'
EVENT='2026-07-01'
SOURCE_PATH='docs/visual-discussion/20261020_independent_source_levels_work_review/source-data-2884.json'
SOURCE_SHA='074a7e4668f3f1bb0f91045e6dba3d1988c34661'

def load(path):return json.loads(path.read_text())
def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def roc(text):
    y,m,d=text.split('/');return f'{int(y)+1911:04d}-{m}-{d}'
def dec(text):return Decimal(text.replace(',',''))
def blob(body):return hashlib.sha1(f'blob {len(body)}\0'.encode()+body).hexdigest()

def adjusted(bars,as_of,event_date=EVENT,previous='34.45',cash='1.4'):
    # Explicitly specified event only; future event is not imported into earlier analysis.
    with localcontext() as ctx:
        ctx.prec=50
        factor=(Decimal(previous)-Decimal(cash))/Decimal(previous) if event_date<=as_of else Decimal(1)
        result=[]
        for original in bars:
            if not START<=original['date']<=as_of:continue
            bar=copy.deepcopy(original)
            for field in ['open','high','low','close']:
                bar[field]=str(Decimal(original[field])*(factor if original['date']<event_date else Decimal(1)))
            result.append(bar)
        return result,str(factor)

def build(source):
    raw_bytes=source.read_bytes();assert blob(raw_bytes)==SOURCE_SHA
    saved=load(source)
    originals=saved['bars']
    rows=[b for b in originals if START<=b['date']<=CUTOFF]
    event_table=load(ROOT/'raw/exright-2026-to-cutoff.json')
    assert event_table['strDate']=='20260101' and event_table['endDate']=='20260724'
    event_rows=[dict(zip(event_table['fields'],r)) for r in event_table['data'] if r[1]=='2884']
    assert len(event_rows)==1
    event=event_rows[0]
    assert [event[k] for k in ['資料日期','除權息前收盤價','除權息參考價','權值+息值','權/息']]==['115年07月01日','34.45','33.05','1.400000','息']
    assert Decimal(event['除權息前收盤價'])-Decimal(event['權值+息值'])==Decimal(event['除權息參考價'])
    bars_by_date={b['date']:b for b in originals}
    assert bars_by_date['2026-06-30']['close']==event['除權息前收盤價']
    comparisons=[]
    for name in ['stock-2884-202606','stock-2884-202607']:
        table=load(ROOT/'raw'/f'{name}.json')
        for r in table['data']:
            dt=roc(r[0])
            if dt>CUTOFF:continue
            expected=[r[i].replace(',','') for i in [3,4,5,6,1]]
            assert [bars_by_date[dt][k] for k in ['open','high','low','close','volume_shares_scaled']]==expected
            comparisons.append(dt)
    candidate,factor=adjusted(originals,CUTOFF)
    cad={b['date']:b for b in candidate}
    market=[]
    for path in sorted((ROOT/'raw').glob('market-*.json')):
        for row in load(path)['data']:
            dt=roc(row[0])
            if START<=dt<=CUTOFF:market.append({'date':dt,'close':str(dec(row[4]))})
    assert len({r['date'] for r in market})==len(market)
    assert [r['date'] for r in market]==[r['date'] for r in rows]
    refs=[]
    for dt in ['2026-02-26','2026-07-17']:
        raw_value=bars_by_date[dt]['high'];candidate_value=cad[dt]['high']
        compare_start=max(EVENT,dt)
        follow=[b for b in candidate if b['date']>compare_start]
        crossed=[b for b in follow if Decimal(b['close'])>Decimal(candidate_value)]
        refs.append({'source_date':dt,'source_field':'high','raw':raw_value,'candidate':candidate_value,'first_later_close_above_after_action_or_source':crossed[0]['date'] if crossed else None,'role':'MANUALLY_SPECIFIED_ORIGINAL_HIGH_NOT_AUTOMATIC_CONFIRMED_TURN_OR_FORMAL_BAND'})
    with localcontext() as ctx:
        ctx.prec=50
        peak=max(market,key=lambda r:Decimal(r['close']));last=market[-1]
        change=(Decimal(last['close'])/Decimal(peak['close'])-1)*100
        since_start=(Decimal(last['close'])/Decimal(market[0]['close'])-1)*100
    evidence={
      'schema':'b-basis-source-comparison/0.1','base_commit':'17a480ec770bfbeb0c179115a48d99a4647b978c',
      'observed_on_taipei':'2026-10-22','research_cutoff':CUTOFF,'window_start':START,'saved_bars':len(rows),
      'saved_source':{'path':SOURCE_PATH,'git_blob':SOURCE_SHA,'sha256':hashlib.sha256(raw_bytes).hexdigest()},
      'event':event,'event_status':'PRIMARY_TWSE_EVENT_ROW_CAPTURED_AND_PRICE_RECONCILED',
      'action_table_limits':event_table['notes'],
      'fresh_raw_checks':{'records':len(comparisons),'ohlcv_fields':len(comparisons)*5,'all_equal':True},
      'candidate_method':{'id':'b-single-cash-event-backward-ratio-research/0.1','formula':'(previous_close-cash_dividend)/previous_close; multiply pre-event OHLC only','prior_method_context':'Existing adjustment-0.1-cash-only-candidate sample formula; no original engine execution or modification','factor':factor,'precision':50,'event_effective':EVENT,'volume':'ORIGINAL_NATIVE_SHARES_UNCHANGED','complete_adjusted_history':False,'product_policy_approved_method':False,'historical_signal_eligible':False},
      'references':refs,
      'market':{'series':'TWSE_TAIEX_CLOSE_CONTEXT_ONLY_NOT_APPROVED_POLICY_INDEX','records':len(market),'first':market[0],'last':last,'window_high_close':peak,'last_vs_window_high_percent':str(change),'last_vs_first_percent':str(since_start),'regime':'NOT_ESTABLISHED','preferred_basis_under_policy':None,'no_20_percent_or_MA_threshold_created':True},
      'earlier_2025_table':{'2884_rows':[r for r in load(ROOT/'raw/exright-2025.json')['data'] if r[1]=='2884'],'no_oct27_action_cause_established':True,'nov6_flag_not_explained':True},
      'scope':{'official_event_row_newly_verified':True,'full_corporate_action_chain':'NOT_AUTHENTICATED','historical_publication_time':'NOT_AUTHENTICATED','historical_signal_eligible':False,'formal_structure':'NOT_VALIDATED','usefulness':'NOT_ESTABLISHED','android':'NOT_TESTED_NEW_BUILD','capital_loop':'NOT_EVALUATED','original_source_gaps':saved['source_gaps'],'old_raw_findings_retained':True,'automatic_policy_switch_implemented':False}
    }
    return evidence,{'raw':rows,'single_event_candidate':candidate,'market':market}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
    evidence,views=build(a.source)
    dump(ROOT/'evidence.json',evidence);dump(ROOT/'comparison-data.json',views)
    print(json.dumps({'bars':evidence['saved_bars'],'fresh_equal_records':evidence['fresh_raw_checks']['records'],'references':evidence['references'],'market':evidence['market']},ensure_ascii=False,indent=2))
