"""Prefix-safe descriptive B price/volume path. No formal band/volume classifier."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
import os,json,hashlib

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
EXPECTED='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
START='2026-06-01'; END='2026-06-30'
FRAME_START='2026-03-16'; FRAME_END='2026-05-29'
CUTOFFS=['2026-06-03','2026-06-04','2026-06-08','2026-06-09','2026-06-11','2026-06-17','2026-06-18','2026-06-22','2026-06-24','2026-06-30']
D=Decimal
def dump(name,value):
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def rational(value):
    f=Fraction(value)
    return {'numerator':f.numerator,'denominator':f.denominator,'display_2dp':f'{D(f.numerator)/D(f.denominator):.2f}'}
def relation(value,reference):
    return 'ABOVE' if value>reference else 'BELOW' if value<reference else 'EQUAL'
def view(all_bars,cutoff):
    # All values, volume baselines, and events are built only from the prefix.
    bs=[b for b in all_bars if b['date']<=cutoff]
    bydate={b['date']:b for b in bs}
    small=bydate.get('2026-04-16'); large=bydate.get('2026-02-26')
    refs={'lower_activity_high':{'date':'2026-04-16','field':'high','value':small['high'] if small else None,'role':'RAW_PRICE_PROXY_NOT_CONFIRMED_FORMAL_SMALL_BAND_EDGE'},'broader_high':{'date':'2026-02-26','field':'high','value':large['high'] if large else None,'role':'RAW_PRICE_PROXY_NOT_CONFIRMED_FORMAL_LARGE_BAND_EDGE'}}
    source=[b for b in bs if FRAME_START<=b['date']<=FRAME_END]
    complete=FRAME_END in bydate
    volumes=sorted(int(b['volume_shares_scaled']) for b in source)
    source_median=Fraction(volumes[(len(volumes)-1)//2]+volumes[len(volumes)//2],2) if complete else None
    frozen={'period':[FRAME_START,FRAME_END],'available_in_saved_prefix':complete,'saved_rows':len(source) if complete else None,'median_shares':rational(source_median) if complete else None,'period_selection':'RETROSPECTIVE_READING_WINDOW_NOT_AUTOMATIC_FORMATION_OR_HISTORICAL_SELECTION'}
    events=[]
    for i,b in enumerate(bs):
        if not START<=b['date']<=END:continue
        v=int(b['volume_shares_scaled']); previous=bs[i-1] if i else None
        p20=bs[max(0,i-20):i]
        mean=Fraction(sum(int(x['volume_shares_scaled']) for x in p20),20) if len(p20)==20 else None
        r={'date':b['date'],'bar':b,'references':{},'volume':{'shares':b['volume_shares_scaled'],'previous_saved_day':previous['date'] if previous else None,'vs_previous_saved_day':rational(Fraction(v,int(previous['volume_shares_scaled']))) if previous else None,'frozen_source_median_shares':rational(source_median) if source_median else None,'vs_frozen_source_median':rational(Fraction(v)/source_median) if source_median else None,'prior20_mean_shares':rational(mean) if mean else None,'prior20_start':p20[0]['date'] if mean else None,'prior20_end':p20[-1]['date'] if mean else None,'vs_prior20_mean':rational(Fraction(v)/mean) if mean else None,'volume_qualification':None}}
        for key,ref in refs.items():
            if ref['value'] is None:r['references'][key]=None;continue
            price=D(ref['value']); c=D(b['close']);h=D(b['high']);l=D(b['low']); pc=D(previous['close']) if previous else None
            crossing='UP' if pc is not None and pc<price<c else 'DOWN' if pc is not None and pc>price>c else None
            from_equal=('UP' if c>price else 'DOWN' if c<price else None) if pc==price else None
            r['references'][key]={'value':ref['value'],'close_relation':relation(c,price),'wick_contains_reference':l<=price<=h,'high_strictly_above':h>price,'whole_bar_above':l>price,'whole_bar_below':h<price,'previous_close_relation':relation(pc,price) if pc is not None else None,'saved_close_cross':crossing,'departure_from_equal_close':from_equal}
        events.append(r)
    last=events[-1] if events else None
    return {'cutoff':cutoff,'selection':'RETROSPECTIVE_FIXED_CASE_PREFIX_VIEW_NOT_HISTORICAL_SIGNAL_SELECTION','references':refs,'frozen_volume_comparison':frozen,'events':events,'current_reference_relations':{k:x['close_relation'] if x else None for k,x in last['references'].items()} if last else None,'formal_small_band':None,'formal_large_band_bounds':None,'volume_qualification':None,'support_pressure_response_confirmed':None,'trade_eligible':False,'historical_signal_eligible':False}

def run():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    s=json.loads(SOURCE.read_text());bs=s['bars']
    assert len(bs)==1213==len({b['date'] for b in bs}) and bs==sorted(bs,key=lambda b:b['date'])
    final=view(bs,END); assert len(final['events'])==21
    dump('path-evidence.json',final)
    dump('cutoff-views.json',{d:view(bs,d) for d in CUTOFFS})
    selected=['2026-06-03','2026-06-04','2026-06-05','2026-06-08','2026-06-09','2026-06-10','2026-06-11','2026-06-17','2026-06-18','2026-06-22','2026-06-23','2026-06-24','2026-06-30']
    dump('selected-events.json',[e for e in final['events'] if e['date'] in selected])
    dump('source-provenance.json',{'base_commit':'e57664243e662b82918c38a8877355a249ff3979','source_repo_path':'docs/visual-discussion/20261020_independent_source_levels_work_review/source-data-2884.json','source_sha256':EXPECTED,'source_gaps':s['source_gaps'],'price_basis_id':s['price_basis_id'],'study_price_references':final['references'],'manual_nested_band_decision':'docs/visual-discussion/20261021_b_nested_band_decision/decision.json','volume_comparisons':'Previous saved day; frozen Mar16-May29 source median; previous20 saved bars mean excluding current day. Descriptive only, not three voting qualifications or a selected strategy threshold.','formal_signal_eligible':False})
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    print(json.dumps({'bars':len(bs),'path_bars':len(final['events']),'cutoffs':len(CUTOFFS),'source_median':final['frozen_volume_comparison'],'crosses':[{k:e[k] for k in ['date','references']} for e in final['events'] if any(x and x['saved_close_cross'] for x in e['references'].values())]},ensure_ascii=False,indent=2))
if __name__=='__main__':run()
