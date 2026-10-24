"""Cutoff-local observation seeds, not formal intervals or M1 pivot outputs.

Generator functions do not accept manual dates, labels, target lengths or cutoffs
to optimize. Drivers specify data cutoffs only. All historical results here are
new retrospective research outputs, never claimed as original engine snapshots.
"""
from pathlib import Path
from decimal import Decimal as D
import argparse, json, hashlib
from collections import defaultdict

canon=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
digest=lambda v:'sha256:'+hashlib.sha256(canon(v)).hexdigest()

def propose(source, cutoff):
    bars=[b for b in source['bars'] if b['date']<=cutoff]
    if not bars or bars[-1]['date']!=cutoff:raise ValueError('cutoff must be a saved bar date')
    gaps=[d for d in source['source_gaps']['known_calendar_missing_dates']if d<=cutoff]
    latest_gap=max(gaps)if gaps else None
    begin=next((i for i,b in enumerate(bars)if latest_gap is None or b['date']>latest_gap),len(bars))
    if begin==len(bars):raise ValueError('no eligible rows after conservative research data separator')
    last=len(bars)-1
    prefix_id=digest(bars)
    pool=defaultdict(list);events=[]
    lo=D(bars[-1]['low']);hi=D(bars[-1]['high'])
    for i in range(last-1,begin-1,-1):
        l,h=D(bars[i]['low']),D(bars[i]['high'])
        if l<lo or h>hi:
            separation='ABOVE_ENTIRE_LATER_ENVELOPE'if l>hi else'BELOW_ENTIRE_LATER_ENVELOPE'if h<lo else'OVERLAPS_OR_TOUCHES_LATER_ENVELOPE'
            event={'origin_index':i,'origin_date':bars[i]['date'],'origin_bar':bars[i],
                   'later_start':bars[i+1]['date'],'later_end':cutoff,
                   'later_low':str(lo),'later_high':str(hi),
                   'extends_low':l<lo,'extends_high':h>hi,'separation':separation,
                   'qualified_at':'CURRENT_RECONSTRUCTED_CUTOFF_ONLY_NOT_ORIGINAL_EVENT_TIME'}
            events.append(event)
            pool[i].append({'role':'ENVELOPE_EXTENDER_BAR','event_index':len(events)-1})
            pool[i+1].append({'role':'AFTER_ENVELOPE_EXTENDER','event_index':len(events)-1})
        lo=min(lo,l);hi=max(hi,h)
    records=[]
    for start,reasons in sorted(pool.items()):
        rows=bars[start:];l=min(D(b['low'])for b in rows);h=max(D(b['high'])for b in rows)
        records.append({'candidate_id':digest({'method':'backward-envelope-seed/0.1','prefix':prefix_id,'start_index':start}),
                        'start_index':start,'start_date':rows[0]['date'],'observed_through':cutoff,'records':len(rows),
                        'observed_low':str(l),'observed_high':str(h),'reasons':reasons,
                        'formal_start':None,'formal_end':None,'recognized_interval':None,
                        'qualification':'OBSERVATION_SEED_NOT_FORMAL_INTERVAL_OR_ACTION'})
    # A descriptive close-turn baseline. Plateau anchors require a later unequal close.
    turns=[];i=begin
    while i<=last:
        j=i
        while j<last and D(bars[j+1]['close'])==D(bars[i]['close']):j+=1
        if i>begin and j<last:
            before,cur,after=D(bars[i-1]['close']),D(bars[i]['close']),D(bars[j+1]['close'])
            if(cur>before and cur>after)or(cur<before and cur<after):
                for anchor in sorted({i,j}):
                    turns.append({'anchor_index':anchor,'start_date':bars[anchor]['date'],
                                  'raw_close_turn':'HIGH'if cur>before else'LOW',
                                  'right_evidence_at':bars[j+1]['date'],
                                  'observed_through':cutoff,'records':len(bars)-anchor,
                                  'qualification':'NEW_CLOSE_ONLY_RESEARCH_EVENT_NOT_ORIGINAL_PIVOT'})
        i=j+1
    # Latest maximal suffix with a positive-width intersection of every daily range.
    low,high=D(bars[-1]['low']),D(bars[-1]['high']);start=last;blocked=None
    for i in range(last-1,begin-1,-1):
        nl,nh=max(low,D(bars[i]['low'])),min(high,D(bars[i]['high']))
        if nl>=nh:
            blocked={'date':bars[i]['date'],'result_low':str(nl),'result_high':str(nh),'reason':'NO_POSITIVE_WIDTH_COMMON_CELL'};break
        start=i;low,high=nl,nh
    result={'schema':'m1-observation-start-research/0.1','code':source['code'],'data_cutoff':cutoff,
            'source_prefix_records':len(bars),'source_prefix_bars_fingerprint':prefix_id,
            'eligibility_scope':{'first_eligible_index':begin,'first_eligible_date':bars[begin]['date'],
               'records':len(bars)-begin,'latest_listed_missing_date':latest_gap,
               'earlier_records_retained_as_background':begin,
               'qualification':'CONSERVATIVE_RESEARCH_SEPARATOR_ONLY_NOT_MARKET_STRUCTURE_BOUNDARY; full calendar/actions remain unverified'},
            'backward_envelope':{'events':events,'candidates':records,'candidate_count':len(records)},
            'close_turn_baseline':{'candidates':turns,'candidate_count':len(turns)},
            'common_price_suffix':{'start_index':start,'start_date':bars[start]['date'],'observed_through':cutoff,
               'records':len(bars)-start,'common_low':str(low),'common_high':str(high),
               'positive_width':low<high,'left_blocker':blocked,
               'qualification':'LATEST_LOCAL_COMMON_CELL_SEED_NOT_WHOLE_INTERVAL'},
            'data_boundary_seed':{'start_date':bars[begin]['date'],'observed_through':cutoff,
               'qualification':'AVAILABLE_DATA_BOUNDARY_ONLY_NOT_FORMATION_SIGNAL'},
            'formal_membership':None,'primary_pressure_id':None,'historical_selection_time':None,
            'historical_signal_eligible':False,'classification_quality':'NOT_VALIDATED','action_qualification':'NOT_EVALUATED'}
    result['research_output_id']=digest(result)
    return result

def run(source2884,source1101):
    # These are evaluation cutoffs, never passed as target starts to the generator.
    jobs=[('2884-Oct7',source2884,'2026-10-07'),('2884-direction-control',source2884,'2026-05-04'),
          ('1101-ABC-May14',source1101,'2025-05-14'),('1101-ABC-Jun2',source1101,'2025-06-02'),
          ('1101-ABC-Jun3',source1101,'2025-06-03')]
    return {name:propose(src,cut)for name,src,cut in jobs}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
    p=Path(a.out);p.mkdir(parents=True,exist_ok=True)
    raw=Path(a.source).read_bytes();other=Path(a.comparison).read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
    assert hashlib.sha256(other).hexdigest()=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
    results=run(json.loads(raw),json.loads(other))
    (p/'proposals.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    summary={name:{'cutoff':r['data_cutoff'],'eligible_rows':r['eligibility_scope']['records'],
                 'envelope_starts':r['backward_envelope']['candidate_count'],
                 'close_starts':r['close_turn_baseline']['candidate_count'],
                 'common_suffix_start':r['common_price_suffix']['start_date'],'common_suffix_records':r['common_price_suffix']['records']}
             for name,r in results.items()}
    (p/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    assert hashlib.sha256(Path(a.source).read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
    assert hashlib.sha256(Path(a.comparison).read_bytes()).hexdigest()==hashlib.sha256(other).hexdigest()
    print(json.dumps(summary))
