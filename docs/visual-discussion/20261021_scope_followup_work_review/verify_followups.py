"""Independent source arithmetic and causal checks for new follow-up research only."""
from pathlib import Path
from decimal import Decimal as D
from copy import deepcopy
from collections import Counter
import argparse,json,gzip,hashlib
from followup_research import track,digest

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--prior-dir',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);prior=Path(a.prior_dir)
s=json.loads(Path(a.source).read_text());t=json.loads(Path(a.comparison).read_text())
pools=json.loads(gzip.decompress((prior/'candidate-pools.json.gz').read_bytes()));scopes=json.loads((prior/'reviewed-scope-tests.json').read_text())
grouped=json.loads((p/'boundary-families.json').read_text());summaries=json.loads((p/'pool-followup-summaries.json').read_text());selected=json.loads((p/'selected-followups.json').read_text())
prior_hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in [prior/'candidate-pools.json.gz',prior/'reviewed-scope-tests.json',prior/'branch_research.py']}
monitor_count=fact_count=family_count=origin_count=0
events={e['event_id']:e for r in scopes.values()for e in r['events']if e['kind']=='WHOLE_BAR_OUTSIDE_FROZEN_FRAME'}
for name,pool in pools.items():
    src=s if name.startswith('2884')else t;expected=Counter();seen_members=[]
    for r in pool['results']:
        for e in r['events']:
            if e['kind']!='WHOLE_BAR_OUTSIDE_FROZEN_FRAME':continue
            events[e['event_id']]=e;f=e['frozen_frame'];direction=e['direction'];bound=D(f['upper']if direction=='UP'else f['lower'])
            expected[(e['known_on_saved_bar'],direction,str(bound.normalize()))]+=1
            q=track(src,e,pool['cutoff']);monitor_count+=1
            saved=next(x for x in summaries[name]if x['event_id']==e['event_id'])
            assert saved['monitor_id']==q['monitor_id']and saved['first_later_close_inside_frozen_frame']==q['first_later_close_inside_frozen_frame']
            rows=[b for b in src['bars']if q['event_known_on']<=b['date']<=q['observed_through']]
            assert len(rows)==len(q['facts'])
            lower,upper=D(f['lower']),D(f['upper'])
            for b,fact in zip(rows,q['facts']):
                assert fact['bar']==b
                c,l,h=map(D,[b['close'],b['low'],b['high']])
                assert fact['close_relation']==('INSIDE_FROZEN_FRAME'if lower<=c<=upper else'DEPARTURE_SIDE'if(c>upper if direction=='UP'else c<lower)else'OPPOSITE_SIDE')
                assert fact['whole_bar_on_departure_side']==(l>upper if direction=='UP'else h<lower)
                assert fact['crossed_boundary_contact']==(l<=bound<=h);fact_count+=1
            later=rows[1:]
            first=lambda pred:next((b['date']for b in later if pred(b)),None)
            assert q['first_later_boundary_contact']==first(lambda b:D(b['low'])<=bound<=D(b['high']))
            assert q['first_later_close_inside_frozen_frame']==first(lambda b:lower<=D(b['close'])<=upper)
            assert q['first_later_close_on_opposite_side']==first(lambda b:D(b['close'])<lower if direction=='UP'else D(b['close'])>upper)
            # Different close-run compression implementation checks all turn evidence.
            runs=[]
            for b in rows:
                if runs and D(runs[-1][-1]['close'])==D(b['close']):runs[-1].append(b)
                else:runs.append([b])
            turns=[]
            for prev,cur,nxt in zip(runs,runs[1:],runs[2:]):
                cp,cc,cn=map(lambda run:D(run[0]['close']),[prev,cur,nxt])
                if(cp<cc>cn)or(cp>cc<cn):turns.append(('HIGH'if cp<cc else'LOW',cur[0]['date'],cur[-1]['date'],nxt[0]['date']))
            assert turns==[(x['kind'],x['plateau_start'],x['plateau_end'],x['known_on_saved_bar'])for x in q['seed_evidence']['new_completed_close_turns']]
            assert q['selected_alternative']is None and q['formal_end']is None and q['seed_evidence']['formed_interval']is None
    actual=Counter()
    for g in grouped[name]:
        family_count+=1;key=(g['event_day'],g['direction'],g['crossed_boundary']);actual[key]+=g['member_count']
        assert g['member_count']==len(g['members'])and g['independent_vote_count']is None and g['formal_same_structure']is None
        for m in g['members']:
            seen_members.append(m['event_id']);boundary=D(g['crossed_boundary']);up=g['direction']=='UP'
            origins=[b['date']for b in src['bars']if m['start']<=b['date']<=m['frame_end']and D(b['high']if up else b['low'])==boundary]
            assert origins==m['boundary_origin_dates'];origin_count+=1
    assert expected==actual and len(seen_members)==len(set(seen_members))

