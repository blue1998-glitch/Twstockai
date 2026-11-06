"""Source audit for a present-day semantic review, not a historical classifier."""
import hashlib,json,os
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE_PATHS={'1101':Path(os.environ.get('STOCK_STUDY_1101','/workspace/scratch/54685b8dac93/real-review/input/comparison-data.json')),
              '2884':Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))}
def write(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def source_facts(source,zones):
    # Deliberately takes no manual label or process-ownership decision.
    result={}
    for name,z in zones.items():
        bars=[b for b in source['bars']if z['path_start']<=b['date']<=z['path_end']]
        assert len(bars)==z['raw_path_frame']['records']
        assert min(D(b['low'])for b in bars)==D(z['raw_path_frame']['observed_low'])
        assert max(D(b['high'])for b in bars)==D(z['raw_path_frame']['observed_high'])
        right=next(b for b in source['bars']if b['date']==z['known_on_saved_bar'])
        assert right==z['right_evidence_bar']
        result[name]={'zone_id':z['zone_id'],'source_period':[z['path_start'],z['path_end']],
            'available_on_saved_date':z['known_on_saved_bar'],'common_interval':[z['common_close_low'],z['common_close_high']],
            'raw_interval':[z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']],
            'source_rows':len(bars),'formal_parent':None,'formal_merge':None,'support_or_pressure_response':None}
    return result
def main():
    inp=json.loads((ROOT/'study-inputs.json').read_text());sources={code:json.loads(p.read_text())for code,p in SOURCE_PATHS.items()}
    facts={case:source_facts(sources[inp['code_map'][case]],zs)for case,zs in inp['zones'].items()}
    get=lambda code,day:next(b for b in sources[code]['bars']if b['date']==day)
    abc=[b for b in sources['1101']['bars']if '2025-04-07'<=b['date']<='2025-06-02']
    after=[b for b in sources['1101']['bars']if '2025-06-03'<=b['date']<='2025-06-12']
    g2=[b for b in sources['1101']['bars']if '2023-01-16'<=b['date']<='2023-08-16']
    assert len(abc)==39 and len(after)==8 and len(g2)==136
    older,new=inp['zones']['G2']['earlier'],inp['zones']['G2']['later'];lo,hi=map(D,[older['common_close_low'],older['common_close_high']])
    path=[b for b in sources['1101']['bars']if new['path_start']<=b['date']<=new['path_end']]
    close_visits=[b for b in path if lo<=D(b['close'])<=hi]
    assert not close_visits and len(path)==8
    assert D(new['common_close_low'])<=lo<=hi<=D(new['common_close_high'])
    confirm=get('1101','2023-03-27');assert lo<=D(confirm['close'])<=hi
    b2,b3=get('1101','2025-06-02'),get('1101','2025-06-03')
    assert b2['close']=='27.70'and D(b2['low'])<D('28.45')<D(b2['high'])and D(b3['high'])<D('28.45')
    assert facts['ABC']['outside']['available_on_saved_date']=='2025-06-12'
    assert '2023-08-03'in sources['1101']['source_gaps']['known_calendar_missing_dates']
    manual_audit={'review_knowledge_date':inp['review_knowledge_date'],'role':'RETROSPECTIVE_DISPLAY_ONLY_NOT_HISTORICAL_INPUT',
        'ABC_existing_manual_period':['2025-04-07','2025-06-02'],'ABC_existing_manual_saved_rows':len(abc),
        'post_ABC_observation_window':['2025-06-03','2025-06-12'],'post_ABC_saved_rows':len(after),
        'post_ABC_added_to_manual_membership':False,'G2_existing_manual_period':['2023-01-16','2023-08-16'],
        'G2_existing_manual_saved_rows':len(g2),'A_existing_answer':inp['manual_review_display_only']['A'],
        'A_formal_start':None,'new_manual_answers_created':False,'formal_membership_from_date_coverage':None}
    counterexample={'earlier_G2_common':[str(lo),str(hi)],'later_G2_source_period':[new['path_start'],new['path_end']],
        'later_common_contains_earlier_common':True,'saved_closes_inside_old_common_during_later_source':close_visits,
        'later_source_rows':len(path),'confirmation_bar_first_separate_record':confirm,
        'meaning':'SAME_MANUAL_G2_CONTEXT_AND_GEOMETRIC_OVERLAP_DO_NOT_PROVE_PAIRWISE_RETEST_OR_FORMAL_MERGE'}
    write('source-facts.json',{'purpose':'PRESENT_DAY_SCOPE_REVIEW_NOT_SIGNAL_GENERATION','facts':facts,'manual_display_audit':manual_audit,'G2_counterexample':counterexample,
        'ABC_price_bridge':{'close_through':b2,'whole_range_below_next_saved_bar':b3,'outside_activity_available_on':'2025-06-12','formal_membership_extended':False},
        'formal_structure':None,'formal_parent':None,'formal_merge':None,'importance_score':None,'independent_confirmation_count':None,
        'historical_signal_eligible':False,'classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','actions_and_flywheel':'NOT_EVALUATED'})
    prov=json.loads((ROOT/'source-provenance.json').read_text())
    for r in prov['inputs']:assert hashlib.sha256(Path(r['local']).read_bytes()).hexdigest()==r['sha256']
    assert hashlib.sha256((ROOT/'study-inputs.json').read_bytes()).hexdigest()==prov['study_inputs_sha256']
    write('verification.json',{'status':'PASS_SOURCE_AUDIT_FOR_SEMANTIC_REVIEW','new_source_audit_runs':1,'existing_zone_raw_geometry_and_right_bar_checks':8,
        'manual_ABC39_G2_136_preserved':True,'post_ABC8_not_added_to_manual_members':True,
        'G2_geometric_overlap_no_source_close_visit_and_later_confirmation_distinct':True,'ABC_close_then_whole_range_then_completed_activity_separate':True,
        'listed_G2_missing_date_retained':True,'source_hashes_verified':7,'manual_label_passed_to_source_facts_function':False,
        'historical_classifier_or_prefix_simulation_performed':False,'old_drivers_verifiers_product_tests_rerun':0,'formal_merge_or_new_scope_rule_validated':False})
    print('PASS: 8 original activities; ABC39 + separate8, G2_136; geometric-overlap counterexample; 7 input hashes')
if __name__=='__main__':main()
