"""Check finite Work hypotheses and their limits, not market classification accuracy."""
import copy,hashlib,json
from collections import Counter
from decimal import Decimal as D
from observation_topics import ROOT,assess,window,write,prior

sources,c=prior.load_inputs();qs=json.loads((ROOT/'queries.json').read_text())['queries'];snap=json.loads((ROOT/'reading-proposals.json').read_text())
checks=Counter();qm={q['query_id']:q for q in qs};zm={z['zone_id']:z for z in c['zones']}
for key,r in snap.items():
    q=qm[r['query_id']];s=sources[r['code']];cut=r['cutoff']
    assert assess(s,q,cut,c)==r;checks['saved_view_reconstruction']+=1
    prefix=copy.deepcopy(s);prefix['bars']=[b for b in prefix['bars']if b['date']<=cut]
    assert assess(prefix,q,cut,c)==r;checks['source_prefix_truncation']+=1
    poison=copy.deepcopy(s)
    for b in poison['bars']:
        if b['date']>cut:
            b.update(open='88888',high='99999',low='-99999',close='77777',volume_shares_scaled='999999999')
    poison['manual_labels']={'all_structures_confirmed':True,'formal_parent':'forbidden'}
    assert assess(poison,q,cut,c)==r;checks['future_price_and_manual_label_poison']+=1
    p=r['reading_proposal']
    if p:
        born=p['first_reviewable_on_saved_bars'];assert born<=cut
        for label,win in [('birth',p['birth_reading_window']),('current',p['current_reading_window'])]:
            end=born if label=='birth'else cut;bars=[b for b in s['bars']if p['complete_evidence_start']<=b['date']<=end]
            assert win['saved_records']==len(bars)and win['observed_through']==bars[-1]['date']
            assert D(win['raw_reading_extent']['low'])==min(D(b['low'])for b in bars)
            assert D(win['raw_reading_extent']['high'])==max(D(b['high'])for b in bars)
            assert not win['continuity_certified']and win['formal_membership']is None and win['formal_price_bounds']is None
            checks['independent_reading_window_source_extents']+=1
        assert not p['formal_structure_established']
    for k in ['formal_start','formal_end','formal_membership','formal_parent','formal_merge','selected_role','primary_pressure_id','historical_selection_time','original_core_snapshot_2026_10_07']:
        assert r[k]is None
    assert not r['historical_signal_eligible']and r['classification']=='NOT_VALIDATED'and r['Android']=='NOT_TESTED_NEW_BUILD'
    checks['formal_and_product_unknowns_preserved']+=1

def view(q,cut):return snap[q+'@'+cut]
def expect(q,cut,response,has_proposal):
    v=view(q,cut);assert v['research_response']==response and bool(v['reading_proposal'])==has_proposal
    checks['specified_counterexample_views']+=1;return v
