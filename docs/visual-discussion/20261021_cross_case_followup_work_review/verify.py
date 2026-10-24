"""Causal and directional checks of finite follow-up evidence, not a classifier test."""
import copy,json
from decimal import Decimal as D
from study import ROOT,SOURCES,EXPECTED,CASE_CONFIG,inputs,view,sha,write

def main():
 data=inputs();sources={k:json.loads(p.read_text())for k,p in SOURCES.items()};checks=0
 for case,cfg in CASE_CONFIG.items():
  bars=sources[cfg['code']]['bars'];queries=[q for q in data['queries']if q['case']==case]
  for cut in cfg['cutoffs']:
   before=[b for b in bars if b['date']<=cut]
   poisoned=copy.deepcopy(bars)
   for b in poisoned:
    if b['date']>cut:
     b.update(open='9000',high='9999',low='1',close='9998',volume_shares_scaled='999999999999')
   lowvol=copy.deepcopy(bars)
   for b in lowvol:b['volume_shares_scaled']='1'
   for q in queries:
    actual=view(bars,q,cut)
    assert actual==view(before,q,cut)==view(poisoned,q,cut)==view(lowvol,q,cut)
    if q['origin']>cut:assert actual is None
    if actual:
     assert all(q['origin']<f['date']<=cut for f in actual['facts'])
     assert actual['birth']==view(bars,q,cfg['end'])['birth']
     assert len(actual['facts'])==sum(actual['summary'][k]for k in ('above_count','equal_count','below_count'))
     assert actual['summary']['formal_standing_or_breakdown_confirmed']is None
     assert actual['summary']['formal_success_or_failure']is None
     # Price reflection swaps ABOVE/BELOW, preserving the directional facts.
     mirrored=copy.deepcopy(bars)
     for b in mirrored:
      b.update(open=str(D(100)-D(b['open'])),close=str(D(100)-D(b['close'])),high=str(D(100)-D(b['low'])),low=str(D(100)-D(b['high'])))
     mq=copy.deepcopy(q);mq['direction']='DOWN'if q['direction']=='UP'else'UP';mq['reference']['price']=str(D(100)-D(q['reference']['price']))
     mv=view(mirrored,mq,cut)
     for left,right in zip(actual['facts'],mv['facts']):
      for k in ('date','relative_to_origin_direction','strict_intraday_return_close_same_side','equal_boundary_touch_close_same_side','whole_bar_same_side','whole_bar_opposite_side','range_contains_reference'):assert left[k]==right[k]
    checks+=1
 final=json.loads((ROOT/'followup-results.json').read_text())
 gd,gr=final['G2'];abc=final['ABC'][0];a=final['A'][0]
 assert (gd['summary']['below_count'],gd['summary']['above_count'],gd['summary']['first_opposite_close'])==(10,7,'2023-07-25')
 assert gd['summary']['strict_intraday_return_close_same_side_dates']==['2023-07-13']
 assert gd['summary']['equal_boundary_touch_close_same_side_dates']==['2023-07-14']
 assert (gr['summary']['followup_bars_excluding_origin'],gr['summary']['above_count'])==(6,6)
 assert gr['summary']['strict_intraday_return_close_same_side_dates']==['2023-07-28']
 assert gr['summary']['equal_boundary_touch_close_same_side_dates']==['2023-07-31','2023-08-02']
 assert (gr['summary']['highest_followup_high'],gr['summary']['lowest_followup_low'])==('37.80','37.10')
 assert all(D(f['bar']['high'])<D('38.05')for f in gr['facts'])
 assert (abc['summary']['followup_bars_excluding_origin'],abc['summary']['below_count'],abc['summary']['highest_followup_high'])==(8,8,'28.00')
 assert abc['birth']['origin']['high']=='29.05'and abc['birth']['origin']['close']=='27.70'
 assert all(D(f['bar']['high'])<D('28.45')for f in abc['facts'])
 assert (a['summary']['followup_bars_excluding_origin'],a['summary']['above_count'],a['summary']['lowest_followup_low'])==(1,1,'48.00')
 assert a['birth']['origin']['close']=='48.80'and a['birth']['origin']['low']=='47.60'
 # Same reference identity persists through G2 down and reclaim; not two independent votes.
 assert gd['birth']['reference_id']==gr['birth']['reference_id']
 assert data['A_earlier_zone']['raw_path_frame']['high_origin_dates']==['2026-09-17']
 aq=next(q for q in data['queries']if q['case']=='A')
 assert aq['reference']['source_dates']==['2026-09-17']
 assert data['B_previous_summaries_unchanged']==json.loads(__import__('study').PRIOR_B.read_text())
 for code,p in SOURCES.items():assert sha(p)==EXPECTED[code]
 write('verification.json',{'status':'PASS','case_cutoffs':sum(len(c['cutoffs'])for c in CASE_CONFIG.values()),'query_cutoff_checks':checks,'prefix_and_future_price_volume_poison':True,'all_volume_one_no_price_evidence_change':True,'directional_price_reflection_checks':True,'births_immutable_and_future_origins_hidden':True,'four_real_episode_oracles':True,'strict_equal_whole_bar_tests_on_real_data':True,'same_G2_reference_and_A_shared_source_not_votes':True,'prior_B_summaries_equal_without_recomputation':True,'source_sha_unchanged':True,'formal_holding_success_dates_still_null':True,'selection':'FINITE_EX_POST_NOT_BLIND_OR_MARKET_RATE_VALIDATION','original_driver_verifier_and_crossing_volume_study_reruns':0,'product_browser_Android_tests':0})
 print('PASS:',checks,'query/cutoff checks, 4 real episode oracles; no formal classifier validated')
if __name__=='__main__':main()
