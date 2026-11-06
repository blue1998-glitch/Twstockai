"""Meaningful prefix/current-volume checks; no old product or classifier test runs."""
from copy import deepcopy
from fractions import Fraction
import json,hashlib
from study import SOURCE,ROOT,EXPECTED,CUTOFFS,END,view,dump

s=json.loads(SOURCE.read_text());bs=s['bars'];checks=[]
for d in CUTOFFS:
    original=view(bs,d)
    assert original==view([b for b in bs if b['date']<=d],d)
    poisoned=deepcopy(bs)
    for b in poisoned:
        if b['date']>d:
            for key in ('open','high','low','close'):b[key]='999999.99'
            b['volume_shares_scaled']='999999999999999'
    assert original==view(poisoned,d)
    checks.append({'cutoff':d,'prefix_equality':True,'future_price_volume_poison_unchanged':True})
v=view(bs,END);events={e['date']:e for e in v['events']}
expected={'2026-06-03':('BELOW','BELOW',None,None),'2026-06-04':('ABOVE','BELOW','UP',None),'2026-06-08':('BELOW','BELOW','DOWN',None),'2026-06-09':('ABOVE','BELOW','UP',None),'2026-06-17':('ABOVE','EQUAL',None,None),'2026-06-18':('ABOVE','BELOW',None,None),'2026-06-22':('ABOVE','ABOVE',None,'UP'),'2026-06-24':('ABOVE','BELOW',None,'DOWN'),'2026-06-30':('ABOVE','BELOW',None,None)}
for d,t in expected.items():
    e=events[d]['references'];small=e['lower_activity_high'];large=e['broader_high']
    assert (small['close_relation'],large['close_relation'],small['saved_close_cross'],large['saved_close_cross'])==t
for d in ['2026-06-04','2026-06-22','2026-06-24']:
    changed=deepcopy(bs);b=next(b for b in changed if b['date']==d);b['volume_shares_scaled']=str(int(b['volume_shares_scaled'])*2)
    e=view(changed,d)['events'][-1];old=events[d]
    for key in ['prior20_mean_shares','prior20_start','prior20_end','frozen_source_median_shares']:assert e['volume'][key]==old['volume'][key]
    def f(x):return Fraction(x['numerator'],x['denominator'])
    for key in ['vs_prior20_mean','vs_frozen_source_median','vs_previous_saved_day']:assert f(e['volume'][key])==2*f(old['volume'][key])
    assert e['volume']['volume_qualification'] is None
assert v['frozen_volume_comparison']['median_shares']['numerator']==35679356
assert v['frozen_volume_comparison']['saved_rows']==52
assert not view(bs,'2026-05-28')['frozen_volume_comparison']['available_in_saved_prefix']
assert view(bs,'2026-05-28')['frozen_volume_comparison']['median_shares'] is None
assert events['2026-06-04']['volume']['vs_previous_saved_day']['numerator']<events['2026-06-04']['volume']['vs_previous_saved_day']['denominator']
assert events['2026-06-04']['volume']['vs_frozen_source_median']['numerator']>events['2026-06-04']['volume']['vs_frozen_source_median']['denominator']
assert events['2026-06-05']['volume']['vs_frozen_source_median']['numerator']>events['2026-06-05']['volume']['vs_frozen_source_median']['denominator']
assert events['2026-06-05']['volume']['vs_prior20_mean']['numerator']<events['2026-06-05']['volume']['vs_prior20_mean']['denominator']
assert all(e['references']['lower_activity_high']['close_relation']=='ABOVE' for d,e in events.items() if d>='2026-06-09')
assert all(e['volume']['volume_qualification'] is None for e in events.values())
assert events['2026-06-18']['references']['broader_high']['departure_from_equal_close']=='DOWN'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
prior_runs=json.loads((ROOT/'verification.json').read_text())['verifier_runs'] if (ROOT/'verification.json').exists() else 0
dump('verification.json',{'status':'PASS','verifier_runs':prior_runs+1,'cutoff_checks':checks,'exact_price_path_cases':len(expected),'current_volume_exclusion_and_ratio_scale_cases':3,'source_median':'35679356 shares / 52 saved rows','incomplete_source_median_unavailable':True,'volume_baseline_disagreement_preserved':True,'Jun9_onward_all_closes_above_lower_reference':True,'departure_from_equal_not_counted_as_opposite_side_cross':True,'formal_volume_qualification_still_null':True,'source_sha_unchanged':True,'old_driver_verifier_product_tests_rerun':0})
print('PASS: 10 prefix/poison cutoffs, 9 price-path cases, 3 current-volume exclusion cases, frozen-source availability and comparison disagreement; no formal volume classification.')
