"""Independent evidence invariants and cutoff/append tests; not a classifier test."""
from pathlib import Path
from decimal import Decimal as D
from copy import deepcopy
import argparse,json,gzip,hashlib
from branch_research import observe,canon,digest

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);s=json.loads(Path(a.source).read_text());t=json.loads(Path(a.comparison).read_text())
pools=json.loads((p/'candidate-pools.json').read_text());scopes=json.loads((p/'reviewed-scope-tests.json').read_text())
event_checks=0;branch_checks=0;observers=0
for group in pools.values():
    for result in group['results']:
        source=s if result['code']=='2884'else t
        rows=[b for b in source['bars']if result['start']<=b['date']<=result['data_cutoff']]
        assert len(rows)==result['source_records']and digest(rows)==result['bars_fingerprint']
        lookup={b['date']:i for i,b in enumerate(rows)}
        assert result['formal_end']is None and result['formal_membership']is None and result['selected_branch']is None
        event_lookup={e['event_id']:e for e in result['events']}
        for event in result['events']:
            index=lookup[event['known_on_saved_bar']];bar=rows[index];kind=event['kind']
            if kind=='FIRST_CLOSE_OUTSIDE_OBSERVED_FRAME':
                frame=event['pending'];old=[b for b in rows if b['date']<=frame['frame_observed_end']]
                assert len(old)==frame['frame_records']and digest(old)==frame['frame_bars_fingerprint']
                assert min(D(b['low'])for b in old)==D(frame['lower'])and max(D(b['high'])for b in old)==D(frame['upper'])
                assert (D(bar['close'])<D(frame['lower']))if frame['direction']=='DOWN'else(D(bar['close'])>D(frame['upper']))
            elif kind=='WHOLE_BAR_OUTSIDE_FROZEN_FRAME':
                frame=event['frozen_frame']
                assert frame['frame_observed_end']<frame['departure_date']<bar['date']
                assert (D(bar['high'])<D(frame['lower']))if frame['direction']=='DOWN'else(D(bar['low'])>D(frame['upper']))
            elif kind=='RETURNED_INSIDE_FROZEN_FRAME':
                frame=event['previous_departure'];assert D(frame['lower'])<=D(bar['close'])<=D(frame['upper'])
            elif kind=='OPPOSITE_CLOSE_BEFORE_WHOLE_BAR_EVENT':
                old=event['previous_departure'];assert (D(bar['close'])>D(old['upper']))if old['direction']=='DOWN'else(D(bar['close'])<D(old['lower']))
            else:raise AssertionError(kind)
            assert event['known_on_saved_bar']<=result['data_cutoff'];event_checks+=1
        for branch in result['branch_proposals']:
            ev=event_lookup[branch['evidence_event_id']];idx=lookup[branch['known_on_saved_bar']]
            assert ev['kind']=='WHOLE_BAR_OUTSIDE_FROZEN_FRAME'
            assert branch['stop_alternative']['proposed_observation_end']==rows[idx-1]['date']
            assert branch['stop_alternative']['records']==idx
            assert branch['following_seed_alternative']['proposed_start']==rows[idx]['date']
            assert branch['continue_alternative']['records']==idx+1
            assert branch['selected_alternative']is None and branch['stop_alternative']['formal_end']is None
            assert branch['following_seed_alternative']['formal_lineage']is None
            branch_checks+=1
        observers+=1

seen=set();prefix_checks=0
for name,full in scopes.items():
    src=s if full['code']=='2884'else t
    rows=[b for b in src['bars']if full['start']<=b['date']<=full['data_cutoff']]
    assert full==observe(src,full['start'],full['data_cutoff'])
    poisoned=deepcopy(src)
    for bar in poisoned['bars']:
        if bar['date']>full['data_cutoff']:
            for f in ['open','high','low','close']:bar[f]='99999999'
    poisoned['source_gaps']['known_calendar_missing_dates'].append('2222-01-01')
    assert observe(poisoned,full['start'],full['data_cutoff'])==full
    transformed=deepcopy(src)
    for b in transformed['bars']:
        for f in ['open','high','low','close']:b[f]=str(D(b[f])*10+7)
    tx=observe(transformed,full['start'],full['data_cutoff'])
    assert [(e['kind'],e['known_on_saved_bar'])for e in tx['events']]==[(e['kind'],e['known_on_saved_bar'])for e in full['events']]
    for bar in rows:
        cut=bar['date'];key=(full['code'],full['start'],cut)
        if key in seen:continue
        seen.add(key)
        old=observe(src,full['start'],cut)
        truncated={**src,'bars':[b for b in src['bars']if b['date']<=cut]}
        assert old==observe(truncated,full['start'],cut)
        assert old['events']==[e for e in full['events']if e['known_on_saved_bar']<=cut]
        assert old['branch_proposals']==[b for b in full['branch_proposals']if b['known_on_saved_bar']<=cut]
        prefix_checks+=1

