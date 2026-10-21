"""Selected Work research: distinguish reference association from structural parenthood.

No scan, parent selection, ranking, new price threshold, or manual-label training.
"""
import copy,gzip,json
from decimal import Decimal as D
from observation_bundle import ROOT,load_inputs,unpack_snapshots,write,earliest

def relation(source,z,context,cutoff,catalog):
    if z['known_on_saved_bar']>cutoff:raise ValueError('Local activity not yet confirmed')
    out={'cutoff':cutoff,'zone_id':z['zone_id'],'local_known_on':z['known_on_saved_bar'],
         'context_available':context['known_on']<=cutoff,'formal_parent':None,'selected_role':None,
         'qualification':'SELECTED_REFERENCE_ASSOCIATION_RESEARCH_NOT_PARENT_SELECTION'}
    if not out['context_available']:return out
    path=[b for b in source['bars']if z['path_start']<=b['date']<=z['path_end']]
    low=min(D(b['low'])for b in path);high=max(D(b['high'])for b in path)
    assert low==D(z['raw_path_frame']['observed_low'])and high==D(z['raw_path_frame']['observed_high'])
    out.update({'context_id':context['context_id'],'context_kind':context['kind'],'context_known_on':context['known_on'],
        'context_source_period':[context['start'],context['source_end']],
        'context_price_bracket':[context['low'],context['high']],
        'local_path_period':[z['path_start'],z['path_end']],
        'local_complete_evidence_period':[earliest(z,catalog),z['known_on_saved_bar']],
        'common_price_contained_in_reference_bracket':D(context['low'])<=D(z['common_close_low'])and D(z['common_close_high'])<=D(context['high']),
        'raw_path_price_contained_in_reference_bracket':D(context['low'])<=low and high<=D(context['high']),
        'raw_path_strictly_below_reference_bracket':high<D(context['low']),
        'path_time_contained_in_reference_source_period':context['start']<=z['path_start']and z['path_end']<=context['source_end'],
        'complete_evidence_time_contained_in_reference_source_period':context['start']<=earliest(z,catalog)and z['known_on_saved_bar']<=context['source_end'],
        'local_path_entirely_after_reference_source_period':z['path_start']>context['source_end'],
        'listed_gap_dates_in_local_evidence':[d for d in source['source_gaps']['known_calendar_missing_dates']if earliest(z,catalog)<=d<=z['known_on_saved_bar']],
        'calendar_status':'LISTED_GAPS_ONLY_NOT_EXHAUSTIVE'})
    return out

