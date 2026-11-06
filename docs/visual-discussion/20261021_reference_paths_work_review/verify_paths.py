"""Independent price-position checks and counterexamples to inferred constraints."""
import copy,hashlib,json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from reference_paths import ROOT,prior,compose,audit,write

sources,c=prior.load_inputs();queries=json.loads((ROOT/'queries.json').read_text());saved=json.loads((ROOT/'reference-paths.json').read_text());checks=Counter()
pm={p['id']:p for p in c['pivots']};qm={q['group']:q for q in queries};zm={z['zone_id']:z for z in c['zones']}
for key,r in saved.items():
    q=qm[r['group']];source=sources[q['code']];cut=r['cutoff'];assert compose(source,q,cut,c)==r;checks['saved_cutoff_views']+=1
    prefix=copy.deepcopy(source);prefix['bars']=[b for b in prefix['bars']if b['date']<=cut]
    assert compose(prefix,q,cut,c)==r;checks['source_prefix_truncation']+=1
    poison=copy.deepcopy(source);poison['manual_structure_label']={'confirmed':True,'parent':'forbidden'}
    for b in poison['bars']:
        if b['date']>cut:b.update(open='-88888',high='99999',low='-99999',close='77777',volume_shares_scaled='999999999')
    assert compose(poison,q,cut,c)==r;checks['future_price_and_manual_label_poison']+=1
    cc=copy.deepcopy(c)
    for p in cc['pivots']:
        if p['known_on']>cut:p.update(price='99999',occurred_at='1900-01-01',source_dates=['2099-01-01'])
    assert compose(source,q,cut,cc)==r;checks['not_yet_available_reference_value_poison']+=1
    for ref in r['references']:
        p=pm[ref['reference_id']]
        if p['known_on']>cut:
            assert set(ref)=={'reference_id','reference_available'}and not ref['reference_available'];checks['unavailable_reference_masks']+=1;continue
        value=D(p['price']);bars=[b for b in source['bars']if p['known_on']<=b['date']<=cut];high=p['kind']=='HIGH'
        for field,predicate in [
            ('daily_price_range_contains_reference',lambda b:D(b['low'])<=value<=D(b['high'])),
            ('strict_extreme_excursion',lambda b:D(b['high'])>value if high else D(b['low'])<value),
            ('strict_close_beyond_original_extreme',lambda b:D(b['close'])>value if high else D(b['close'])<value),
            ('whole_bar_beyond_original_extreme',lambda b:D(b['low'])>value if high else D(b['high'])<value)]:
            expected=next((b for b in bars if predicate(b)),None);assert ref['first_saved_events_from_reference_availability'][field]==expected
            assert [f['bar']for f in ref['saved_bar_facts']if f[field]]==[b for b in bars if predicate(b)];checks['independent_full_trace_and_first_events']+=1
        for v in ref['local_activity_views']:
            z=zm[v['zone_id']];assert v['relationship_first_available_on']==max(z['known_on_saved_bar'],p['known_on'])<=cut
            left=min(c['turns'][tid]['left_evidence_date']for lid in z['leg_ids']for tid in [c['legs'][lid]['from_turn_id'],c['legs'][lid]['to_turn_id']])
            assert v['complete_source_strictly_after_reference_available']==(left>p['known_on'])
            for out,lo,hi in [('common_side',z['common_close_low'],z['common_close_high']),('raw_path_side',z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high'])]:
                expected='BELOW'if D(hi)<value else'ABOVE'if D(lo)>value else'CONTAINS_OR_EQUALS_REFERENCE';assert v[out]==expected
            checks['local_candidate_attachment_timing_and_price_sides']+=1
        assert ref['support_or_pressure_response_demonstrated']is None and ref['importance_score']is None and not ref['continuous_calendar_certified']
        checks['no_constraint_or_importance_inference']+=1
    assert all(r[k]is None for k in ['formal_interval','formal_start','formal_end','formal_membership','formal_parent','formal_merge','selected_role','primary_pressure_id','historical_selection_time','original_core_snapshot_2026_10_07','numeric_frame_2026_10_07'])
    assert not r['historical_signal_eligible']and r['classifier']=='NOT_VALIDATED'and r['Android']=='NOT_TESTED_NEW_BUILD';checks['formal_and_product_unknowns']+=1
def ref(group,cut,day):return next(r for r in saved[group+'@'+cut]['references']if r['reference_id']==next(p['id']for p in c['pivots']if p['code']==qm[group]['code']and p['scale']=='0.03'and p['occurred_at']==day))
a=ref('A','2026-10-15','2026-09-17');assert a['review_question']['known_on_saved_bar']=='2026-10-15'and not a['post_cross_completed_local_ids']
assert a['first_saved_events_from_reference_availability']['whole_bar_beyond_original_extreme']['date']=='2026-10-15'
assert not any(f['daily_price_range_contains_reference']for f in a['saved_bar_facts'])
event=next(e for e in c['events']if e['code']=='2884'and e['frozen_frame']['frame_start']=='2026-09-17'and e['frozen_frame']['upper']=='47.35')
assert event['known_on_saved_bar']=='2026-10-16'and event['departure_date']=='2026-10-15';checks['A_direct_reference_fact_vs_prior_later_bar_branch']+=1
b=ref('ABC','2025-06-02','2025-04-08');assert b['review_question']['known_on_saved_bar']=='2025-06-02'and not b['post_cross_completed_local_ids']
assert b['first_saved_events_from_reference_availability']['whole_bar_beyond_original_extreme']is None
assert ref('ABC','2025-06-03','2025-04-08')['first_saved_events_from_reference_availability']['whole_bar_beyond_original_extreme']['date']=='2025-06-03'
assert len([x for x in sources['1101']['bars']if '2025-04-07'<=x['date']<='2025-06-02'])==39;checks['ABC_close_then_whole_day_and_approved_manual39']+=1
for group,cut,day in [('ABC','2025-06-13','2025-03-12'),('ABC','2025-06-13','2025-05-13'),('G2','2023-08-16','2023-05-02')]:
    r=ref(group,cut,day);fresh=[v for v in r['local_activity_views']if v['complete_source_strictly_after_reference_available']]
    assert len(fresh)>1 and all(v['raw_path_side']=='BELOW'for v in fresh)
    assert not any(f['daily_price_range_contains_reference']or f['strict_close_beyond_original_extreme']for f in r['saved_bar_facts'])
    assert r['review_question']is None and r['support_or_pressure_response_demonstrated']is None;checks['multiple_same_side_activities_without_reference_range_contact']+=1
for group,cuts in [('A',['2026-10-15','2026-10-16']),('ABC',['2025-06-02','2025-06-03','2025-06-12','2025-06-13'])]:
    day='2026-09-17'if group=='A'else'2025-04-08';first=ref(group,cuts[0],day)['review_question']
    for cut in cuts[1:]:assert ref(group,cut,day)['review_question']==first;checks['review_question_birth_preserved_after_append']+=1

# Equality, wick-only excursion, a gap past the reference, and later return.
base={'code':'SYNTH','bars':[{'date':'2026-01-0'+str(i+1),'open':o,'high':h,'low':l,'close':cl,'volume_shares_scaled':'100'}for i,(o,h,l,cl)in enumerate([('9.5','10','9','10'),('9.5','11','9','9.5'),('12','12.5','11','12'),('9.5','9.8','9','9.2')])],'source_gaps':{'known_calendar_missing_dates':[]}}
p={'id':'synthetic-high','code':'SYNTH','kind':'HIGH','price':'10','known_on':'2026-01-01'};empty={'zones':[]}
for low in [False,True]:
    ss=copy.deepcopy(base);pp=copy.deepcopy(p)
    if low:
        pp.update(id='synthetic-low',kind='LOW')
        for x in ss['bars']:
            old=x.copy();x.update(open=str(20-D(old['open'])),high=str(20-D(old['low'])),low=str(20-D(old['high'])),close=str(20-D(old['close'])))
    r1=audit(ss,pp,'2026-01-01','2026-01-01',empty);r2=audit(ss,pp,'2026-01-01','2026-01-02',empty);r3=audit(ss,pp,'2026-01-01','2026-01-03',empty);r4=audit(ss,pp,'2026-01-01','2026-01-04',empty)
    assert r1['review_question']is None and r2['review_question']is None
    assert r2['first_saved_events_from_reference_availability']['strict_extreme_excursion']['date']=='2026-01-02'
    assert r3['review_question']['known_on_saved_bar']=='2026-01-03'and r3['review_question']==r4['review_question']
    assert not r3['saved_bar_facts'][-1]['daily_price_range_contains_reference']and r3['saved_bar_facts'][-1]['whole_bar_beyond_original_extreme']
    assert r4['current_close_side']==('ABOVE'if low else'BELOW');checks['synthetic_equality_wick_gap_cross_return_direction']+=1
reuse=[]
for group,cut,day,expected in [('A','2026-10-16','2026-10-01',5),('G2','2023-08-16','2023-05-02',9)]:
    r=ref(group,cut,day);p=r['reference'];items=[v for v in r['local_activity_views']if v['raw_path_side']=='CONTAINS_OR_EQUALS_REFERENCE']
    assert len(items)==expected and not any(f['daily_price_range_contains_reference']for f in r['saved_bar_facts'])
    for v in items:
        origins=zm[v['zone_id']]['raw_path_frame']['low_origin_dates'if p['kind']=='LOW'else'high_origin_dates']
        assert origins==[p['occurred_at']]and not v['complete_source_strictly_after_reference_available']
    reuse.append({'group':group,'reference':p,'raw_path_views_containing_reference':[v['zone_id']for v in items],
        'all_extreme_origin_dates':[p['occurred_at']],'post_availability_daily_range_contains_count':0,
        'interpretation':'Repeated candidate windows reuse the same forming extreme; not repeated subsequent tests.'})
    checks['forming_extreme_reuse_not_post_availability_tests']+=1
write(ROOT/'formation-point-reuse-audit.json',reuse)
for path,meta in json.loads((ROOT/'source-provenance.json').read_text())['files'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==meta['sha256'];checks['unchanged_input_hashes']+=1
write(ROOT/'verification.json',{'status':'PASS_SCOPED_REFERENCE_PATH_RESEARCH','checks':dict(checks),'new_driver_runs':1,'new_verifier_runs':2,
    'prior_drivers_or_product_tests_rerun':0,'constraint_inference':'NOT_ESTABLISHED','classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD'})
print(json.dumps({'status':'PASS','checks':dict(checks)}))
