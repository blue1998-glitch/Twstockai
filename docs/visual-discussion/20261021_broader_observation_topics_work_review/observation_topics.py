"""Finite Work hypotheses: larger reading windows are not formal structures.

Joins version-bound saved evidence only; no new market scan or classifier validation.
"""
import gzip,hashlib,json,sys
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
sys.path.insert(0,str(BASE/'observation-bundle-research'))
import observation_bundle as prior
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def digest(x):return'sha256:'+hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def window(source,start,end):
    bs=[b for b in source['bars']if start<=b['date']<=end]
    if not bs:raise ValueError('No saved bars in reading window')
    return {'start':start,'observed_through':bs[-1]['date'],'saved_records':len(bs),
        'raw_reading_extent':{'low':str(min(D(b['low'])for b in bs)),'high':str(max(D(b['high'])for b in bs))},
        'listed_missing_dates':[d for d in source['source_gaps']['known_calendar_missing_dates']if start<=d<=end],
        'formal_membership':None,'formal_price_bounds':None,'continuity_certified':False}
def make_proposal(source,kind,start,born,support,cutoff):
    identity={'reading_topic':kind,'complete_evidence_start':start,'first_reviewable_on_saved_bars':born,'support_ids':support}
    return {'proposal_id':digest(identity),**identity,'birth_reading_window':window(source,start,born),
        'current_reading_window':window(source,start,cutoff),'formal_structure_established':False,
        'qualification':'A_WINDOW_FOR_COMPARING_ACTIVITIES_NOT_A_NEW_INTERVAL_OR_EXPANSION_OF_MANUAL_MEMBERSHIP'}
