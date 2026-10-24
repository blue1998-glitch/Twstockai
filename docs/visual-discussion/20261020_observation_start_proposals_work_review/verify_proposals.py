"""Verify experimental seed geometry and cutoff isolation, not classification quality."""
from pathlib import Path
from decimal import Decimal as D
from copy import deepcopy
import argparse,json,hashlib
from proposal_research import propose,run,canon

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);s=json.loads(Path(a.source).read_text());t=json.loads(Path(a.comparison).read_text())
saved=json.loads((p/'proposals.json').read_text());assert saved==run(s,t)
independent=[];prefix_checks=0
for name,r in saved.items():
    src=s if r['code']=='2884'else t
    b=[b for b in src['bars']if b['date']<=r['data_cutoff']]
    begin=r['eligibility_scope']['first_eligible_index'];want=set();events=[]
    for i in range(begin,len(b)-1):
        later=b[i+1:];lower=min(D(x['low'])for x in later);upper=max(D(x['high'])for x in later)
        if D(b[i]['low'])<lower or D(b[i]['high'])>upper:
            want|={i,i+1};events.append(i)
    actual={x['start_index']for x in r['backward_envelope']['candidates']}
    assert actual==want
    assert sorted(x['origin_index']for x in r['backward_envelope']['events'])==events
    tail=r['common_price_suffix'];z=b[tail['start_index']:]
    assert min(D(x['high'])for x in z)==D(tail['common_high'])
    assert max(D(x['low'])for x in z)==D(tail['common_low'])
    if tail['start_index']>begin:
        extended=b[tail['start_index']-1:]
        assert max(D(x['low'])for x in extended)>=min(D(x['high'])for x in extended)
    for c in r['close_turn_baseline']['candidates']:assert c['start_date']<c['right_evidence_at']<=r['data_cutoff']
    truncated={**src,'bars':b};assert propose(truncated,r['data_cutoff'])==r
    poison=deepcopy(src)
    for bar in poison['bars']:
        if bar['date']>r['data_cutoff']:
            for f in ['open','high','low','close']:bar[f]='999999999.99'
    poison['source_gaps']['known_calendar_missing_dates'].append('2222-01-01')
    assert propose(poison,r['data_cutoff'])==r
    transformed=deepcopy(src)
    for bar in transformed['bars']:
        for f in ['open','high','low','close']:bar[f]=str(D(bar[f])*D(10)+D(7))
    rt=propose(transformed,r['data_cutoff'])
    assert [x['start_date']for x in rt['backward_envelope']['candidates']]==[x['start_date']for x in r['backward_envelope']['candidates']]
    assert rt['common_price_suffix']['start_date']==r['common_price_suffix']['start_date']
    independent.append({'case':name,'independent_forward_later_min_max':'PASS','truncation_and_future_poison':'PASS','positive_affine_price_transform':'PASS'})

for src,key in [(s,'2884-Oct7'),(t,'1101-ABC-Jun2')]:
    r=saved[key];bs=[b for b in src['bars']if b['date']<=r['data_cutoff']]
    begin=r['eligibility_scope']['first_eligible_index']
    for end in range(begin,len(bs)):
        cut=bs[end]['date']
        assert propose(src,cut)==propose({**src,'bars':bs[:end+1]},cut)
        prefix_checks+=1

def dates(r,method):return {x['start_date']for x in r[method]['candidates']}
assert '2026-09-17'in dates(saved['2884-Oct7'],'backward_envelope')
for k in ['1101-ABC-May14','1101-ABC-Jun2','1101-ABC-Jun3']:assert '2025-04-07'in dates(saved[k],'backward_envelope')
assert '2025-05-13'in dates(saved['1101-ABC-Jun2'],'backward_envelope')
assert '2025-05-13'not in dates(saved['1101-ABC-Jun2'],'close_turn_baseline')
c2=next(c for c in saved['1101-ABC-Jun2']['backward_envelope']['candidates']if c['start_date']=='2025-04-07')
c3=next(c for c in saved['1101-ABC-Jun3']['backward_envelope']['candidates']if c['start_date']=='2025-04-07')
assert c2['records']==39 and c3['records']==40 and c2['candidate_id']!=c3['candidate_id']
assert c2['formal_end']is None and c3['formal_end']is None

def synthetic(closes):
    return {'code':'SYNTHETIC','source_gaps':{'known_calendar_missing_dates':[]},'bars':[{'date':f'2000-01-{i+1:02d}','open':str(c),'close':str(c),'high':str(D(c)+D('.5')),'low':str(D(c)-D('.5')),'volume_shares_scaled':'1'}for i,c in enumerate(closes)]}
flat=propose(synthetic([10,10,10,10]),'2000-01-04')
assert flat['backward_envelope']['candidate_count']==0 and flat['close_turn_baseline']['candidate_count']==0 and flat['common_price_suffix']['records']==4
plateau=synthetic([10,11,11,10]);p3=propose(plateau,'2000-01-03');p4=propose(plateau,'2000-01-04')
assert p3['close_turn_baseline']['candidate_count']==0
assert {c['start_date']for c in p4['close_turn_baseline']['candidates']}=={'2000-01-02','2000-01-03'}
assert all(c['right_evidence_at']=='2000-01-04'for c in p4['close_turn_baseline']['candidates'])

v={'schema':'m1-observation-start-verification/1','proposal_driver_runs':1,'verification_script_runs':1,
   'fixed_output_cases':len(saved),'independent_case_checks':independent,'all_active_segment_prefix_equalities':prefix_checks,
   'synthetic_checks':['constant prices produce no envelope event or close-turn event','unfinished equal-close plateau not confirmed','plateau confirmed only after later unequal close'],
   'reviewed_reference_recovery':{'2884_Sep17':'PRESENT_AS_ONE_RESEARCH_ANCHOR_NOT_FORMAL_START','ABC_Apr7_at_May14_Jun2_Jun3':'PRESENT_AS_ONE_START_PROPOSAL','ABC_May13_wick':'ENVELOPE_PRESENT_CLOSE_ONLY_BASELINE_ABSENT'},
   'known_endpoint_limitation':'April7-to-June3 observation proposal still exists and includes user-excluded June3. It must NOT become the approved39-row ABC interval; June2 candidate is separately retained.',
   'original_core_indicator_recomputations':0,'product_classifier':'NOT_IMPLEMENTED_OR_TESTED',
   'browser':'NOT_RUN','Android':'NOT_TESTED_NEW_BUILD','PDF_visual_QA':'NOT_YET_CREATED',
   'historical_signal_eligible':False,'primary_pressure_id':None}
(p/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'fixed_cases':len(saved),'all_prefix_equalities':prefix_checks,'independent_and_synthetic':'PASS','endpoint_limitation':'DEMONSTRATED_NOT_FIXED'}))
