"""Persistent post-departure evidence, never a formal interval selector.

Reads immutable prior events; no old research driver or production core rerun.
Same crossed boundary families are correlated evidence, not independent votes.
"""
from pathlib import Path
from decimal import Decimal as D
from collections import defaultdict
import argparse,json,hashlib,gzip

canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
digest=lambda x:'sha256:'+hashlib.sha256(canon(x)).hexdigest()

def track(source,event,cutoff):
    if event['kind']!='WHOLE_BAR_OUTSIDE_FROZEN_FRAME':raise ValueError('requires saved whole-bar event')
    day=event['known_on_saved_bar']
    if cutoff<day:raise ValueError('event unavailable before known date')
    if event['code']!=source['code']:raise ValueError('source mismatch')
    available=[b for b in source['bars']if b['date']<=cutoff]
    if not available or available[-1]['date']!=cutoff:raise ValueError('cutoff must be saved date')
    frame=event['frozen_frame'];lo,hi=D(frame['lower']),D(frame['upper']);direction=event['direction']
    boundary=hi if direction=='UP'else lo
    declared=source['source_gaps']['known_calendar_missing_dates']
    gaps=[g for g in declared if day<g<=cutoff]
    stop=min(gaps)if gaps else None
    rows=[b for b in available if day<=b['date']and(stop is None or b['date']<stop)]
    if not rows or rows[0]['date']!=day:raise ValueError('event bar unavailable')
    if rows[0]!=event['current_bar']:raise ValueError('saved event/source bar mismatch')
    monitor_id=digest({'method':'persistent-frozen-frame-followup/0.1','event_id':event['event_id']})
    facts=[];first_contact=None;first_inside=None;first_opposite=None
    for i,b in enumerate(rows):
        l,h,c=D(b['low']),D(b['high']),D(b['close'])
        whole=h<lo if direction=='DOWN'else l>hi
        contact=l<=boundary<=h
        inside=lo<=c<=hi
        opposite=c>hi if direction=='DOWN'else c<lo
        relation='INSIDE_FROZEN_FRAME'if inside else 'DEPARTURE_SIDE'if(c<lo if direction=='DOWN'else c>hi)else'OPPOSITE_SIDE'
        fact={'known_on_saved_bar':b['date'],'whole_bar_on_departure_side':whole,
              'crossed_boundary_contact':contact,'close_relation':relation,'bar':b}
        fact['fact_id']=digest({'monitor_id':monitor_id,**fact});facts.append(fact)
        if i:
            if contact and first_contact is None:first_contact=b['date']
            if inside and first_inside is None:first_inside=b['date']
            if opposite and first_opposite is None:first_opposite=b['date']
    # New completed-close turns use only later unequal completed closes.
    turns=[];i=0
    while i<len(rows):
        j=i
        while j+1<len(rows)and D(rows[j+1]['close'])==D(rows[i]['close']):j+=1
        if i>0 and j+1<len(rows):
            before,cur,after=D(rows[i-1]['close']),D(rows[i]['close']),D(rows[j+1]['close'])
            if(cur>before and cur>after)or(cur<before and cur<after):
                turn={'kind':'HIGH'if cur>before else'LOW','plateau_start':rows[i]['date'],
                      'plateau_end':rows[j]['date'],'close':rows[i]['close'],'known_on_saved_bar':rows[j+1]['date']}
                turn['turn_id']=digest({'monitor_id':monitor_id,**turn});turns.append(turn)
        i=j+1
    seen=set();two_sided=None
    for t in turns:
        seen.add(t['kind'])
        if len(seen)==2:two_sided=t['known_on_saved_bar'];break
    frame_rows=[b for b in available if frame['frame_start']<=b['date']<=frame['frame_observed_end']]
    origins=[b['date']for b in frame_rows if D(b['high']if direction=='UP'else b['low'])==boundary]
    result={'schema':'m1-persistent-followup-research/0.1','monitor_id':monitor_id,'event_id':event['event_id'],
        'code':source['code'],'event_known_on':day,'requested_cutoff':cutoff,'observed_through':rows[-1]['date'],
        'observation_start':event['observation_start'],'frozen_frame':frame,'direction':direction,
        'crossed_boundary':str(boundary),'boundary_origin_dates':origins,'facts':facts,
        'first_later_boundary_contact':first_contact,'first_later_close_inside_frozen_frame':first_inside,
        'first_later_close_on_opposite_side':first_opposite,
        'seed_evidence':{'seed_date':day,'saved_records':len(rows),'new_completed_close_turns':turns,
                         'both_high_and_low_turns_available_on':two_sided,'formed_interval':None,
                         'qualification':'PRICE_PATH_DESCRIPTION_ONLY_NOT_FORMATION_OR_FORMAL_PARENT_CHILD'},
        'source_qualification':{'frame_crossed_listed_missing_dates':[g for g in declared if frame['frame_start']<=g<day],
            'followup_blocked_at_listed_missing_date':stop,'followup_truncated_at_gap':bool(gaps),
            'calendar_and_actions':'ORIGINAL_UNVERIFIED_LIMITATIONS_RETAINED'},
        'selected_alternative':None,'formal_end':None,'formal_membership':None,'primary_pressure_id':None,
        'historical_selection_time':None,'historical_signal_eligible':False,'classification_quality':'NOT_VALIDATED',
        'core_usefulness':'NOT_ESTABLISHED','actions':'NOT_EVALUATED'}
    result['research_output_id']=digest(result);return result