def assess(source,q,cutoff,c):
    if cutoff<q['cutoffs'][0]:raise ValueError('Outside specified illustrative research cutoffs')
    bs=[b for b in source['bars']if b['date']<=cutoff]
    if not bs:raise ValueError('No source prefix')
    out={'query_id':q['query_id'],'code':q['code'],'cutoff':cutoff,'source_observed_through':bs[-1]['date'],
        'evidence_ids':[],'evidence_facts':{},'reading_proposal':None,'current_episode':None,
        'formal_start':None,'formal_end':None,'formal_membership':None,'formal_parent':None,'formal_merge':None,
        'selected_role':None,'primary_pressure_id':None,'historical_selection_time':None,'historical_signal_eligible':False,
        'classification':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','actions':'NOT_EVALUATED',
        'capital_growth_flywheel_effectiveness':'NOT_EVALUATED','original_core_snapshot_2026_10_07':None,
        'manual_review_used':False,'research_scope':'SELECTED_EX_POST_QUERIES_NOT_BLIND_SCAN_OR_PROVEN_UNIVERSAL_RULES'}
    zm={z['zone_id']:z for z in c['zones']}
    if q['kind']=='PAIR':
        a,b=[zm[q[k]]for k in ['older_zone_id','later_zone_id']]
        for z in [a,b]:
            if z['known_on_saved_bar']<=cutoff:out['evidence_ids'].append(z['zone_id'])
        if a['known_on_saved_bar']>cutoff or b['known_on_saved_bar']>cutoff:
            out['research_response']='WAIT_FOR_COMPLETED_LATER_ACTIVITY';return out
        p=next(p for p in c['pairs']if p['older_zone_id']==a['zone_id']and p['later_zone_id']==b['zone_id'])
        assert p['known_on_saved_bar']<=cutoff
        out['evidence_ids'].append(p['comparison_id'])
        last=bs[-1];out['evidence_facts']={'known_on':p['known_on_saved_bar'],'freshness':p['freshness'],
            'common_price_relation':p['common_price_relation'],'raw_price_relation':p['raw_price_relation'],
            'actual_later_path_close_visits_older_core':p['actual_later_path_close_visits_older_core'],
            'confirmation_bar_close':b['right_evidence_bar']['close'],
            'confirmation_bar_close_vs_older_common':prior.location(b['right_evidence_bar']['close'],a['common_close_low'],a['common_close_high']),
            'current_close_vs_older_common':prior.location(last['close'],a['common_close_low'],a['common_close_high'])}
        if p['freshness']!='ALL_LATER_SOURCE_AFTER_OLDER_KNOWN':
            out['research_response']='SUPPLEMENT_EXISTING_ACTIVITY_WITH_REUSED_EVIDENCE';return out
        if p['common_price_relation']in ['LATER_RANGE_STRICTLY_BELOW','LATER_RANGE_STRICTLY_ABOVE']:
            out['research_response']='PROPOSE_CROSS_PRICE_ACTIVITY_READING'
            out['reading_proposal']=make_proposal(source,'COMPARE_COMPLETED_ACTIVITIES_AT_DIFFERENT_PRICES',prior.earliest(a,c),p['known_on_saved_bar'],[a['zone_id'],b['zone_id'],p['comparison_id']],cutoff)
        elif p['actual_later_path_close_visits_older_core']:
            out['research_response']='SUPPLEMENT_REVISIT_EVIDENCE_NO_NEW_BROADER_TOPIC_FROM_THIS_PAIR'
        else:
            out['research_response']='KEEP_GEOMETRIC_OVERLAP_AND_CONFIRMATION_DAY_ENTRY_SEPARATE'
        return out
    e=next(e for e in c['events']if e['event_id']==q['event_id'])
    if e['known_on_saved_bar']>cutoff:
        out['research_response']='WAIT_FOR_SAVED_DEPARTURE_EVENT';return out
    out['evidence_ids'].append(e['event_id'])
    h=prior.project_history(source,c['histories'][e['event_id']],cutoff)
    out['evidence_facts']={'event_known_on':e['known_on_saved_bar'],'fixed_frame':e['frozen_frame'],
        'trace_observed_through':h['observed_through'],'trace_covers_cutoff':h['covers_requested_cutoff'],
        'current_close_vs_fixed_frame':prior.location(bs[-1]['close'],e['frozen_frame']['lower'],e['frozen_frame']['upper'])}
    links=[l for l in c['followup_links']if l['event_id']==e['event_id']and l['known_on']<=cutoff and(q.get('zone_id')is None or l['zone_id']==q['zone_id'])]
    if not links:
        out['research_response']='TRACK_DEPARTURE_NO_COMPLETED_FOLLOWUP_TOPIC_YET';return out
    assert len(links)==1,'Selected queries require exactly one explicitly specified followup activity'
    link=links[0];z=zm[link['zone_id']];ep=next(ep for ep in h['episodes']if ep['episode_id']==link['episode_id'])
    out['evidence_ids']+=[link['link_id'],z['zone_id'],ep['episode_id']]
    out['current_episode']=ep
    out['evidence_facts'].update({'followup_known_on':link['known_on'],'followup_path':[z['path_start'],z['path_end']],
        'followup_common':[z['common_close_low'],z['common_close_high']],
        'followup_raw':[z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']],
        'activity_birth_status':link['status_at_birth']})
    out['research_response']='PROPOSE_OLD_FRAME_AND_LATER_OUTSIDE_ACTIVITY_READING'
    out['reading_proposal']=make_proposal(source,'COMPARE_RETAINED_FRAME_WITH_LATER_OUTSIDE_ACTIVITY',e['frozen_frame']['frame_start'],link['known_on'],[e['event_id'],link['link_id'],z['zone_id'],ep['episode_id']],cutoff)
    return out

def specifications(c):
    specs=json.loads((BASE/'overlap-role-research/selected-query-specs.json').read_text());qs=[]
    for name,cuts in [('ABC-fresh-lower',['2025-05-23','2025-05-26','2025-06-02']),('G2-fresh-overlap',['2023-02-09','2023-02-10']),
                      ('B-shared-path',['2026-04-27','2026-04-28']),('A-reused-context',['2026-10-08','2026-10-12'])]:
        qs.append({'query_id':name,'kind':'PAIR','code':'1101'if name.startswith(('ABC','G2'))else'2884',
                   'older_zone_id':specs[name]['older_zone_id'],'later_zone_id':specs[name]['later_zone_id'],'cutoffs':cuts})
    a=next(z for z in c['zones']if z['code']=='1101'and z['path_start']=='2023-01-17'and z['path_end']=='2023-02-09')
    b=next(z for z in c['zones']if z['code']=='1101'and z['path_start']=='2023-03-15'and z['path_end']=='2023-03-24')
    qs.append({'query_id':'G2-geometric-only','kind':'PAIR','code':'1101','older_zone_id':a['zone_id'],'later_zone_id':b['zone_id'],'cutoffs':['2023-03-24','2023-03-27']})
    for name,code,start,upper,zstart,zend,cuts in [
        ('ABC-outside','1101','2025-04-07','31.40','2025-06-06','2025-06-11',['2025-06-03','2025-06-11','2025-06-12','2025-06-13']),
        ('G2-outside-return','1101','2023-01-16','37.85','2023-04-24','2023-04-26',['2023-04-26','2023-04-27','2023-05-12']),
        ('A-latest-departure','2884','2026-09-17','47.35',None,None,['2026-10-15','2026-10-16'])]:
        e=next(e for e in c['events']if e['code']==code and e['frozen_frame']['frame_start']==start and e['frozen_frame']['upper']==upper)
        zid=next(z['zone_id']for z in c['zones']if z['code']==code and z['path_start']==zstart and z['path_end']==zend)if zstart else None
        qs.append({'query_id':name,'kind':'EVENT','code':code,'event_id':e['event_id'],'zone_id':zid,'cutoffs':cuts})
    return qs
def main():
    sources,c=prior.load_inputs();qs=specifications(c)
    snapshots={q['query_id']+'@'+cut:assess(sources[q['code']],q,cut,c)for q in qs for cut in q['cutoffs']}
    write(ROOT/'queries.json',{'selection':'EX_POST_RESEARCH_COMPARISONS_NOT_HISTORICAL_SELECTION','queries':qs})
    write(ROOT/'reading-proposals.json',snapshots)
    proposals={r['reading_proposal']['proposal_id']:r['reading_proposal']for r in snapshots.values()if r['reading_proposal']}
    write(ROOT/'summary.json',{'queries':len(qs),'cutoff_views':len(snapshots),'distinct_reading_proposals':len(proposals),
        'proposals':{p['reading_topic']+'@'+p['first_reviewable_on_saved_bars']:{'proposal_id':p['proposal_id'],'birth_window':p['birth_reading_window']}for p in proposals.values()},
        'research_hypothesis_driver_runs':1,'new_market_thresholds':0,'new_seed_turn_original_core_generation':0,'prior_driver_reruns':0,
        'manual_labels_used':False,'formal_structure_classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD'})
    paths=[prior.SOURCE,prior.COMPARISON,BASE/'observation-bundle-research/observation-bundles.json.gz',BASE/'observation-bundle-research/evidence-extensions.json.gz',
        BASE/'overlap-role-research/overlap-role-registry.json.gz',BASE/'overlap-role-research/selected-query-specs.json',
        BASE/'followup-role-research/followup-role-registry.json.gz',BASE/'followup-role-research/selected-role-proposals.json.gz',BASE/'source-role-research/source-role-registry.json.gz']
    write(ROOT/'source-provenance.json',{'files':{str(p):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in paths},
        'prior_commit':'7790e911c5072d4ebdca1016f118f0c7a7b209eb','qualification':'Raw candidate; calendar/actions/Adjusted/historical publication unresolved; prior saved universe not historical selection.'})
    print(json.dumps({'queries':len(qs),'cutoff_views':len(snapshots),'distinct_reading_proposals':len(proposals)}))
if __name__=='__main__':main()
