"""Selected post-reference path witnesses, not a support/pressure classifier."""
import hashlib,json,sys
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
sys.path.insert(0,str(BASE/'observation-bundle-research'))
import observation_bundle as prior
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def side(value,point):
    a,b=map(D,[value,point]);return'ABOVE'if a>b else'BELOW'if a<b else'EQUAL'
def contains(b,price):return D(b['low'])<=D(price)<=D(b['high'])
def volume(a,b):
    x,y=int(a['volume_shares_scaled']),int(b['volume_shares_scaled'])
    return {'numerator':str(x),'denominator':str(y),'ratio_exact':str(x)+'/'+str(y)if y else None,
        'comparison':'HIGHER'if x>y else'LOWER'if x<y else'EQUAL','qualification':'DESCRIPTIVE_ONLY_NO_VOLUME_RULE_OR_THRESHOLD'}
def assess(source,q,cut,c):
    p=next(p for p in c['pivots']if p['id']==q['reference_id'])
    out={'query_id':q['query_id'],'code':q['code'],'cutoff':cut,'reference':None,'anchor_source_bar':None,'birth':None,
        'current_range_intersection_streak':None,'followup':None,'observed_path':[],
        'support_or_pressure_response_demonstrated':None,'volume_qualification':None,'importance_score':None,
        'formal_interval':None,'formal_start':None,'formal_end':None,'formal_membership':None,'formal_parent':None,'formal_merge':None,
        'selected_role':None,'primary_pressure_id':None,'historical_selection_time':None,'historical_signal_eligible':False,
        'original_core_snapshot_2026_10_07':None,'numeric_frame_2026_10_07':None,'manual_label_used':False,
        'classifier':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','Android':'NOT_TESTED_NEW_BUILD',
        'actions':'NOT_EVALUATED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'}
    if p['known_on']>cut:out['status']='ORIGINAL_REFERENCE_NOT_AVAILABLE';return out
    out['reference']=p
    bs=[b for b in source['bars']if b['date']<=cut]
    if q['anchor_date']>cut:out['status']='ANCHOR_NOT_YET_OBSERVED';return out
    i=next(i for i,b in enumerate(bs)if b['date']==q['anchor_date']);a=bs[i];out['anchor_source_bar']=a
    if a['date']<=p['known_on']:out['status']='FORMING_OR_SAME_DAY_SOURCE_NOT_POST_AVAILABILITY';return out
    if not contains(a,p['price']):out['status']='NO_DAILY_RANGE_INTERSECTION';return out
    if i==0:raise ValueError('No previous saved bar')
    previous=bs[i-1];gaps=source['source_gaps']['known_calendar_missing_dates']
    if contains(previous,p['price'])and previous['date']>p['known_on']and not any(previous['date']<d<=a['date']for d in gaps):
        raise ValueError('Selected anchor must begin a saved-row intersection streak; do not count every continued bar as independent')
    birth={'reference_id':p['id'],'reference_available_on':p['known_on'],'anchor_bar':a,'previous_saved_bar':previous,
        'previous_close_side':side(previous['close'],p['price']),'anchor_close_side':side(a['close'],p['price']),
        'frozen_contact_bar_range':[a['low'],a['high']],'anchor_volume_vs_previous_saved_bar':volume(a,previous),
        'previous_listed_gap_dates':[d for d in gaps if previous['date']<d<=a['date']],
        'meaning':'DAILY_RANGE_INTERSECTION_AND_CLOSE_LOCATION_NOT_INTRADAY_BOUNCE_OR_CONFIRMED_SUPPORT'}
    out['birth']={'witness_id':'sha256:'+hashlib.sha256(json.dumps(birth,sort_keys=True,separators=(',',':')).encode()).hexdigest(),**birth}
    later=bs[i+1:];gap=next((d for d in gaps if a['date']<d<=cut),None)
    usable=[b for b in later if gap is None or b['date']<gap]
    first=next((b for b in usable if D(b['close'])>D(a['high'])or D(b['close'])<D(a['low'])),None)
    follow_status='LATER_CLOSE_ABOVE_CONTACT_BAR'if first and D(first['close'])>D(a['high'])else'LATER_CLOSE_BELOW_CONTACT_BAR'if first else'LISTED_DATA_GAP_BEFORE_WITNESS'if gap else'WAITING_FOR_LATER_SAVED_CLOSE_OUTSIDE_CONTACT_BAR'
    last=a['date'];ended=None;streak_gap=None
    for b in later:
        before=next((d for d in gaps if last<d<=b['date']),None)
        if before:streak_gap=before;break
        if not contains(b,p['price']):ended=b['date'];break
        last=b['date']
    streak_bars=[b for b in bs[i:]if a['date']<=b['date']<=last]
    out.update({'status':'POST_AVAILABILITY_RANGE_INTERSECTION_RESEARCH','current_range_intersection_streak':{
        'start':a['date'],'last_intersection':last,'consecutive_saved_records':len(streak_bars),'first_later_non_intersection':ended,
        'listed_gap_stopping_continuity':streak_gap,'continuous_market_calendar_certified':False,'independent_test_count':None},
        'followup':{'status':follow_status,'first_later_close_outside_contact_bar':first,
            'first_later_high_above_contact_high':next((b for b in usable if D(b['high'])>D(a['high'])),None),
            'first_later_low_below_contact_low':next((b for b in usable if D(b['low'])<D(a['low'])),None),
            'first_listed_gap_after_anchor':gap,'witness_volume_vs_anchor':volume(first,a)if first else None,
            'formal_reaction_confirmation':None},
        'observed_path':[{'bar':b,'close_side_of_original_reference':side(b['close'],p['price']),
            'daily_range_contains_reference':contains(b,p['price']),'close_side_of_contact_range':
            'ABOVE'if D(b['close'])>D(a['high'])else'BELOW'if D(b['close'])<D(a['low'])else'INSIDE_OR_EQUAL',
            'after_listed_gap':gap is not None and b['date']>=gap}for b in bs[i:]]})
    return out
