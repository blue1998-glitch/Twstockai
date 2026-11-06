"""B review evidence and two human-readable alternatives; no merge classifier."""
import copy,hashlib,json,os
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
def write(name,x):(ROOT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def project(source,c,cut):
    bs=[b for b in source['bars']if b['date']<=cut];last=bs[-1]
    out={'cutoff':cut,'current_bar':last,'activities':{},'joint_source_audit':None,'manual_B_structure_label':None,
         'formal_merge':None,'formal_parent':None,'formal_start':None,'formal_end':None,'formal_price_bounds':None,
         'user_decision':'PENDING_NEW_CORE_REVIEW','historical_signal_eligible':False,
         'classifier':'NOT_VALIDATED','Android':'NOT_TESTED_NEW_BUILD','actions_and_flywheel':'NOT_EVALUATED'}
    for key,z in c['zones'].items():
        if z['known_on_saved_bar']>cut:out['activities'][key]=None;continue
        rows=[b for b in bs if z['path_start']<=b['date']<=z['path_end']]
        assert len(rows)==z['raw_path_frame']['records']and min(D(b['low'])for b in rows)==D(z['raw_path_frame']['observed_low'])and max(D(b['high'])for b in rows)==D(z['raw_path_frame']['observed_high'])
        lo,hi=D(z['common_close_low']),D(z['common_close_high']);cl=D(last['close'])
        out['activities'][key]={'zone':copy.deepcopy(z),'current_close_side_of_common':'BELOW'if cl<lo else'ABOVE'if cl>hi else'AT_LOW'if cl==lo else'AT_HIGH'if cl==hi else'INSIDE',
            'current_daily_range_intersects_common':D(last['low'])<=hi and D(last['high'])>=lo}
    if all(out['activities'][key]is not None for key in ['upper','lower']):
        a,b=c['zones']['upper'],c['zones']['lower'];ids=set(a['leg_ids'])|set(b['leg_ids']);legs=[c['legs'][i]for i in ids]
        lo=max(D(l['close_low'])for l in legs);hi=min(D(l['close_high'])for l in legs)
        rows=[x for x in bs if min(a['path_start'],b['path_start'])<=x['date']<=max(a['path_end'],b['path_end'])]
        overlap=[x['date']for x in bs if max(a['path_start'],b['path_start'])<=x['date']<=min(a['path_end'],b['path_end'])]
        oldlo,oldhi=D(a['common_close_low']),D(a['common_close_high'])
        between=[x for x in bs if a['path_end']<x['date']<=cut]
        out['joint_source_audit']={'shared_leg_ids':sorted(set(a['leg_ids'])&set(b['leg_ids'])),
            'shared_source_dates':overlap,'distinct_leg_ids':sorted(ids),'unique_source_rows':len(rows),'union_source_period':[rows[0]['date'],rows[-1]['date']],
            'raw_union':[str(min(D(x['low'])for x in rows)),str(max(D(x['high'])for x in rows))],
            'all_distinct_leg_common_intersection':[str(lo),str(hi)]if lo<=hi else None,
            'common_intersection_empty':lo>hi,'empty_intersection_is_formal_merge_veto':False,
            'closes_after_upper_source_end_returned_to_upper_common':[x for x in between if oldlo<=D(x['close'])<=oldhi],
            'current_wick_intersects_upper_common':D(last['low'])<=oldhi and D(last['high'])>=oldlo,
            'independent_confirmation_count':None,'formal_merge_inferred_from_shared_leg':False}
    return out
def main():
    s=json.loads(SOURCE.read_text());c=json.loads((ROOT/'study-inputs.json').read_text());views={cut:project(s,c,cut)for cut in c['cutoffs']}
    for cut,r in views.items():
        prefix=copy.deepcopy(s);prefix['bars']=[b for b in prefix['bars']if b['date']<=cut];assert project(prefix,c,cut)==r
        poison=copy.deepcopy(s);poison['manual_B_structure_label']='FORBIDDEN_LABEL'
        for b in poison['bars']:
            if b['date']>cut:b.update(open='999',high='999',low='-999',close='999',volume_shares_scaled='9999999999')
        assert project(poison,c,cut)==r
        cc=copy.deepcopy(c)
        for z in cc['zones'].values():
            if z['known_on_saved_bar']>cut:z.update(path_start='1900-01-01',path_end='2099-01-01',common_close_low='-999',common_close_high='999',leg_ids=['FUTURE'])
        assert project(s,cc,cut)==r
        assert r['formal_merge']is None and r['manual_B_structure_label']is None and r['user_decision']=='PENDING_NEW_CORE_REVIEW'
    assert views['2026-04-23']['activities']['upper']is None
    assert views['2026-04-24']['activities']['upper']is not None and views['2026-04-27']['activities']['lower']is None
    r=views['2026-04-28'];u=r['joint_source_audit']
    assert len(u['shared_leg_ids'])==1 and len(u['distinct_leg_ids'])==4 and u['shared_source_dates']==['2026-04-22','2026-04-23']
    assert u['unique_source_rows']==8 and list(map(D,u['raw_union']))==[D('32.00'),D('33.20')]
    assert u['common_intersection_empty']and not u['closes_after_upper_source_end_returned_to_upper_common']
    assert r['current_bar']['high']=='32.95'and r['current_bar']['close']=='32.45'and u['current_wick_intersects_upper_common']
    assert r['activities']['upper']['current_close_side_of_common']=='BELOW'and r['activities']['lower']['current_close_side_of_common']=='AT_LOW'
    # Independent span check against the original legs, retaining their exact source IDs.
    for z in c['zones'].values():
        ls=[c['legs'][i]for i in z['leg_ids']]
        assert max(D(l['close_low'])for l in ls)==D(z['common_close_low'])and min(D(l['close_high'])for l in ls)==D(z['common_close_high'])
    prov=json.loads((ROOT/'source-provenance.json').read_text())
    for x in prov['inputs']:assert hashlib.sha256(Path(x['local']).read_bytes()).hexdigest()==x['sha256']
    assert hashlib.sha256((ROOT/'study-inputs.json').read_bytes()).hexdigest()==prov['selection_sha256']
    write('evidence-views.json',views)
    write('verification.json',{'status':'PASS_B_REVIEW_EVIDENCE_ONLY','new_source_audit_runs':1,'cutoff_views':4,'prefix_future_price_volume_manual_and_unavailable_geometry_isolation':4,'original_local_source_and_leg_geometry_checks':2,'shared_leg_dedup_and_eight_unique_source_rows':'PASS','upper_close_nonreturn_vs_current_wick_return_distinguished':'PASS','empty_common_not_used_as_universal_merge_veto':True,'manual_B_label_and_formal_merge_not_created':True,'source_hashes_verified':4,'old_drivers_verifiers_product_tests_rerun':0,'formal_merge_rule_validated':False})
    print('PASS: 4 cutoff views; 1 shared leg deduplicated, 4 distinct legs, 8 source bars; new decision pending')
if __name__=='__main__':main()