prefixes=set();checks=0
for q in selected.values():
    src=s if q['code']=='2884'else t;e=events[q['event_id']]
    assert track(src,e,q['requested_cutoff'])==q
    for b in q['facts']:
        cut=b['known_on_saved_bar'];key=(q['event_id'],cut)
        if key in prefixes:continue
        prefixes.add(key);old=track(src,e,cut)
        trunc={**src,'bars':[b for b in src['bars']if b['date']<=cut]}
        assert track(trunc,e,cut)==old
        assert old['facts']==[x for x in q['facts']if x['known_on_saved_bar']<=cut]
        assert old['seed_evidence']['new_completed_close_turns']==[x for x in q['seed_evidence']['new_completed_close_turns']if x['known_on_saved_bar']<=cut]
        checks+=1
    poison=deepcopy(src)
    for b in poison['bars']:
        if b['date']>q['requested_cutoff']:
            for field in ['open','high','low','close']:b[field]='999999999'
    poison['source_gaps']['known_calendar_missing_dates'].append('2222-01-01')
    assert track(poison,e,q['requested_cutoff'])==q
    affine=deepcopy(src);ae=deepcopy(e)
    for b in affine['bars']:
        for field in ['open','high','low','close']:b[field]=str(D(b[field])*10+7)
    ae['current_bar']=next(b for b in affine['bars']if b['date']==e['known_on_saved_bar'])
    for field in ['lower','upper']:ae['frozen_frame'][field]=str(D(ae['frozen_frame'][field])*10+7)
    ae['frozen_frame']['frame_bars_fingerprint']=digest([b for b in affine['bars']if ae['frozen_frame']['frame_start']<=b['date']<=ae['frozen_frame']['frame_observed_end']])
    aq=track(affine,ae,q['requested_cutoff'])
    assert [(f['known_on_saved_bar'],f['whole_bar_on_departure_side'],f['crossed_boundary_contact'],f['close_relation'])for f in aq['facts']]==[(f['known_on_saved_bar'],f['whole_bar_on_departure_side'],f['crossed_boundary_contact'],f['close_relation'])for f in q['facts']]
    assert [(x['kind'],x['known_on_saved_bar'])for x in aq['seed_evidence']['new_completed_close_turns']]==[(x['kind'],x['known_on_saved_bar'])for x in q['seed_evidence']['new_completed_close_turns']]

assert selected['G2-boundary-touch']['first_later_boundary_contact']=='2023-02-22'
assert selected['G2-boundary-touch']['first_later_close_inside_frozen_frame']is None
assert selected['G2-return']['first_later_close_inside_frozen_frame']=='2023-03-01'
assert selected['ABC-through-Jun13']['first_later_close_inside_frozen_frame']is None
assert all(f['whole_bar_on_departure_side']for f in selected['ABC-through-Jun13']['facts'])
assert selected['ABC-through-Jun13']['seed_evidence']['both_high_and_low_turns_available_on']=='2025-06-11'
assert selected['G2-through-Mar3']['seed_evidence']['both_high_and_low_turns_available_on']=='2023-02-24'
assert selected['2884-last-source-bar']['seed_evidence']['saved_records']==1

# Synthetic safeguards: equality counts as contact/inside; opposite closes differ
# from inside returns; later contact/return remains after a prior whole-bar event.
base=deepcopy(selected['G2-first-bar']);event=deepcopy(events[base['event_id']]);source=deepcopy(t)
extra=deepcopy(event['current_bar']);extra.update(date='2023-02-22',open='37.85',high='37.85',low='37.85',close='37.85')
source['bars']=[b for b in source['bars']if b['date']<'2023-02-22']+[extra]
q=track(source,event,'2023-02-22');assert q['first_later_close_inside_frozen_frame']=='2023-02-22'and q['first_later_boundary_contact']=='2023-02-22'
extra.update(open='34',high='34',low='34',close='34');q=track(source,event,'2023-02-22')
assert q['first_later_close_on_opposite_side']=='2023-02-22'and q['first_later_close_inside_frozen_frame']is None
source=deepcopy(t);source['source_gaps']['known_calendar_missing_dates'].append('2023-02-22')
q=track(source,event,'2023-03-03');assert len(q['facts'])==1 and q['source_qualification']['followup_truncated_at_gap']
try:track(t,event,'2023-02-20')
except ValueError:pass
else:raise AssertionError('future event accepted')
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in prior_hashes.items())
v={'schema':'m1-persistent-followup-verification/1','research_driver_runs':1,'verification_script_runs':1,
   'pool_monitor_observations_checked':monitor_count,'source_fact_geometry_checks':fact_count,'boundary_families_checked':family_count,
   'member_origin_checks':origin_count,'unique_selected_event_prefix_checks':checks,
   'eight_selected_cutoff_future_poison_and_affine_relation_checks':'PASS','append_keeps_fact_and_completed_turn_ids':'PASS',
   'synthetic_equality_opposite_gap_and_future_event_rejection':'PASS','prior_files_sha256_unchanged':prior_hashes,
   'classification':'NOT_VALIDATED','formal_endpoint_selection':'NOT_ESTABLISHED','Android':'NOT_TESTED_NEW_BUILD',
   'core_indicator_recomputations':0,'old_research_driver_runs':0,'original_product_tests':'NOT_RUN','PDF_visual_QA':'NOT_YET_CREATED'}
(p/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(v,ensure_ascii=False))