abc=scopes['ABC-next-record'];stop=abc['branch_proposals'][0]
assert stop['stop_alternative']['proposed_observation_end']=='2025-06-02'and stop['following_seed_alternative']['proposed_start']=='2025-06-03'
assert stop['stop_alternative']['records']==39 and stop['continue_alternative']['records']==40
assert not scopes['ABC-reviewed-39']['branch_proposals']
assert not scopes['2884-reviewed-cutoff']['branch_proposals']
assert any(e['kind']=='RETURNED_INSIDE_FROZEN_FRAME'and e['known_on_saved_bar']=='2026-10-01'for e in scopes['2884-reviewed-cutoff']['events'])
assert scopes['G2-manual-scope-test']['branch_proposals'][0]['stop_alternative']['proposed_observation_end']=='2023-02-20'
assert all(b['selected_alternative']is None for b in scopes['G2-manual-scope-test']['branch_proposals'])

def synthetic(bars):return {'code':'SYNTHETIC','bars':[{'date':f'2000-01-{i+1:02d}',**{k:str(v)for k,v in zip(['open','high','low','close'],vals)},'volume_shares_scaled':'1'}for i,vals in enumerate(bars)],'source_gaps':{'known_calendar_missing_dates':[]}}
# A new low with an inside close produces no departure. Equality is not outside.
q=synthetic([(10,11,9,10),(10,11,8,10)])
assert not observe(q,'2000-01-01','2000-01-02')['events']
q=synthetic([(10,11,9,10),(9,10,7,8),(8,9,6,7),(9,10,8,9)])
z=observe(q,'2000-01-01','2000-01-04');assert not z['branch_proposals']
assert [e['kind']for e in z['events']]==['FIRST_CLOSE_OUTSIDE_OBSERVED_FRAME','RETURNED_INSIDE_FROZEN_FRAME']
q=synthetic([(10,11,9,10),(9,10,7,8),(11,13,10,12),(13,14,12,13)])
z=observe(q,'2000-01-01','2000-01-04');assert [e['kind']for e in z['events']]==['FIRST_CLOSE_OUTSIDE_OBSERVED_FRAME','OPPOSITE_CLOSE_BEFORE_WHOLE_BAR_EVENT','WHOLE_BAR_OUTSIDE_FROZEN_FRAME']
assert z['branch_proposals'][0]['following_seed_alternative']['proposed_start']=='2000-01-04'

raw=(p/'candidate-pools.json').read_bytes();packed=gzip.compress(raw,mtime=0);(p/'candidate-pools.json.gz').write_bytes(packed);assert gzip.decompress(packed)==raw
v={'schema':'m1-observation-branch-research-verification/1','research_driver_runs':1,'verification_script_runs':1,
   'pool_cases':len(pools),'observers_checked':observers,'event_geometry_checks':event_checks,'branch_consistency_checks':branch_checks,
   'unique_scope_prefix_checks':prefix_checks,'append_history_event_and_branch_ids_stable':'PASS',
   'six_scope_future_poison_and_positive_affine_transform':'PASS','synthetic_new_low_equality_return_and_opposite_direction':'PASS',
   'ABC39_stop_alternative_and_Jun3_seed':'PASS_FINITE_REVIEWED_SCOPE_NOT_GLOBAL_CLASSIFICATION',
   'G2_earlier_stop_alternatives':'DEMONSTRATED_SCOPE_CONFLICT_IF_FORCED_UNIVERSAL_STOP; source limitations retained',
   'source_SHA256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'comparison_SHA256':hashlib.sha256(Path(a.comparison).read_bytes()).hexdigest(),
   'raw_pool_SHA256':hashlib.sha256(raw).hexdigest(),'gzip_roundtrip':'PASS','gzip_bytes':len(packed),
   'formal_branch_selection':'NOT_ESTABLISHED','original_core_indicator_recomputations':0,
   'product_classifier':'NOT_IMPLEMENTED_OR_TESTED','browser':'NOT_RUN','Android':'NOT_TESTED_NEW_BUILD',
   'PDF_visual_QA':'NOT_YET_CREATED','historical_signal_eligible':False,'primary_pressure_id':None}
(p/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'observers':observers,'events':event_checks,'branches':branch_checks,'prefixes':prefix_checks,'gzip_bytes':len(packed),'result':'PASS_RESEARCH_ONLY'}))
