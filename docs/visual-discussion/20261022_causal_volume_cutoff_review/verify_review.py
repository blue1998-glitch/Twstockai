"""Checks the research cutoff contract, not recognition or strategy quality."""
from copy import deepcopy
from datetime import date
from decimal import Decimal as D
import hashlib,json
from pathlib import Path
from build_review import cases_from,snapshot,build

root=Path(__file__).resolve().parent
raw=(root/'source-inputs.json').read_bytes();value=json.loads(raw)
checks=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)

cases=cases_from(value);saved=json.loads((root/'cutoff-facts.json').read_text())
check('regenerated_facts_equal_saved',build(value)==saved)
for c in cases:
    check(c['id']+'_unique_sorted_dates',len({b['date'] for b in c['bars']})==len(c['bars']) and c['bars']==sorted(c['bars'],key=lambda b:b['date']))
    check(c['id']+'_valid_OHLCV',all(D(b['high'])>=max(D(b['open']),D(b['close']),D(b['low'])) and D(b['low'])<=min(D(b['open']),D(b['close'])) and int(b['volume_shares'])>=0 for b in c['bars']))
    for day in c['dates']:
        s=snapshot(c,day)
        check(c['id']+'_'+day+'_exact_prefix',s['bars']==[b for b in c['bars'] if b['date']<=day] and s['latest']['date']==day)
        m=deepcopy(c)
        for b in m['bars']:
            if b['date']>day:b.update(open='99999',high='99999',low='0',close='0',volume_shares='999999999999')
        m['bars'].append(dict(date='2027-01-01',open='0',high='999999',low='0',close='0',volume_shares='999999999999'))
        m['review_notes']=[dict(event_date='1900-01-01',text='POISON_FUTURE_INTERPRETATION')]
        check(c['id']+'_'+day+'_future_poison_and_annotation_independent',s==snapshot(m,day))
        check(c['id']+'_'+day+'_no_economic_or_trade_promotion',s['volume_economic_role']=='UNKNOWN' and s['actual_trapped_share_count'] is None and s['inferred_structure_state'] is None and s['historical_signal_eligible'] is False)
        check(c['id']+'_'+day+'_broad_context',(date.fromisoformat(day)-date.fromisoformat(s['first_date'])).days>=180)
    try:snapshot(c,'2025-06-01' if c['code']=='1101' else '2026-10-11')
    except ValueError:checks.append(c['id']+'_missing_date_rejected')
    else:raise AssertionError('nearest date used')
check('1101_official_source_field_exact_strings',all(any(b['date']==f"{int(r[0].split('/')[0])+1911}-{r[0].split('/')[1]}-{r[0].split('/')[2]}" and [b[k] for k in ['volume_shares','open','high','low','close']]==[r[i].replace(',','').strip() for i in [1,3,4,5,6]] for b in cases[0]['bars']) for m in value['raw1101'] for r in m['response']['data']))
check('2884_saved_source_exact_strings',all([b[k] for k in ['date','open','high','low','close','volume_shares']]==[r[k] for k in ['date','open','high','low','close','volume_shares_scaled']] for b,r in zip(cases[1]['bars'],value['raw2884']['bars'])))
a=snapshot(cases[1],'2026-10-15');b=snapshot(cases[1],'2026-10-16')
check('2884_oct15_whole_K_above_saved_high',a['reference_comparison']['whole_candle_above'] and a['reference_comparison']['close_relation']=='ABOVE')
check('2884_oct16_price_above_but_volume_below_old_column',b['reference_comparison']['close_relation']=='ABOVE' and b['reference_comparison']['volume_vs_source_bar']=='BELOW')
check('source_input_unchanged',raw==(root/'source-inputs.json').read_bytes())
findings=json.loads((root/'case-findings.json').read_text())
check('manual_ABC39_stays_retrospective',findings['manual_range']['count']==39 and findings['manual_range']['historical_membership_known_at'] is None)
check('manual_ABC_price_and_volume_peaks_distinct',findings['price_peak_rows'][0]['date']=='2025-05-13' and findings['volume_peak_rows'][0]['date']=='2025-04-07' and findings['volume_peak_rows'][0]['volume_shares']=='118749437')
check('observation_minimum_not_formal_box_floor',findings['boundary_guard']['earlier_minimum_low']=='28.45' and findings['boundary_guard']['june2_low']=='27.65' and findings['boundary_guard']['june2_close']=='27.70' and findings['boundary_guard']['formal_box_floor'] is None)
report=dict(status='PASS',checks=len(checks),check_names=checks,scope='RESEARCH_SAVED_FACT_PREFIX_ONLY_NOT_CLASSIFIER_TEST',source_commit=value['base_commit'],facts_sha256=hashlib.sha256((root/'cutoff-facts.json').read_bytes()).hexdigest(),classifier='NOT_VALIDATED',android='NOT_TESTED_NEW_RESEARCH_VIEW')
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