def families(source,results):
    """Group current saved event batch by physical crossed boundary; retain members."""
    groups=defaultdict(list)
    for result in results:
        by_id={e['event_id']:e for e in result['events']}
        for branch in result['branch_proposals']:
            e=by_id[branch['evidence_event_id']];f=e['frozen_frame'];up=e['direction']=='UP'
            boundary=D(f['upper']if up else f['lower'])
            key=(e['known_on_saved_bar'],e['direction'],str(boundary.normalize()))
            origin=[b['date']for b in source['bars']if f['frame_start']<=b['date']<=f['frame_observed_end']and D(b['high']if up else b['low'])==boundary]
            groups[key].append({'event_id':e['event_id'],'proposal_id':branch['proposal_id'],'start':result['start'],
               'frame_lower':f['lower'],'frame_upper':f['upper'],'frame_end':f['frame_observed_end'],
               'departure_date':f['departure_date'],'boundary_origin_dates':origin})
    out=[]
    for(day,direction,boundary),members in sorted(groups.items()):
        x={'code':source['code'],'event_day':day,'direction':direction,'crossed_boundary':boundary,
           'members':members,'member_count':len(members),'independent_vote_count':None,
           'formal_same_structure':None,'qualification':'CORRELATED_BOUNDARY_EVIDENCE_NOT_STRUCTURAL_MERGE_OR_VOTE'}
        x['family_id']=digest({'code':source['code'],'event_day':day,'direction':direction,'boundary':boundary});out.append(x)
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--prior-dir',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
    p=Path(a.out);p.mkdir(parents=True,exist_ok=True);prior=Path(a.prior_dir)
    source_paths=[Path(a.source),Path(a.comparison)];raws=[x.read_bytes()for x in source_paths]
    assert [hashlib.sha256(x).hexdigest()for x in raws]==['ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901','184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15']
    s,t=map(json.loads,raws);packed=(prior/'candidate-pools.json.gz').read_bytes();pools=json.loads(gzip.decompress(packed));scopes=json.loads((prior/'reviewed-scope-tests.json').read_text())
    assert hashlib.sha256(gzip.decompress(packed)).hexdigest()=='db4dc777c42dd89d605556be776841ba76e966ecdd9bd46055fbaa58e5d9c2b9'
    grouped={};batch_summaries={};count=0
    for name,pool in pools.items():
        src=s if name.startswith('2884')else t;grouped[name]=families(src,pool['results']);summaries=[]
        for r in pool['results']:
            for e in r['events']:
                if e['kind']!='WHOLE_BAR_OUTSIDE_FROZEN_FRAME':continue
                q=track(src,e,pool['cutoff']);count+=1
                summaries.append({k:q[k]for k in ['monitor_id','event_id','event_known_on','observation_start','observed_through','first_later_boundary_contact','first_later_close_inside_frozen_frame','first_later_close_on_opposite_side'] }|{'seed_records':q['seed_evidence']['saved_records'],'both_turns_on':q['seed_evidence']['both_high_and_low_turns_available_on'],'selected_alternative':None})
        batch_summaries[name]=summaries
    def find(scope,day):return next(e for e in scopes[scope]['events']if e['kind']=='WHOLE_BAR_OUTSIDE_FROZEN_FRAME'and e['known_on_saved_bar']==day)
    ae=find('ABC-next-record','2025-06-03');ge=find('G2-manual-scope-test','2023-02-21');g2=find('G2-manual-scope-test','2023-02-24');be=find('2884-later-rise','2026-10-16')
    controls={
        'ABC-first-bar':track(t,ae,'2025-06-03'),'ABC-through-Jun13':track(t,ae,'2025-06-13'),
        'G2-first-bar':track(t,ge,'2023-02-21'),'G2-boundary-touch':track(t,ge,'2023-02-22'),
        'G2-return':track(t,ge,'2023-03-01'),'G2-through-Mar3':track(t,ge,'2023-03-03'),
        'G2-second-frame-return':track(t,g2,'2023-03-03'),'2884-last-source-bar':track(s,be,'2026-10-16')}
    summary={'pool_monitor_observations':count,'pool_boundary_families':{k:len(v)for k,v in grouped.items()},
        'same_day_family_examples':{},'selected_scope_tests':{},'formal_branch_selection':'NOT_ESTABLISHED',
        'prior_events_modified':False,'source_sha256':[hashlib.sha256(x).hexdigest()for x in raws]}
    for name,day in [('ABC-Jun3','2025-06-03'),('2884-Oct16','2026-10-16')]:
        today=[g for g in grouped[name]if g['event_day']==day]
        summary['same_day_family_examples'][name]={'proposal_events':sum(g['member_count']for g in today),'boundary_families':len(today),'boundaries':[g['crossed_boundary']for g in today]}
    for name,q in controls.items():summary['selected_scope_tests'][name]={'event_date':q['event_known_on'],'cutoff':q['requested_cutoff'],'seed_records':q['seed_evidence']['saved_records'],'first_later_boundary_contact':q['first_later_boundary_contact'],'first_later_close_inside':q['first_later_close_inside_frozen_frame'],'both_turns_on':q['seed_evidence']['both_high_and_low_turns_available_on']}
    for name,obj in [('boundary-families.json',grouped),('pool-followup-summaries.json',batch_summaries),('selected-followups.json',controls),('summary.json',summary)]:
        (p/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    assert [x.read_bytes()for x in source_paths]==raws
    assert (prior/'candidate-pools.json.gz').read_bytes()==packed
    print(json.dumps(summary,ensure_ascii=False))
