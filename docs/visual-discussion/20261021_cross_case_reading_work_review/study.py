"""Selected cross-case reading, not automatic recognition or structural promotion."""
import copy,json,os
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={'1101':Path(os.environ.get('STOCK_STUDY_1101','/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')),
         '2884':Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))}
G2=Path('/workspace/scratch/e9363d3b9105/return-context-research/context-views.json')
def write(name,x):(ROOT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def side(value,point):return 'ABOVE'if D(value)>D(point)else'BELOW'if D(value)<D(point)else'EQUAL'
def loc(value,lo,hi):return 'BELOW'if D(value)<D(lo)else'ABOVE'if D(value)>D(hi)else'AT_LOW'if D(value)==D(lo)else'AT_HIGH'if D(value)==D(hi)else'INSIDE'
def left(z,c):return c['turns'][c['legs'][z['leg_ids'][0]]['from_turn_id']]['left_evidence_date']
def turns(z,c):return {i for l in z['leg_ids']for i in [c['legs'][l]['from_turn_id'],c['legs'][l]['to_turn_id']]}
def project(source,all_inputs,case,cut):
    c=all_inputs['cases'][case];bs=[b for b in source['bars']if b['date']<=cut];last=bs[-1]
    out={'case':case,'code':c['code'],'cutoff':cut,'current_bar':last,'points':{},'activities':{},'activity_comparisons':[],
         'earlier_activity_high_source_binding':None,'formal_pattern':None,'formal_structure_change':None,
         'formal_parent':None,'formal_end':None,'formal_reaction':None,'importance_score':None,
         'independent_confirmation_count':None,'primary_pressure_id':None,'historical_signal_eligible':False,
         'manual_labels_used':False,'classifier':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED',
         'Android':'NOT_TESTED_NEW_BUILD','actions_and_flywheel':'NOT_EVALUATED'}
    for key,p in c['points'].items():
        if p['known_on']>cut:out['points'][key]=None;continue
        post=[b for b in bs if b['date']>=p['known_on']]
        out['points'][key]={'point':copy.deepcopy(p),'current_close_side':side(last['close'],p['price']),
            'current_daily_range_contains_point':D(last['low'])<=D(p['price'])<=D(last['high']),
            'first_saved_close_above_from_availability':next((b for b in post if D(b['close'])>D(p['price'])),None),
            'first_saved_close_below_from_availability':next((b for b in post if D(b['close'])<D(p['price'])),None)}
    for key,z in c['zones'].items():
        if z['known_on_saved_bar']>cut:out['activities'][key]=None;continue
        frame=z['raw_path_frame'];out['activities'][key]={'zone':copy.deepcopy(z),'complete_evidence_start':left(z,all_inputs),
            'current_close_vs_common':loc(last['close'],z['common_close_low'],z['common_close_high']),
            'current_close_vs_raw':loc(last['close'],frame['observed_low'],frame['observed_high']),
            'whole_current_daily_range_vs_raw':'ABOVE'if D(last['low'])>D(frame['observed_high'])else'BELOW'if D(last['high'])<D(frame['observed_low'])else'INTERSECTS_OR_EQUAL'}
    keys=list(c['zones'])
    for i,a in enumerate(keys):
        for b in keys[i+1:]:
            if out['activities'][a]is None or out['activities'][b]is None:continue
            x,y=c['zones'][a],c['zones'][b];xl,xh=[D(x[k])for k in ['common_close_low','common_close_high']];yl,yh=[D(y[k])for k in ['common_close_low','common_close_high']]
            out['activity_comparisons'].append({'earlier':a,'later':b,'both_common_edges_higher':yl>xl and yh>xh,'both_common_edges_lower':yl<xl and yh<xh,
                'raw_ranges_overlap':max(D(x['raw_path_frame']['observed_low']),D(y['raw_path_frame']['observed_low']))<=min(D(x['raw_path_frame']['observed_high']),D(y['raw_path_frame']['observed_high'])),
                'shared_leg_ids':sorted(set(x['leg_ids'])&set(y['leg_ids'])),'shared_turn_ids':sorted(turns(x,all_inputs)&turns(y,all_inputs)),
                'later_complete_source_after_earlier_known':left(y,all_inputs)>x['known_on_saved_bar'],
                'independence_or_importance_inferred':False})
    if out['points']['high']and out['activities']['earlier']:
        p=out['points']['high']['point'];z=out['activities']['earlier']['zone']
        out['earlier_activity_high_source_binding']={'point_price_equals_raw_high':D(p['price'])==D(z['raw_path_frame']['observed_high']),
            'shared_raw_high_source_dates':sorted(set(p['source_dates'])&set(z['raw_path_frame']['high_origin_dates'])),
            'point_date_in_complete_evidence_period':left(z,all_inputs)<=p['occurred_at']<=z['known_on_saved_bar'],
            'multiple_confirmations_inferred':False}
    return out
def findings(views,g2):
    g=g2['2023-07-25'];a=views['A@2026-10-15'];abc=views['ABC@2025-06-02']
    return {'meaning':'SAME_QUESTIONS_DIFFERENT_SAVED_PRICE_EVIDENCE_NOT_SAME_FORMAL_LABEL',
        'G2':{'source':'previous context-views@2023-07-25; not recomputed','close':g['current_bar']['close'],'above_single_reference':g['original_points']['later-low']['current_close_side']=='ABOVE','relative_to_earlier_common':g['local_activities']['earlier-local']['current_vs_common'],'relative_to_retained_high':g['original_points']['retained-high']['current_close_side'],'formal_change':None},
        'ABC':{'cutoff':'2025-06-02','close':abc['current_bar']['close'],'relative_to_original_low':abc['points']['low']['current_close_side'],'relative_to_earlier_common':abc['activities']['earlier']['current_close_vs_common'],'relative_to_earlier_raw':abc['activities']['earlier']['current_close_vs_raw'],'daily_range_still_contains_original_low':abc['points']['low']['current_daily_range_contains_point'],'later_outside_activity_available':abc['activities']['outside']is not None,'formal_end':None},
        'A':{'cutoff':'2026-10-15','close':a['current_bar']['close'],'relative_to_original_high':a['points']['high']['current_close_side'],'relative_to_earlier_common':a['activities']['earlier']['current_close_vs_common'],'relative_to_earlier_raw':a['activities']['earlier']['current_close_vs_raw'],'daily_range_contains_original_high':a['points']['high']['current_daily_range_contains_point'],'original_high_and_earlier_raw_share_source':a['earlier_activity_high_source_binding'],'formal_change':None}}
if __name__=='__main__':
    c=json.loads((ROOT/'study-inputs.json').read_text());sources={code:json.loads(p.read_text())for code,p in SOURCES.items()}
    views={case+'@'+cut:project(sources[q['code']],c,case,cut)for case,q in c['cases'].items()for cut in q['cutoffs']}
    write('cross-case-views.json',views);write('cross-case-findings.json',findings(views,json.loads(G2.read_text())))
    print('Saved 21 cutoff views and cross-case findings; no prior driver rerun')