def specifications(c):
    rows=[('G2-low-later-up','1101','2023-03-13','2023-03-28',['2023-03-27','2023-03-28','2023-03-29','2023-04-07','2023-04-10','2023-04-11']),
        ('G2-low-later-down','1101','2023-05-15','2023-07-07',['2023-07-06','2023-07-07','2023-07-10','2023-07-11']),
        ('ABC-high-equality-then-down','1101','2025-04-10','2025-05-12',['2025-05-09','2025-05-12','2025-05-13','2025-05-14']),
        ('ABC-low-close-through','1101','2025-04-08','2025-06-02',['2025-05-29','2025-06-02','2025-06-03']),
        ('A-gap-control','2884','2026-09-17','2026-10-15',['2026-10-14','2026-10-15','2026-10-16']),
        ('G2-forming-source-control','1101','2023-05-02','2023-05-02',['2023-05-02','2023-05-09'])]
    return [{'query_id':name,'code':code,'reference_id':next(p['id']for p in c['pivots']if p['code']==code and p['scale']=='0.03'and p['occurred_at']==day),
        'anchor_date':anchor,'cutoffs':cuts,'selection':'EX_POST_CONTRASTS_NOT_PRIMARY_REFERENCE_SELECTION_OR_BLIND_SCAN'}for name,code,day,anchor,cuts in rows]
def main():
    sources,c=prior.load_inputs();qs=specifications(c);snap={q['query_id']+'@'+cut:assess(sources[q['code']],q,cut,c)for q in qs for cut in q['cutoffs']}
    write(ROOT/'queries.json',qs);write(ROOT/'response-witnesses.json',snap)
    write(ROOT/'summary.json',{'queries':len(qs),'cutoff_views':len(snap),'latest':{q['query_id']:snap[q['query_id']+'@'+q['cutoffs'][-1]]for q in qs},
        'research_driver_runs':1,'prior_driver_reruns':0,'new_pivot_or_local_candidate_generation':0,
        'reaction_classifier':'NOT_VALIDATED','support_or_pressure_response_demonstrated':None})
    write(ROOT/'exploration-notes.json',{'exploratory_command_runs':1,'source':'saved original3% pivots and saved bars only',
        'search':'post-availability intersecting bars with prior close not equal, and some later close outside that bar before selected scope end',
        'saved_scope_completed_occurrences':{'1101_2023-01-16_2023-08-16':173,'2884_2026-09-17_2026-10-16':0,'1101_2025-04-07_2025-06-13':36},
        'qualification':'EX_POST_LOOKAHEAD_FOR_SELECTING_OPPOSING_EXAMPLES_NOT_A_BACKTEST_OR_INDEPENDENT_MARKET_SAMPLE; overlapping dates/references recur; no success rate.'})
    ps=[prior.SOURCE,prior.COMPARISON,BASE/'overlap-role-research/overlap-role-registry.json.gz',BASE/'followup-role-research/followup-role-registry.json.gz',
        BASE/'followup-role-research/selected-role-proposals.json.gz',BASE/'source-role-research/source-role-registry.json.gz',BASE/'observation-bundle-research/evidence-extensions.json.gz']
    write(ROOT/'source-provenance.json',{'previous_verified_commit':'507cf5efa3e84a814211f1cc580fd0a06eb726e6',
        'files':{str(p):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in ps},
        'qualification':'RAW_CANDIDATE; actions/Adjusted/complete calendar/historical public timing unresolved; not an original historical core snapshot.'})
    print(json.dumps({'queries':len(qs),'cutoff_views':len(snap)}))
if __name__=='__main__':main()