def main():
    sources,c=load_inputs();z=lambda code,a,b:next(x for x in c['zones']if x['code']==code and x['path_start']==a and x['path_end']==b)
    ct=lambda code,start,kind:next(x for x in c['contexts']if x['code']==code and x['start']==start and x['scale']=='0.03'and x['kind']==kind)
    bracket='ADJACENT_ORIGINAL_PIVOT_PRICE_BRACKET_NOT_BOX';box='SAVED_ORIGINAL_RESEARCH_BOX_NOT_FORMAL_PARENT'
    az=z('2884','2026-09-30','2026-10-05');old=ct('2884','2026-08-12',bracket);later=ct('2884','2026-09-17',bracket)
    abcin=z('1101','2025-05-19','2025-05-23');abcout=z('1101','2025-06-06','2025-06-11');abcbox=ct('1101','2025-04-08',box)
    specs=[('A-earlier-reference','2884',az,old,'2026-10-06'),('A-next-reference-not-yet-known','2884',az,later,'2026-10-06'),
           ('A-next-reference-now-known','2884',az,later,'2026-10-07'),('ABC-later-internal-activity','1101',abcin,abcbox,'2025-05-26'),
           ('ABC-later-external-activity','1101',abcout,abcbox,'2025-06-12')]
    results={name:relation(sources[code],zz,cc,cut,c)for name,code,zz,cc,cut in specs}
    # Exact counterexamples, checked against saved source periods and independent OHLC extrema.
    assert results['A-earlier-reference']['common_price_contained_in_reference_bracket']and results['A-earlier-reference']['local_path_entirely_after_reference_source_period']
    assert not results['A-next-reference-not-yet-known']['context_available']and 'context_id'not in results['A-next-reference-not-yet-known']
    assert results['A-next-reference-now-known']['raw_path_price_contained_in_reference_bracket']and not results['A-next-reference-now-known']['path_time_contained_in_reference_source_period']
    assert results['ABC-later-internal-activity']['raw_path_price_contained_in_reference_bracket']and results['ABC-later-internal-activity']['local_path_entirely_after_reference_source_period']
    assert results['ABC-later-external-activity']['raw_path_strictly_below_reference_bracket']
    # A not-yet-confirmed selected reference cannot expose its later numeric values.
    poison=copy.deepcopy(later);poison.update(low='-999',high='999',start='1900-01-01',source_end='2099-01-01')
    assert relation(sources['2884'],az,poison,'2026-10-06',c)==results['A-next-reference-not-yet-known']
    for name,code,zz,cc,cut in specs:
        prefix=copy.deepcopy(sources[code]);prefix['bars']=[b for b in prefix['bars']if b['date']<=cut]
        assert relation(prefix,zz,cc,cut,c)==results[name]
    packed=json.loads(gzip.decompress((ROOT/'observation-bundles.json.gz').read_bytes()));bundles=unpack_snapshots(packed,c)
    gp=next(p for p in c['pivots']if p['code']=='1101'and p['scale']=='0.03'and p['occurred_at']=='2023-05-02'and p['kind']=='HIGH')
    before=any(v['pivot_id']==gp['id']for v in bundles['G2-2023-04-27']['retained_original_pivot_views'])
    after=next(v for v in bundles['G2-2023-08-16']['retained_original_pivot_views']if v['pivot_id']==gp['id'])
    assert not before and gp['known_on']=='2023-05-09'and after['first_saved_crossing_from_availability']is None
    results['G2-original-high-reference']={'point':gp,'unavailable_in_2023_04_27_bundle':not before,'view_at_2023_08_16':after,
        'role':'ORIGINAL_HIGH_POINT_REFERENCE_NOT_PRICE_INTERVAL_OR_PARENT','formal_parent':None}
    # Retrospective display audit only; not fed into compose(), relation(), or a classifier.
    manual_scopes={}
    for name,key,start,end,expected in [('ABC','ABC-2025-06-13','2025-04-07','2025-06-02',39),('G2','G2-2023-08-16','2023-01-16','2023-08-16',136)]:
        r=bundles[key];rows=[b for b in sources[r['code']]['bars']if start<=b['date']<=end];assert len(rows)==expected
        zs=[next(z for z in c['zones']if z['zone_id']==v['zone_id'])for v in r['local_activity_views']]
        inside=[z['zone_id']for z in zs if start<=z['path_start']and z['path_end']<=end]
        outside=[z['zone_id']for z in zs if z['path_start']>end]
        assert len(inside)==(39 if name=='ABC' else 170)and len(outside)==(1 if name=='ABC' else 0)
        manual_scopes[name]={'review_knowledge_date':'2026-10-21','display_only':True,'manual_period':[start,end],
            'manual_saved_rows':len(rows),'research_bundle':key,'local_path_inside_manual_dates':inside,'local_path_entirely_after_manual_dates':outside,
            'formal_parent':None,'formal_price_bounds':None,'manual_label_used_as_historical_input':False,
            'qualification':'TEMPORAL_DISPLAY_ASSOCIATION_ONLY_NOT_FORMAL_MEMBERSHIP_OR_CLASSIFIER_VALIDATION'}
    write(ROOT/'structure-link-cases.json',{'selected_cases':results,'retrospective_display_audit':manual_scopes,
        'research_driver_attempts':2,'successful_research_driver_runs':1,'first_attempt':'SYNTAX_ERROR_BEFORE_EXECUTION_CORRECTED','classification':'NOT_VALIDATED','primary_pressure_id':None,'historical_signal_eligible':False})
    write(ROOT/'structure-link-verification.json',{'status':'PASS_SELECTED_RESEARCH_CONSTRAINTS','selected_reference_cases':6,
        'exact_counterexample_assertions':5,'cutoff_source_prefix_checks':5,'unavailable_reference_value_poison_checks':1,
        'G2_original_point_availability_and_no_strict_saved_crossing_checks':1,'retrospective_scope_counts':2,
        'source_or_prior_artifact_mutations':0,'formal_parent_assignments':0,'product_or_Android_validation':False})
    print('PASS: selected reference associations, cutoff masking, two separate retrospective scope audits')
if __name__=='__main__':main()
