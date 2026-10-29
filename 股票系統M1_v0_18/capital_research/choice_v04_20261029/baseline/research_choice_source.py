"""Pure saved-choice/source consistency check, never selection or execution."""
from copy import deepcopy
from .lifecycle import FLAGS
from .research_choice import validate_record, bind_saved_source

SCHEMA = 'capital-research-choice-source-check/0.1'


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def check_saved(choice_value, explicit_source):
    """Check full declared bindings and exact membership of an existing snapshot."""
    out = dict(schema=SCHEMA, synthetic=True, check_status='REFUSED', reasons=[],
        mismatch_fields=[], choice_status=None, record_id=None, candidate_role=None,
        candidate_check=None, candidate_qualification=None, choice_summary=None,
        columns=[], scope='ONE_CHOICE_AND_ITS_EXPLICIT_SOURCE_NOT_POLICY_COMPARISON',
        order_generation='NOT_PERFORMED', execution='NOT_PERFORMED',
        execution_authorized=False, primary_pressure_id=None, **{k:False for k in FLAGS})
    try:
        c = validate_record(choice_value)['choice']
        out.update(choice_status=c['status'], record_id=c['record_id'])
        _require(c['source_binding'] is not None, 'CHOICE_SOURCE_BINDING_UNKNOWN')
        _require(isinstance(explicit_source, dict) and isinstance(explicit_source.get('adapter'), dict),
            'COMPLETE_EXPLICIT_SOURCE_WRAPPER_REQUIRED')
        binding = bind_saved_source(explicit_source)
        if c['source_binding'] != binding:
            declared = c['source_binding']
            out['mismatch_fields'] = sorted(k for k in set(declared) | set(binding)
                if k not in declared or k not in binding or declared[k] != binding[k])
            raise ValueError('SOURCE_BINDING_MISMATCH')
        snapshot = c['selected'] if c['selected'] is not None else c['rejected_candidate']
        role = 'SELECTED' if c['selected'] is not None else 'REJECTED_SNAPSHOT' if snapshot is not None else 'NONE'
        member = None
        if snapshot is not None:
            candidates = explicit_source['adapter']['generation']['research']['candidates']
            matches = [row for row in candidates if row['id'] == snapshot['id']]
            _require(len(matches) == 1, 'CANDIDATE_ID_NOT_UNIQUE')
            member = matches[0]
            _require(snapshot == member, 'CANDIDATE_SNAPSHOT_MISMATCH')
        out.update(check_status='MATCHED', candidate_role=role,
            candidate_check='EXACT_UNIQUE_MEMBER' if snapshot is not None else 'NO_SAVED_CANDIDATE',
            candidate_qualification=snapshot['classification'] if snapshot is not None else None,
            choice_summary=deepcopy({k:c[k] for k in ('requested_selection','recorded_at','reasons')}),
            columns=[dict(label='選擇紀錄保存值', binding=deepcopy(c['source_binding']), candidate=deepcopy(snapshot)),
                dict(label='明示來源保存值', binding=deepcopy(binding), candidate=deepcopy(member))])
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        out['reasons'] = [str(exc)]
    return out
