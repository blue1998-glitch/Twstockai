"""Strict change boundary for the volume-origin wording revision."""
from copy import deepcopy
from contracts import fingerprint
from structure import VOLUME_PRECISION,VERSION


def precision_fields(value,path=''):
    fields={}
    if isinstance(value,dict):
        for k,v in value.items():
            p=path+'/'+k
            if k=='volume_precision':fields[p]=v
            else:fields.update(precision_fields(v,p))
    elif isinstance(value,list):
        for i,v in enumerate(value):fields.update(precision_fields(v,path+'/'+str(i)))
    return fields


def strip_structure_identity(value):
    if isinstance(value,dict):
        return {k:strip_structure_identity(v) for k,v in value.items() if k not in {'snapshot_id','event_id','rule_version','volume_precision'}}
    if isinstance(value,list):return [strip_structure_identity(v) for v in value]
    return value


def compare_results(old,new,unit):
    a=old['components']['structure'];b=new['components']['structure']
    assert a['rule_version']=='structure-0.2-research' and b['rule_version']==VERSION
    assert new['component_versions']==dict(old['component_versions'],structure=VERSION)
    assert old['analysis_id']!=new['analysis_id']
    assert old['components']['daily_ma']==new['components']['daily_ma']
    assert {k:v for k,v in old.items() if k not in {'analysis_id','component_versions','components','aligned_snapshots'}}=={k:v for k,v in new.items() if k not in {'analysis_id','component_versions','components','aligned_snapshots'}}
    assert b['volume_unit']==unit
    assert all(s['volume_unit']==unit and s['rule_version']==VERSION for s in b['snapshots'])
    old_precision=precision_fields(a);new_precision=precision_fields(b)
    assert old_precision and old_precision.keys()==new_precision.keys()
    assert set(old_precision.values())=={'Source lots scaled to shares; display precision retained'}
    assert set(new_precision.values())=={VOLUME_PRECISION[unit]}
    before=deepcopy(a);after=deepcopy(b);after.pop('volume_unit')
    for s in after['snapshots']:s.pop('volume_unit')
    # Keep candidate IDs, every price/ratio/date/state, parameters, source and
    # all quality fields. Only version-derived identities and wording omitted.
    normalized_before=strip_structure_identity(before);normalized_after=strip_structure_identity(after)
    assert normalized_before==normalized_after
    assert len(a['snapshots'])==len(b['snapshots'])
    changed_ids={}
    for x,y,old_join,new_join in zip(a['snapshots'],b['snapshots'],old['aligned_snapshots'],new['aligned_snapshots']):
        assert x['snapshot_id']!=y['snapshot_id'];changed_ids[x['snapshot_id']]=y['snapshot_id']
        assert new_join['structure_snapshot_id']==y['snapshot_id']
        assert old_join['snapshot_id']!=new_join['snapshot_id']
        assert {k:v for k,v in old_join.items() if k not in {'snapshot_id','structure_snapshot_id'}}=={k:v for k,v in new_join.items() if k not in {'snapshot_id','structure_snapshot_id'}}
    assert len(a['event_ledger'])==len(b['event_ledger'])
    for x,y in zip(a['event_ledger'],b['event_ledger']):
        assert y['snapshot_id']==changed_ids[x['snapshot_id']]
        assert y['event_id']==y['snapshot_id']+':'+x['event_id'].rsplit(':',1)[1]
        assert y['rule_version']==VERSION
    return dict(code=old['shared_input']['code'],price_mode=old['shared_input']['price_mode'],volume_unit=unit,
                snapshots=len(b['snapshots']),precision_occurrences=len(new_precision),
                old_analysis_id=old['analysis_id'],new_analysis_id=new['analysis_id'],
                old_result_fingerprint=fingerprint(old),new_result_fingerprint=fingerprint(new),
                normalized_structure_fingerprint=fingerprint(normalized_after),all_numeric_dates_states_equal=True,
                complete_ma_component_equal=True,source_and_parameters_equal=True,new_snapshot_identities_distinct=True,
                old_precision=next(iter(old_precision.values())),new_precision=VOLUME_PRECISION[unit])
