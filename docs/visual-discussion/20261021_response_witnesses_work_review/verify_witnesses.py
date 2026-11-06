"""Check scoped path facts, cutoff isolation, frozen witnesses and counterexamples."""
import copy,hashlib,json
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from response_witnesses import ROOT,prior,assess,write

sources,c=prior.load_inputs();qs=json.loads((ROOT/'queries.json').read_text());qm={q['query_id']:q for q in qs};snap=json.loads((ROOT/'response-witnesses.json').read_text());checks=Counter()
for key,r in snap.items():
    q=qm[r['query_id']];source=sources[q['code']];cut=r['cutoff'];assert assess(source,q,cut,c)==r;checks['saved_cutoff_view_reconstruction']+=1
    prefix=copy.deepcopy(source);prefix['bars']=[b for b in prefix['bars']if b['date']<=cut]
    assert assess(prefix,q,cut,c)==r;checks['source_prefix_truncation']+=1
    poison=copy.deepcopy(source);poison['manual_labels']={'all_support_confirmed':True,'primary':'forbidden'}
    for b in poison['bars']:
        if b['date']>cut:b.update(open='-8888',high='9999',low='-9999',close='7777',volume_shares_scaled='999999999')
    assert assess(poison,q,cut,c)==r;checks['future_price_volume_and_manual_label_poison']+=1
    cc=copy.deepcopy(c)
    for p in cc['pivots']:
        if p['known_on']>cut:p.update(price='9999',occurred_at='1900-01-01')
    assert assess(source,q,cut,cc)==r;checks['unavailable_reference_value_poison']+=1
    if r['birth']:
        a=r['anchor_source_bar'];birth=r['birth'];idx=next(i for i,b in enumerate(source['bars'])if b['date']==a['date'])
        assert birth['previous_saved_bar']==source['bars'][idx-1]and birth['frozen_contact_bar_range']==[a['low'],a['high']]
        assert r['reference']['known_on']<a['date']and D(a['low'])<=D(r['reference']['price'])<=D(a['high'])
        gap=next((d for d in source['source_gaps']['known_calendar_missing_dates']if a['date']<d<=cut),None)
        later=[b for b in source['bars']if a['date']<b['date']<=cut and(gap is None or b['date']<gap)]
        expected=next((b for b in later if D(b['close'])>D(a['high'])or D(b['close'])<D(a['low'])),None)
        assert r['followup']['first_later_close_outside_contact_bar']==expected;checks['independent_frozen_bar_and_first_close_witness']+=1
        for label,field,op in [('first_later_high_above_contact_high','high',lambda x,y:x>y),('first_later_low_below_contact_low','low',lambda x,y:x<y)]:
            assert r['followup'][label]==next((b for b in later if op(D(b[field]),D(a[field]))),None);checks['independent_wick_witnesses']+=1
        streak=r['current_range_intersection_streak'];bs=[a]
        for b in source['bars'][idx+1:]:
            if b['date']>cut or any(bs[-1]['date']<d<=b['date']for d in source['source_gaps']['known_calendar_missing_dates']):break
            if not D(b['low'])<=D(r['reference']['price'])<=D(b['high']):break
            bs.append(b)
        assert streak['last_intersection']==bs[-1]['date']and streak['consecutive_saved_records']==len(bs)and streak['independent_test_count']is None
        checks['consecutive_saved_intersection_streak_not_independent_tests']+=1
        pairs=[(a,birth['previous_saved_bar'],birth['anchor_volume_vs_previous_saved_bar'])]
        if expected:pairs.append((expected,a,r['followup']['witness_volume_vs_anchor']))
        for x,y,v in pairs:
            num,den=int(x['volume_shares_scaled']),int(y['volume_shares_scaled'])
            assert v['numerator']==str(num)and v['denominator']==str(den)and v['ratio_exact']==(str(num)+'/'+str(den)if den else None)
            assert v['comparison']==('HIGHER'if num>den else'LOWER'if num<den else'EQUAL');checks['exact_volume_descriptions_no_signal_threshold']+=1
        assert r['followup']['formal_reaction_confirmation']is None
    assert all(r[k]is None for k in ['support_or_pressure_response_demonstrated','volume_qualification','importance_score','formal_interval','formal_start','formal_end','formal_membership','formal_parent','formal_merge','selected_role','primary_pressure_id','historical_selection_time','original_core_snapshot_2026_10_07','numeric_frame_2026_10_07'])
    assert not r['historical_signal_eligible']and r['classifier']=='NOT_VALIDATED'and r['Android']=='NOT_TESTED_NEW_BUILD';checks['formal_product_and_action_unknowns']+=1
