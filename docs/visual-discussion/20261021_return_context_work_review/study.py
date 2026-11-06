"""Finite cutoff-qualified local/background comparison; no structural classifier."""
import copy,json,os
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('STOCK_STUDY_SOURCE','/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json'))
def write(name,x):(ROOT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def location(value,low,high):
    v,a,b=map(D,[value,low,high])
    return 'BELOW' if v<a else 'ABOVE' if v>b else 'AT_LOW' if v==a else 'AT_HIGH' if v==b else 'INSIDE'
def turn_ids(z,c):return {i for leg in z['leg_ids']for i in [c['legs'][leg]['from_turn_id'],c['legs'][leg]['to_turn_id']]}
def left_date(z,c):return c['turns'][c['legs'][z['leg_ids'][0]]['from_turn_id']]['left_evidence_date']
def project(source,c,cut):
    bars=[b for b in source['bars']if b['date']<=cut];last=bars[-1]
    out={'cutoff':cut,'current_bar':last,'local_activities':{},'original_points':{},'original_boxes':{},
         'local_comparisons':[],'box_source_comparison':None,
         'formal_structure':None,'formal_parent':None,'formal_merge':None,'formal_end':None,
         'formal_reaction':None,'selected_role':None,'importance_score':None,'primary_pressure_id':None,
         'independent_confirmation_count':None,'historical_signal_eligible':False,
         'classifier':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','Android':'NOT_TESTED_NEW_BUILD',
         'actions_and_flywheel':'NOT_EVALUATED','manual_labels_used':False}
    for name,p in c['pivots'].items():
        if p['known_on']>cut:out['original_points'][name]=None;continue
        value=D(p['price']);cl=D(last['close'])
        out['original_points'][name]={'point':copy.deepcopy(p),'current_close_side':'ABOVE'if cl>value else'BELOW'if cl<value else'EQUAL'}
    for name,z in c['zones'].items():
        if z['known_on_saved_bar']>cut:out['local_activities'][name]=None;continue
        path=[b for b in bars if z['path_start']<=b['date']<=z['path_end']]
        assert min(D(b['low'])for b in path)==D(z['raw_path_frame']['observed_low'])
        assert max(D(b['high'])for b in path)==D(z['raw_path_frame']['observed_high'])
        out['local_activities'][name]={'zone':copy.deepcopy(z),'complete_evidence_start':left_date(z,c),
            'current_vs_common':location(last['close'],z['common_close_low'],z['common_close_high']),
            'current_vs_raw':location(last['close'],z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']),
            'source_period_is_not_formal_lifetime':True}
    keys=list(c['zones'])
    for i,oldkey in enumerate(keys):
        for newkey in keys[i+1:]:
            old,new=out['local_activities'][oldkey],out['local_activities'][newkey]
            if old is None or new is None:continue
            a,b=old['zone'],new['zone'];al,ah=map(D,[a['common_close_low'],a['common_close_high']]);bl,bh=map(D,[b['common_close_low'],b['common_close_high']])
            raw_overlap=max(D(a['raw_path_frame']['observed_low']),D(b['raw_path_frame']['observed_low']))<=min(D(a['raw_path_frame']['observed_high']),D(b['raw_path_frame']['observed_high']))
            out['local_comparisons'].append({'older':oldkey,'later':newkey,'both_common_edges_higher':bl>al and bh>ah,'both_common_edges_lower':bl<al and bh<ah,
                'raw_price_ranges_overlap':raw_overlap,'shared_leg_ids':sorted(set(a['leg_ids'])&set(b['leg_ids'])),
                'shared_turn_ids':sorted(turn_ids(a,c)&turn_ids(b,c)),
                'later_complete_evidence_strictly_after_older_known':left_date(b,c)>a['known_on_saved_bar'],
                'meaning':'SOURCE_FRESHNESS_AND_PRICE_LOCATION_ONLY_NOT_STATISTICAL_INDEPENDENCE_OR_STRUCTURE_PROMOTION'})
    for name,context in c['contexts'].items():
        if context['known_on']>cut:out['original_boxes'][name]=None;continue
        out['original_boxes'][name]={'context':copy.deepcopy(context),'current_close_location':location(last['close'],context['low'],context['high'])}
    a,b=[out['original_boxes'][k]for k in ['earlier-original-box','later-original-box']]
    if a and b:
        a,b=a['context'],b['context']
        out['box_source_comparison']={'same_high_price':D(a['high'])==D(b['high']),
            'shared_turn_ids':sorted(set(a['source_turn_ids'])&set(b['source_turn_ids'])),
            'later_low_below_earlier_low':D(b['low'])<D(a['low']),
            'meaning':'REUSED_ORIGINAL_SOURCES_NOT_MULTIPLE_LATER_TESTS_OR_LARGER_FORMAL_G2_BOUNDS'}
    return out
if __name__=='__main__':
    source=json.loads(SOURCE.read_text());c=json.loads((ROOT/'study-inputs.json').read_text())
    write('context-views.json',{cut:project(source,c,cut)for cut in c['cutoffs']})
    print('Saved 13 cutoff-qualified context comparisons; no original engine or driver run')
