"""Verify availability, open-ended evidence and non-veto of changed volume."""
import json,hashlib
from copy import deepcopy
from study_followup import ROOT,SOURCE,EXPECTED,CUTOFFS,END,observe,write
bs=json.loads(SOURCE.read_text())['bars'];checks=[];births={}
for cutoff in CUTOFFS:
    full=observe(bs,cutoff)
    assert full==observe([b for b in bs if b['date']<=cutoff],cutoff)
    poisoned=deepcopy(bs)
    for b in poisoned:
        if b['date']>cutoff:
            for k in ('open','high','low','close'):b[k]='999999.99'
            b['volume_shares_scaled']='999999999999999'
    assert full==observe(poisoned,cutoff)
    no_expansion=deepcopy(bs)
    for b in no_expansion:b['volume_shares_scaled']='1'
    assert full==observe(no_expansion,cutoff)
    for e in full['episodes']:
        birth=e['birth'];eid=birth['id']
        if eid in births:assert birth==births[eid]
        births[eid]=birth
        assert all(birth['query']['origin']<x['date']<=cutoff for x in e['daily_followup_facts'])
        assert e['summary']['formal_holding_confirmed'] is None and e['summary']['formal_success_or_failure'] is None
    checks.append({'cutoff':cutoff,'prefix':True,'future_price_volume_poison':True,'all_volume_replaced_with_1_price_evidence_unchanged':True,'available_origins':len(full['episodes'])})
final=observe(bs,END);m={e['birth']['query']['name']:e['summary']for e in final['episodes']}
a,b,c=[m[k]for k in ['lower_first','lower_reclaim','broader_first']]
assert (a['followup_saved_bars_excluding_origin'],a['close_above_count'],a['close_below_count'])==(17,16,1)
assert a['first_close_below_date']=='2026-06-08' and a['first_close_regain_after_first_below']=='2026-06-09'
assert a['low_below_close_above_dates']==['2026-06-05','2026-06-09','2026-06-10','2026-06-11']
assert a['trailing_consecutive_saved_closes_above']==15
assert (b['followup_saved_bars_excluding_origin'],b['close_above_count'],b['close_below_count'])==(14,14,0)
assert b['low_below_close_above_dates']==['2026-06-10','2026-06-11']
assert b['lowest_followup_close']=='33.65' and b['lowest_followup_low']=='33.05'
assert (c['followup_saved_bars_excluding_origin'],c['close_above_count'],c['close_below_count'])==(6,1,5)
assert c['first_close_below_date']=='2026-06-24' and c['first_close_regain_after_first_below'] is None
assert c['high_equal_close_below_dates']==['2026-06-24'] and c['high_above_close_below_dates']==['2026-06-25']
assert c['whole_bar_below_dates']==['2026-06-26','2026-06-29','2026-06-30']
assert c['trailing_consecutive_saved_closes_below']==5
assert len(observe(bs,'2026-06-08')['episodes'])==1 and len(observe(bs,'2026-06-09')['episodes'])==2 and len(observe(bs,'2026-06-22')['episodes'])==3
assert all(e['summary']['followup_saved_bars_excluding_origin']==0 for e in observe(bs,'2026-06-04')['episodes'])
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
write('verification.json',{'status':'PASS','verifier_runs':1,'cutoff_checks':checks,'episode_births_immutable':len(births),'specified_real_episode_oracles':3,'later_rows_exclude_origin':True,'unavailable_future_origins_not_exposed':True,'volume_not_a_price_evidence_veto':True,'same_reference_reclaim_not_new_independent_success':True,'no_holding_confirmation_from_count':True,'original_source_SHA_unchanged':True,'old_driver_verifier_product_tests_rerun':0})
print('PASS: 12 prefix/future-poison/non-veto cutoffs; 3 immutable existing origins and real episode oracles. No formal hold/success rule.')