def v(name,cut):return snap[name+'@'+cut]
up=v('G2-low-later-up','2023-04-11');down=v('G2-low-later-down','2023-07-10')
assert up['birth']['previous_close_side']==down['birth']['previous_close_side']=='ABOVE'
assert up['birth']['anchor_close_side']==down['birth']['anchor_close_side']=='ABOVE'
assert up['followup']['first_later_close_outside_contact_bar']['date']=='2023-04-11'and up['followup']['status']=='LATER_CLOSE_ABOVE_CONTACT_BAR'
assert down['followup']['first_later_close_outside_contact_bar']['date']=='2023-07-10'and down['followup']['status']=='LATER_CLOSE_BELOW_CONTACT_BAR'
assert up['followup']['witness_volume_vs_anchor']['comparison']==down['followup']['witness_volume_vs_anchor']['comparison']=='HIGHER';checks['same_contact_close_side_and_higher_volume_opposite_followup']+=1
assert up['current_range_intersection_streak']['consecutive_saved_records']==4 and down['current_range_intersection_streak']['consecutive_saved_records']==2
assert v('G2-low-later-up','2023-03-29')['followup']['first_later_low_below_contact_low']['low']=='36.05'
assert v('G2-low-later-up','2023-04-10')['followup']['first_later_close_outside_contact_bar']is None;checks['wick_cross_does_not_backfill_later_close_witness']+=1
eq=v('ABC-high-equality-then-down','2025-05-13');assert eq['birth']['anchor_close_side']=='EQUAL'
assert eq['followup']['first_later_high_above_contact_high']['high']=='31.40'and eq['followup']['first_later_close_outside_contact_bar']is None
assert v('ABC-high-equality-then-down','2025-05-14')['followup']['first_later_close_outside_contact_bar']['close']=='30.35';checks['ABC_equality_then_wick_then_down_close_distinct_dates']+=1
assert v('ABC-low-close-through','2025-06-02')['birth']['anchor_close_side']=='BELOW'
assert v('ABC-low-close-through','2025-06-03')['followup']['first_later_close_outside_contact_bar']['close']=='26.85'
assert v('A-gap-control','2026-10-15')['status']=='NO_DAILY_RANGE_INTERSECTION'and v('A-gap-control','2026-10-15')['birth']is None
assert v('G2-forming-source-control','2023-05-02')['reference']is None and v('G2-forming-source-control','2023-05-09')['birth']is None;checks['close_through_gap_and_forming_source_controls']+=1
for q in qs:
    born=[v(q['query_id'],cut)['birth']for cut in q['cutoffs']if v(q['query_id'],cut)['birth']]
    if born:assert all(b==born[0]for b in born);checks['fixed_birth_and_anchor_range_across_cutoffs']+=1
continued=copy.deepcopy(qm['G2-low-later-down']);continued['anchor_date']='2023-07-10'
try:assess(sources['1101'],continued,'2023-07-11',c)
except ValueError as e:assert 'intersection streak'in str(e);checks['continued_intersection_not_recounted_as_new_anchor']+=1
else:raise AssertionError('Repeated intersection was accepted as independent anchor')

# Both wick directions and equality do not settle the order or the close outcome.
source={'code':'SYNTH','bars':[{'date':'2026-01-0'+str(i+1),'open':o,'high':h,'low':lo,'close':cl,'volume_shares_scaled':str(vol)}for i,(o,h,lo,cl,vol)in enumerate([
    ('11.4','12','11.1','11.5',100),('10.5','11','9','10.5',0),('10','12','8','11',120),('11.1','11.4','10.8','11.2',90)])],
    'source_gaps':{'known_calendar_missing_dates':[]}}
p={'id':'synthetic','code':'SYNTH','kind':'LOW','price':'10','known_on':'2026-01-01'};cat={'pivots':[p]};q={'query_id':'synthetic','code':'SYNTH','reference_id':'synthetic','anchor_date':'2026-01-02'}
for reflected in [False,True]:
    s=copy.deepcopy(source);cc=copy.deepcopy(cat)
    if reflected:
        cc['pivots'][0]['kind']='HIGH'
        for b in s['bars']:
            old=b.copy();b.update(open=str(20-D(old['open'])),high=str(20-D(old['low'])),low=str(20-D(old['high'])),close=str(20-D(old['close'])))
    waiting=assess(s,q,'2026-01-03',cc);done=assess(s,q,'2026-01-04',cc)
    assert waiting['followup']['first_later_close_outside_contact_bar']is None
    assert waiting['followup']['first_later_high_above_contact_high']and waiting['followup']['first_later_low_below_contact_low']
    assert done['followup']['status']==('LATER_CLOSE_BELOW_CONTACT_BAR'if reflected else'LATER_CLOSE_ABOVE_CONTACT_BAR')
    assert done['followup']['witness_volume_vs_anchor']['ratio_exact']is None;checks['synthetic_equal_close_both_wicks_zero_volume_direction']+=1
    s['bars'].append({'date':'2026-01-05','open':'10.5','high':'10.8','low':'10.2','close':'10.5','volume_shares_scaled':'80'})
    returned=assess(s,q,'2026-01-05',cc)
    assert returned['birth']==done['birth']and returned['followup']['first_later_close_outside_contact_bar']==done['followup']['first_later_close_outside_contact_bar']
    assert returned['observed_path'][-1]['close_side_of_contact_range']=='INSIDE_OR_EQUAL';checks['synthetic_later_return_preserves_first_witness_updates_current_path']+=1
gapped=copy.deepcopy(source);gapped['bars']=[b for b in gapped['bars']if b['date']!='2026-01-03'];gapped['source_gaps']['known_calendar_missing_dates']=['2026-01-03']
gg=assess(gapped,q,'2026-01-04',cat);assert gg['followup']['status']=='LISTED_DATA_GAP_BEFORE_WITNESS'and gg['followup']['first_later_close_outside_contact_bar']is None;checks['synthetic_listed_gap_blocks_contiguous_witness']+=1
for path,meta in json.loads((ROOT/'source-provenance.json').read_text())['files'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==meta['sha256'];checks['unchanged_input_hashes']+=1
write(ROOT/'verification.json',{'status':'PASS_SCOPED_RESPONSE_WITNESS_RESEARCH','checks':dict(checks),'new_research_driver_runs':1,'new_verifier_runs':2,
    'prior_drivers_and_product_tests_rerun':0,'reaction_classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','support_or_pressure_response_demonstrated':None})
print(json.dumps({'status':'PASS','checks':dict(checks)}))
