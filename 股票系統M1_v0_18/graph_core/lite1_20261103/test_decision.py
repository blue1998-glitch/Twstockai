"""Synthetic saved-fact presentation contracts, not market samples."""
import copy,unittest
from graph_core.lite1_20261103 import decision as d

def fixture(kind='CLOSE_CROSS_UP'):
 s=dict(identity='TWSE:SYN',code='SYN',market='TWSE',as_of='2026-10-30',status='ANALYZED_FINMIND_HISTORY')
 ref=dict(pivot_id='p',price='32.8500',confirmed_at='2026-10-20',occurred_at='2026-10-19',path=dict(events=[dict(type=kind,date=s['as_of'],first_observed_at=s['as_of'])]))
 r=dict(schema_version='graph-recognition-research/0.2',context=dict(code='SYN',exchange='TWSE',source_id='synthetic-source',price_basis_id='synthetic-raw'),as_of=s['as_of'],result_id='synthetic-result',source_prefix_fingerprint='synthetic-prefix',comparison=dict(primary_pressure_id=None),data_gaps=dict(basis_resets=[],missing_expected_dates=[],missing_price_rows=[]),boxes=[],pivots=[],reference_candidates=[ref],anchor_volume=dict(ratio_to_previous_means={'1':'0.9'}))
 return s,r

class Decisions(unittest.TestCase):
 def test_cross_up_is_close_fact_with_exact_price_and_source_pointer(self):
  s,r=fixture();x=d.project(s,r);self.assertEqual(x['headline'],'突破參照');self.assertEqual(x['key_prices'],['32.8500']);self.assertEqual(x['refs'][0]['pointer'],'/reference_candidates/0/path/events/0');self.assertIsNone(x['primary_pressure_id']);self.assertFalse(x['formal_authorized'])
 def test_down_return_and_equal_remain_distinct(self):
  for event,label in [('CLOSE_CROSS_DOWN','跌破參照'),('FAILED_UP_RETURN_BELOW','跌回參照下'),('CLOSE_EQUALS_REFERENCE','收盤等於參照'),('RETURN_ABOVE_AFTER_DOWN','重返參照上')]:
   s,r=fixture(event);self.assertEqual(d.project(s,r)['headline'],label)
 def test_range_return_uses_both_saved_research_bounds(self):
  s,r=fixture();r['reference_candidates']=[];r['boxes']=[dict(id='b',start='2026-10-01',confirmed_at='2026-10-20',usable_at_anchor=True,research_bounds=dict(low='30.000',high='32.8500'),path=dict(events=[dict(type='CLOSE_REENTERED_RANGE',date=s['as_of'],first_observed_at=s['as_of'])]))]
  x=d.project(s,r);self.assertEqual(x['headline'],'回到區間');self.assertEqual(x['key_prices'],['30.000','32.8500']);self.assertEqual(x['key_caption'],'多個價位')
 def test_initial_position_is_never_called_a_breakout(self):
  s,r=fixture('INITIAL_CLOSE_LOCATION');self.assertEqual(d.project(s,r)['headline'],'今日無新過線')
 def test_all_conflicting_references_preserved_no_winner(self):
  s,r=fixture();other=copy.deepcopy(r['reference_candidates'][0]);other.update(pivot_id='other',price='35.50');other['path']['events'][0]['type']='CLOSE_CROSS_DOWN';r['reference_candidates'].append(other)
  x=d.project(s,r);self.assertEqual(x['headline'],'多參照分歧');self.assertEqual(len(x['refs']),2);self.assertIsNone(x['primary_pressure_id'])
 def test_volume_does_not_cancel_price_fact_or_confirm_it(self):
  s,r=fixture();x=d.project(s,r);self.assertEqual(x['headline'],'突破參照');self.assertEqual(x['volume_label'],'量減（較前筆）');self.assertIsNone(x['volume_confirms_price'])
 def test_exact_volume_equality_and_near_equality(self):
  for v,label in [('1','量平（較前筆）'),('1.000000000000000000000001','量增（較前筆）'),('0.999999999999999999999999','量減（較前筆）'),(None,'量未知')]:
   s,r=fixture();r['anchor_volume']['ratio_to_previous_means']['1']=v;self.assertEqual(d.project(s,r)['volume_label'],label)
 def test_current_reset_means_unknown_not_structural_failure(self):
  s,r=fixture();r['data_gaps']['basis_resets']=[s['as_of']];x=d.project(s,r);self.assertEqual(x['headline'],'今日不可判定');self.assertEqual(x['volume_label'],'量不可比');self.assertEqual(x['refs'],[]);self.assertIsNone(x['structural_invalidation'])
 def test_old_reset_does_not_erase_new_comparable_events(self):
  s,r=fixture();r['data_gaps']['basis_resets']=['2026-01-01'];self.assertEqual(d.project(s,r)['headline'],'突破參照')
 def test_stopped_reference_not_reused(self):
  s,r=fixture();r['reference_candidates'][0]['path']['events'].insert(0,dict(type=d.STOP,date='2026-10-25',first_observed_at='2026-10-25'));self.assertFalse(d.project(s,r)['can_judge'])
 def test_short_and_missing_have_direct_labels(self):
  s,r=fixture();s['status']='INSUFFICIENT_HISTORY';self.assertEqual(d.project(s,r)['headline'],'歷史不足');s['status']='MISSING_QUOTE';self.assertEqual(d.empty(s)['risk'],'缺少今日行情')
 def test_source_or_date_mismatch_refused(self):
  s,r=fixture();r['context']['code']='OTHER'
  with self.assertRaises(ValueError):d.project(s,r)
 def test_later_confirmation_not_visible_earlier(self):
  s,r=fixture();r['reference_candidates'][0]['confirmed_at']='2026-11-01';x=d.project(s,r);self.assertFalse(x['can_judge']);self.assertEqual(x['refs'],[])
 def test_inputs_unchanged(self):
  s,r=fixture();old=copy.deepcopy((s,r));d.project(s,r);self.assertEqual((s,r),old)
 def test_same_numeric_price_formats_preserve_all_ties(self):
  s,r=fixture();other=copy.deepcopy(r['reference_candidates'][0]);other.update(pivot_id='other',price='32.85');r['reference_candidates'].append(other);x=d.project(s,r);self.assertEqual(x['key_prices'],['32.8500']);self.assertEqual([v['price'] for v in x['refs']],['32.8500','32.85'])

if __name__=='__main__':unittest.main()
