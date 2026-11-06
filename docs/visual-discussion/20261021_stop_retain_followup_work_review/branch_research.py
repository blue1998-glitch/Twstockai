"""Research alternatives for observation windows. Never decides formal membership.

Envelope is raw observed geometry, not approved support/resistance or a box.
Only a first completed close outside a prior observed envelope freezes a frame.
A later entire bar beyond that frozen frame emits a stop/next-seed ALTERNATIVE,
while an unsegmented continuation remains available. No branch is auto-selected.
"""
from pathlib import Path
from decimal import Decimal as D
import argparse,json,hashlib,sys,gzip

canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
digest=lambda x:'sha256:'+hashlib.sha256(canon(x)).hexdigest()

def observe(source,start,cutoff):
    rows=[b for b in source['bars']if start<=b['date']<=cutoff]
    if not rows or rows[0]['date']!=start or rows[-1]['date']!=cutoff:raise ValueError('start/cutoff must be saved dates')
    lo=D(rows[0]['low']);hi=D(rows[0]['high']);pending=None;events=[];branches=[]
    known_gaps=[g for g in source['source_gaps']['known_calendar_missing_dates']if start<=g<=cutoff]
    def emit(kind,index,detail):
        x={'kind':kind,'code':source['code'],'observation_start':start,'known_on_saved_bar':rows[index]['date'],**detail}
        x['event_id']=digest(x);events.append(x);return x
    for i,b in enumerate(rows[1:],1):
        l,h,c=D(b['low']),D(b['high']),D(b['close'])
        if pending is not None:
            lower,upper=D(pending['lower']),D(pending['upper'])
            whole=h<lower if pending['direction']=='DOWN'else l>upper
            if whole:
                event=emit('WHOLE_BAR_OUTSIDE_FROZEN_FRAME',i,{'direction':pending['direction'],'departure_date':pending['departure_date'],
                    'frozen_frame':pending,'current_bar':b,'qualification':'GEOMETRIC_EVIDENCE_ONLY_NOT_FORMAL_CLEARANCE'})
                gaps_here=[g for g in known_gaps if g<=b['date']]
                branch={'evidence_event_id':event['event_id'],'known_on_saved_bar':b['date'],
                    'stop_alternative':{'observed_start':start,'proposed_observation_end':rows[i-1]['date'],'records':i,
                                        'formal_end':None,'recognized_form':None},
                    'following_seed_alternative':{'proposed_start':b['date'],'status':'ONE_BAR_OBSERVATION_SEED_NOT_FORMED_INTERVAL','formal_lineage':None},
                    'continue_alternative':{'observed_start':start,'observed_through':b['date'],'records':i+1,'membership_decision':None},
                    'selected_alternative':None,'crossed_listed_missing_dates':gaps_here,
                    'source_qualified_for_stop_decision':False if gaps_here else None,
                    'qualification':'COMPETING_RESEARCH_PROPOSALS_NOT_A_FORMAL_SPLIT'}
                branch['proposal_id']=digest(branch);branches.append(branch);pending=None
            elif lower<=c<=upper:
                emit('RETURNED_INSIDE_FROZEN_FRAME',i,{'previous_departure':pending,'current_bar':b,
                    'qualification':'CLOSE_RETURN_EVENT_NOT_INTRADAY_ORDER_OR_FORMAL_REPAIR'});pending=None
            elif(pending['direction']=='DOWN'and c>upper)or(pending['direction']=='UP'and c<lower):
                old=pending
                pending={**pending,'direction':'UP'if c>upper else'DOWN','departure_date':b['date']}
                emit('OPPOSITE_CLOSE_BEFORE_WHOLE_BAR_EVENT',i,{'previous_departure':old,'new_pending':pending,'current_bar':b})
            # Otherwise the close stays outside but the bar still straddles the frame.
        elif c<lo or c>hi:
            pending={'direction':'DOWN'if c<lo else'UP','lower':str(lo),'upper':str(hi),
                     'frame_start':start,'frame_observed_end':rows[i-1]['date'],'frame_records':i,'departure_date':b['date'],
                     'frame_bars_fingerprint':digest(rows[:i]),'formal_price_bounds':None}
            emit('FIRST_CLOSE_OUTSIDE_OBSERVED_FRAME',i,{'pending':pending,'current_bar':b})
        # The continuation observes every bar. Frozen pending frames do not expand.
        lo=min(lo,l);hi=max(hi,h)
    result={'schema':'m1-observation-branch-research/0.1','code':source['code'],'start':start,'data_cutoff':cutoff,
        'source_records':len(rows),'bars_fingerprint':digest(rows),'events':events,'branch_proposals':branches,
        'continue_observation':{'start':start,'through':cutoff,'records':len(rows),'observed_low':str(lo),'observed_high':str(hi)},
        'pending_departure':pending,'crossed_listed_missing_dates':known_gaps,
        'formal_start':None,'formal_end':None,'formal_membership':None,'selected_branch':None,
        'primary_pressure_id':None,'historical_selection_time':None,'historical_signal_eligible':False,
        'classification_quality':'NOT_VALIDATED','action_qualification':'NOT_EVALUATED'}
    result['research_output_id']=digest(result);return result

