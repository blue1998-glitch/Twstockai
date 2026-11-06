"""Same-reference paths: price positions are not proof of support or pressure.

Independent research audit of saved original pivots and saved local candidates.
"""
import hashlib,json,sys
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
sys.path.insert(0,str(BASE/'observation-bundle-research'))
import observation_bundle as prior
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def uid(x):return'sha256:'+hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def interval_side(lo,hi,price):
    a,b,p=map(D,[lo,hi,price]);return'BELOW'if b<p else'ABOVE'if a>p else'CONTAINS_OR_EQUALS_REFERENCE'
def facts(b,p):
    price=D(p['price']);o,h,l,cl=[D(b[k])for k in ['open','high','low','close']];up=p['kind']=='HIGH'
    return {'bar':b,'close_side':'ABOVE'if cl>price else'BELOW'if cl<price else'EQUAL',
        'daily_price_range_contains_reference':l<=price<=h,
        'strict_extreme_excursion':h>price if up else l<price,
        'strict_close_beyond_original_extreme':cl>price if up else cl<price,
        'whole_bar_beyond_original_extreme':l>price if up else h<price}
def audit(source,p,scope_start,cutoff,c):
    out={'reference_id':p['id'],'reference_available':p['known_on']<=cutoff}
    if not out['reference_available']:return out
    bars=[b for b in source['bars']if p['known_on']<=b['date']<=cutoff];fs=[facts(b,p)for b in bars]
    if not fs:raise ValueError('No saved bars after original reference availability')
    zs=[z for z in c['zones']if z['code']==p['code']and z['known_on_saved_bar']<=cutoff and prior.earliest(z,c)>=scope_start]
    zviews=[{'zone_id':z['zone_id'],'relationship_first_available_on':max(p['known_on'],z['known_on_saved_bar']),
        'common_side':interval_side(z['common_close_low'],z['common_close_high'],p['price']),
        'raw_path_side':interval_side(z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high'],p['price']),
        'complete_source_strictly_after_reference_available':prior.earliest(z,c)>p['known_on']}for z in zs]
    first={k:next((f['bar']for f in fs if f[k]),None)for k in ['daily_price_range_contains_reference','strict_extreme_excursion','strict_close_beyond_original_extreme','whole_bar_beyond_original_extreme']}
    cross=first['strict_close_beyond_original_extreme'];question=None
    if cross:
        birth={'reference_id':p['id'],'trigger_bar':cross,'known_on_saved_bar':cross['date'],
            'topic':'REVIEW_PATH_AFTER_SAVED_CLOSE_CROSSED_RETAINED_ORIGINAL_REFERENCE'}
        question={'question_id':uid(birth),**birth,'formal_structure_established':False,'action_eligible':None}
    return {**out,'reference':p,'measurement_start':p['known_on'],'observed_through':bars[-1]['date'],
        'saved_bar_facts':fs,'first_saved_events_from_reference_availability':first,
        'current_close_side':fs[-1]['close_side'],'local_activity_views':zviews,
        'post_cross_completed_local_ids':[z['zone_id']for z in zs if cross and prior.earliest(z,c)>cross['date']],
        'review_question':question,'support_or_pressure_response_demonstrated':None,'importance_score':None,
        'listed_missing_dates':[d for d in source['source_gaps']['known_calendar_missing_dates']if p['known_on']<=d<=cutoff],
        'continuous_calendar_certified':False,'qualification':'OHLC_RANGE_CONTAINMENT_IS_NOT_INTRADAY_ORDER_OR_TRADE_AT_REFERENCE; SAME_SIDE_IS_NOT_PROVEN_CONSTRAINT'}
def specifications(c):
    configs=[('A','2884','2026-09-17',['2026-10-06','2026-10-07','2026-10-12','2026-10-14','2026-10-15','2026-10-16'],['2026-09-17','2026-10-01']),
             ('ABC','1101','2025-04-07',['2025-05-13','2025-05-14','2025-05-26','2025-06-02','2025-06-03','2025-06-12','2025-06-13'],['2025-03-12','2025-04-08','2025-05-13']),
             ('G2','1101','2023-01-16',['2023-04-27','2023-05-09','2023-05-12','2023-08-16'],['2023-05-02'])]
    return [{'group':name,'code':code,'local_research_scope_start':start,'cutoffs':cuts,
        'reference_ids':[next(p['id']for p in c['pivots']if p['code']==code and p['scale']=='0.03'and p['occurred_at']==day)for day in days],
        'selection':'EX_POST_FINITE_RESEARCH_NOT_HISTORICAL_SELECTION_OR_PRIMARY_REFERENCE_CHOICE'}for name,code,start,cuts,days in configs]
def compose(source,q,cut,c):
    pm={p['id']:p for p in c['pivots']}
    return {'group':q['group'],'code':q['code'],'cutoff':cut,
        'references':[audit(source,pm[pid],q['local_research_scope_start'],cut,c)for pid in q['reference_ids']],
        'formal_interval':None,'formal_start':None,'formal_end':None,'formal_membership':None,'formal_parent':None,'formal_merge':None,
        'selected_role':None,'primary_pressure_id':None,'historical_selection_time':None,'historical_signal_eligible':False,
        'original_core_snapshot_2026_10_07':None,'numeric_frame_2026_10_07':None,'manual_label_used':False,
        'classifier':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','Android':'NOT_TESTED_NEW_BUILD',
        'actions':'NOT_EVALUATED','capital_growth_flywheel_effectiveness':'NOT_EVALUATED'}
def main():
    sources,c=prior.load_inputs();qs=specifications(c);snap={q['group']+'@'+cut:compose(sources[q['code']],q,cut,c)for q in qs for cut in q['cutoffs']}
    write(ROOT/'queries.json',qs);write(ROOT/'reference-paths.json',snap)
    latest={q['group']:snap[q['group']+'@'+q['cutoffs'][-1]]for q in qs}
    write(ROOT/'summary.json',{'groups':len(qs),'cutoff_views':len(snap),'reference_views':sum(len(v['references'])for v in snap.values()),
        'available_reference_views':sum(r['reference_available']for v in snap.values()for r in v['references']),
        'original_references':sum(len(q['reference_ids'])for q in qs),'latest':{k:[{'reference_id':r['reference_id'],'price':r['reference']['price'],'kind':r['reference']['kind'],
        'first_events':r['first_saved_events_from_reference_availability'],'local_candidates':len(r['local_activity_views']),
        'entire_raw_paths_below':sum(v['raw_path_side']=='BELOW'for v in r['local_activity_views']),
        'entire_raw_paths_above':sum(v['raw_path_side']=='ABOVE'for v in r['local_activity_views']),
        'daily_range_contains_count':sum(f['daily_price_range_contains_reference']for f in r['saved_bar_facts']),
        'post_cross_complete_local_candidates':len(r['post_cross_completed_local_ids'])}for r in v['references']]for k,v in latest.items()},
        'research_driver_runs':1,'new_original_pivot_or_local_candidate_generation':0,'prior_driver_reruns':0,
        'response_or_constraint_inference':'NOT_ESTABLISHED','classifier':'NOT_VALIDATED'})
    ps=[prior.SOURCE,prior.COMPARISON,BASE/'overlap-role-research/overlap-role-registry.json.gz',BASE/'followup-role-research/followup-role-registry.json.gz',
        BASE/'followup-role-research/selected-role-proposals.json.gz',BASE/'source-role-research/source-role-registry.json.gz',
        BASE/'observation-bundle-research/evidence-extensions.json.gz',BASE/'broader-observation-research/reading-proposals.json']
    write(ROOT/'source-provenance.json',{'files':{str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in ps},
        'previous_verified_commit':'6c6eaf8affd644eb125f0691f4088089240b623d','source_qualification':'Raw candidate; corporate actions/Adjusted/calendar/historical publication unresolved; original confirmation metadata is not an original historical core snapshot.'})
    print(json.dumps({'cutoff_views':len(snap),'reference_views':sum(len(v['references'])for v in snap.values())}))
if __name__=='__main__':main()