expect('ABC-fresh-lower','2025-05-23','WAIT_FOR_COMPLETED_LATER_ACTIVITY',False)
a=expect('ABC-fresh-lower','2025-05-26','PROPOSE_CROSS_PRICE_ACTIVITY_READING',True)
assert a['reading_proposal']['birth_reading_window']['saved_records']==34
expect('ABC-outside','2025-06-03','TRACK_DEPARTURE_NO_COMPLETED_FOLLOWUP_TOPIC_YET',False)
expect('ABC-outside','2025-06-11','TRACK_DEPARTURE_NO_COMPLETED_FOLLOWUP_TOPIC_YET',False)
b=expect('ABC-outside','2025-06-12','PROPOSE_OLD_FRAME_AND_LATER_OUTSIDE_ACTIVITY_READING',True)
assert b['reading_proposal']['birth_reading_window']['saved_records']==47
assert b['current_episode']['start']=='2025-06-02'and b['current_episode']['ended_on']is None
expect('G2-outside-return','2023-04-26','TRACK_DEPARTURE_NO_COMPLETED_FOLLOWUP_TOPIC_YET',False)
g=expect('G2-outside-return','2023-04-27','PROPOSE_OLD_FRAME_AND_LATER_OUTSIDE_ACTIVITY_READING',True)
gr=expect('G2-outside-return','2023-05-12','PROPOSE_OLD_FRAME_AND_LATER_OUTSIDE_ACTIVITY_READING',True)
assert g['current_episode']['start']=='2023-04-21'and g['current_episode']['ended_on']is None
assert gr['current_episode']['ended_on']=='2023-05-12'and gr['current_episode']['end_reason']=='CLOSE_RETURN_INSIDE'
assert gr['evidence_facts']['current_close_vs_fixed_frame']=='INSIDE'
expect('G2-fresh-overlap','2023-02-10','SUPPLEMENT_REVISIT_EVIDENCE_NO_NEW_BROADER_TOPIC_FROM_THIS_PAIR',False)
n=expect('G2-geometric-only','2023-03-27','KEEP_GEOMETRIC_OVERLAP_AND_CONFIRMATION_DAY_ENTRY_SEPARATE',False)
assert not n['evidence_facts']['actual_later_path_close_visits_older_core']and n['evidence_facts']['confirmation_bar_close']=='36.65'and n['evidence_facts']['confirmation_bar_close_vs_older_common']=='INSIDE'
expect('B-shared-path','2026-04-28','SUPPLEMENT_EXISTING_ACTIVITY_WITH_REUSED_EVIDENCE',False)
expect('A-reused-context','2026-10-12','SUPPLEMENT_EXISTING_ACTIVITY_WITH_REUSED_EVIDENCE',False)
expect('A-latest-departure','2026-10-15','WAIT_FOR_SAVED_DEPARTURE_EVENT',False)
expect('A-latest-departure','2026-10-16','TRACK_DEPARTURE_NO_COMPLETED_FOLLOWUP_TOPIC_YET',False)

for name,first,last in [('ABC-fresh-lower','2025-05-26','2025-06-02'),('ABC-outside','2025-06-12','2025-06-13'),('G2-outside-return','2023-04-27','2023-05-12')]:
    p1=view(name,first)['reading_proposal'];p2=view(name,last)['reading_proposal']
    assert {k:v for k,v in p1.items()if k!='current_reading_window'}=={k:v for k,v in p2.items()if k!='current_reading_window'}
    checks['append_preserves_proposal_birth']+=1
    assert p1['current_reading_window']['saved_records']<p2['current_reading_window']['saved_records']

# No future zone or event geometry is exposed when its completion is unavailable.
for name,cut in [('ABC-fresh-lower','2025-05-23'),('ABC-outside','2025-06-11'),('A-latest-departure','2026-10-15')]:
    cc=copy.deepcopy(c);q=qm[name]
    for z in cc['zones']:
        if z['known_on_saved_bar']>cut:z.update(common_close_low='-999',common_close_high='999',raw_path_frame={'bad_future':'must not be exposed'})
    for e in cc['events']:
        if e['known_on_saved_bar']>cut:e['frozen_frame']={'bad_future':'must not be exposed'}
    assert assess(sources[q['code']],q,cut,cc)==view(name,cut)
    checks['unavailable_zone_and_event_geometry_poison']+=1

# The geometry alone cannot fix formal hierarchy; manual 39/136 remain separate audits.
for name,start,end,expected in [('ABC','2025-04-07','2025-06-02',39),('G2','2023-01-16','2023-08-16',136)]:
    assert len([b for b in sources['1101']['bars']if start<=b['date']<=end])==expected
    checks['retrospective_manual_count_separate']+=1
for p,meta in json.loads((ROOT/'source-provenance.json').read_text())['files'].items():
    from pathlib import Path
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==meta['sha256'];checks['unchanged_input_sha256']+=1
write(ROOT/'verification.json',{'status':'PASS_SCOPED_HYPOTHESIS_AND_CUTOFF_CHECKS','checks':dict(checks),
    'new_verifier_runs':1,'research_driver_runs':1,'prior_drivers_or_product_tests_rerun':0,
    'not_validated':['formal larger structure','main role or parent merge','universal proposal sufficiency','classifier accuracy','historical selection','Android new build','capital growth flywheel effectiveness']})
print(json.dumps({'status':'PASS','checks':dict(checks)}))