def jobs(s,t,prior_generator):
    configs=[('2884-Oct7',s,'2026-10-07'),('2884-Oct16',s,'2026-10-16'),
             ('2884-control-May4',s,'2026-05-04'),('ABC-May14',t,'2025-05-14'),('ABC-Jun2',t,'2025-06-02'),('ABC-Jun3',t,'2025-06-03')]
    pools={}
    for name,source,cut in configs:
        prior=prior_generator(source,cut)
        starts=[c['start_date']for c in prior['backward_envelope']['candidates']]
        pools[name]={'cutoff':cut,'source_prefix_records':prior['source_prefix_records'],
                     'candidate_method':'backward-envelope-seed/0.1_UNCHANGED_REUSED_FUNCTION_NOT_CLI_RERUN',
                     'results':[observe(source,start,cut)for start in starts]}
    # These scopes test accepted examples only, outside automatic generator inputs.
    scopes={
      '2884-reviewed-cutoff':observe(s,'2026-09-17','2026-10-07'),
      '2884-later-rise':observe(s,'2026-09-17','2026-10-16'),
      '2884-direction-control':observe(s,'2026-04-15','2026-05-04'),
      'ABC-reviewed-39':observe(t,'2025-04-07','2025-06-02'),
      'ABC-next-record':observe(t,'2025-04-07','2025-06-03'),
      'G2-manual-scope-test':observe(t,'2023-01-16','2023-08-16')}
    return pools,scopes

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--prior-module',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
    p=Path(a.out);p.mkdir(parents=True,exist_ok=True)
    sraw=Path(a.source).read_bytes();traw=Path(a.comparison).read_bytes()
    assert hashlib.sha256(sraw).hexdigest()=='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
    assert hashlib.sha256(traw).hexdigest()=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
    prior_raw=Path(a.prior_module).read_bytes();assert hashlib.sha256(prior_raw).hexdigest()=='7e7ccc3d4d9fcb091c502c0ae7ee813a9a2722fd7bb70459d9aa8039d6606483'
    sys.path.insert(0,str(Path(a.prior_module).parent));from proposal_research import propose
    pools,scopes=jobs(json.loads(sraw),json.loads(traw),propose)
    for name,obj in [('candidate-pools.json',pools),('reviewed-scope-tests.json',scopes)]:
        (p/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    (p/'candidate-pools.json.gz').write_bytes(gzip.compress((p/'candidate-pools.json').read_bytes(),mtime=0))
    summary={'pool_cases':{name:{'candidate_starts':len(x['results']),'branch_proposals':sum(len(z['branch_proposals'])for z in x['results'])}for name,x in pools.items()},
             'scope_tests':{name:{'events':[(e['kind'],e['known_on_saved_bar'])for e in x['events']],
                  'proposed_ends':[z['stop_alternative']['proposed_observation_end']for z in x['branch_proposals']],
                  'source_gap_qualification':x['crossed_listed_missing_dates']}for name,x in scopes.items()},
             'source_sha256':hashlib.sha256(sraw).hexdigest(),'comparison_sha256':hashlib.sha256(traw).hexdigest(),
             'prior_generator_sha256':hashlib.sha256(prior_raw).hexdigest(),'formal_endpoint_rule':'NOT_ESTABLISHED','selected_branch':None}
    (p/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    assert Path(a.source).read_bytes()==sraw and Path(a.comparison).read_bytes()==traw and Path(a.prior_module).read_bytes()==prior_raw
    print(json.dumps(summary,ensure_ascii=False))
