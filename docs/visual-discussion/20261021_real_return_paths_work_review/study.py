"""Finite ex-post real return contrasts; no classifier or reaction confirmation."""
import copy, hashlib, json
from pathlib import Path
from decimal import Decimal as D
ROOT = Path(__file__).resolve().parent
SOURCE = Path('/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')
BASELINE = Path('/workspace/scratch/89f271ea68f4/response-witness-research/response-witnesses.json')
def write(name, value):
    (ROOT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def side(value, reference):
    return 'ABOVE' if D(value)>D(reference) else 'BELOW' if D(value)<D(reference) else 'EQUAL'
def project(source, original, cutoff):
    first = original['followup']['first_later_close_outside_contact_bar']
    assert first['date'] <= cutoff
    reference = original['reference']['price']
    initial_side = side(first['close'], reference)
    assert initial_side != 'EQUAL'
    bars = [b for b in source['bars'] if first['date'] < b['date'] <= cutoff]
    gaps = [d for d in source['source_gaps']['known_calendar_missing_dates'] if first['date'] < d <= cutoff]
    qualified = [b for b in bars if not gaps or b['date'] < gaps[0]]
    touch = next((b for b in qualified if D(b['low'])<=D(reference)<=D(b['high'])), None)
    close_return = next((b for b in qualified if side(b['close'], reference) != initial_side), None)
    opposite = next((b for b in qualified if side(b['close'], reference) not in [initial_side, 'EQUAL']), None)
    current = ([first]+bars)[-1]
    return {'cutoff':cutoff, 'original_reference':original['reference'],
        'original_birth':original['birth'], 'original_first_close_witness':first,
        'first_witness_close_side':initial_side, 'first_later_daily_range_intersection':touch,
        'first_later_close_at_or_across_reference':close_return, 'first_later_strict_opposite_close':opposite,
        'current_bar':current, 'current_close_side':side(current['close'],reference),
        'listed_gaps_after_original_witness':gaps, 'current_path':bars,
        'formal_reaction_confirmation':None, 'formal_structure_change':None,
        'independent_reaction_count':None, 'primary_pressure_id':None,
        'historical_signal_eligible':False, 'classifier':'NOT_VALIDATED',
        'Android':'NOT_TESTED_NEW_BUILD', 'action_eligibility':'NOT_EVALUATED'}
def run():
    source=json.loads(SOURCE.read_text()); baseline=json.loads(BASELINE.read_text())
    cases={'earlier-up-later-return':('G2-low-later-up@2023-04-11',['2023-04-11','2023-07-20','2023-07-21','2023-07-24','2023-07-25','2023-08-02']),
           'earlier-down-wick-then-close-return':('G2-low-later-down@2023-07-10',['2023-07-10','2023-07-12','2023-07-13','2023-07-14','2023-07-21','2023-07-24','2023-07-25','2023-07-26','2023-08-02'])}
    views={}; count=0
    for name,(key,cuts) in cases.items():
        original=baseline[key]
        for cut in cuts:
            r=project(source,original,cut); views[name+'@'+cut]=r
            prefix=copy.deepcopy(source);prefix['bars']=[b for b in prefix['bars'] if b['date']<=cut]
            assert project(prefix,original,cut)==r
            poison=copy.deepcopy(source);poison['manual_labels']={'force_support':True}
            for b in poison['bars']:
                if b['date']>cut:b.update(open='999',high='999',low='-999',close='999',volume_shares_scaled='999999999')
            assert project(poison,original,cut)==r
            assert r['original_birth']==original['birth'] and r['original_first_close_witness']==original['followup']['first_later_close_outside_contact_bar']
            assert r['formal_reaction_confirmation'] is None and r['formal_structure_change'] is None
            # Independently confirm every first-event date from source prefix.
            seq=[b for b in prefix['bars'] if original['followup']['first_later_close_outside_contact_bar']['date']<b['date']]
            p=D(original['reference']['price']); was_above=r['first_witness_close_side']=='ABOVE'
            matches=[b for b in seq if D(b['low'])<=p<=D(b['high'])]
            assert r['first_later_daily_range_intersection']==(matches[0] if matches else None)
            matches=[b for b in seq if D(b['close'])<=p] if was_above else [b for b in seq if D(b['close'])>=p]
            assert r['first_later_close_at_or_across_reference']==(matches[0] if matches else None)
            count+=1
    down=views['earlier-down-wick-then-close-return@2023-07-13']
    assert down['first_later_daily_range_intersection']['date']=='2023-07-13' and down['first_later_close_at_or_across_reference'] is None
    down=views['earlier-down-wick-then-close-return@2023-07-25']
    assert down['first_later_strict_opposite_close']['date']=='2023-07-25' and down['current_bar']['close']=='37.40'
    up=views['earlier-up-later-return@2023-07-21']
    assert up['first_later_strict_opposite_close']['date']=='2023-07-21' and up['current_bar']['close']=='36.10'
    assert views['earlier-up-later-return@2023-07-25']['current_close_side']=='ABOVE'
    # Equality is separately visible and cannot be called strict crossing.
    fake=copy.deepcopy(source); fake['bars']=[copy.deepcopy(down['original_first_close_witness'])]
    equal={**fake['bars'][0], 'date':'2023-07-11','open':'37.15','high':'37.15','low':'37.15','close':'37.15'}
    fake['bars'].append(equal)
    eq=project(fake,baseline['G2-low-later-down@2023-07-10'],'2023-07-11')
    assert eq['first_later_close_at_or_across_reference']==equal and eq['first_later_strict_opposite_close'] is None
    fake['source_gaps']['known_calendar_missing_dates']=['2023-07-11']
    gap=project(fake,baseline['G2-low-later-down@2023-07-10'],'2023-07-11')
    assert gap['first_later_close_at_or_across_reference'] is None and gap['current_bar']==equal
    write('return-paths.json', views)
    write('verification.json', {'status':'PASS_SCOPED_REAL_RETURN_STUDY','real_views':count,'prefix_isolation':count,'future_price_volume_manual_poison':count,'original_birth_and_first_witness_preserved':count,'first_return_events_independently_checked':count,'synthetic_equality_and_gap_controls':2,'driver_runs':1,'old_drivers_and_verifiers_rerun':0,'selection':'Two ex-post specified, overlapping paths within previously reviewed G2; not independent samples or success rate','source_qualifications':source['source_gaps'],'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(BASELINE.read_bytes()).hexdigest()})
    print('PASS: 15 real cutoff views, prefix/future isolation, fixed witnesses, 2 equality/gap controls')
if __name__=='__main__':run()
