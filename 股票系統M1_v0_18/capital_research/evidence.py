"""Read-only saved-layer adapter; never chooses a box, mode or trading rule."""
from copy import deepcopy
from graph_core.core import fingerprint
from manual_basis.core import validate_result
from .core import timestamp


def from_saved_layers(structure, reaction, manual, *, available_at, decision_at):
    """Explicit *observed* availability is required; date known_on is insufficient.

    Returns preserved evidence for layer 1. It deliberately does not create an
    entry-context, formal resistance, capital account or historical signal.
    """
    validate_result(manual)
    if manual['status'] != 'READY_SAVED_RESEARCH':
        raise ValueError('Saved manual mode/source unavailable; no Raw fallback')
    if timestamp(available_at) > timestamp(decision_at):
        raise ValueError('Saved layer not yet available')
    if timestamp(manual['intent']['selected_at']) > timestamp(available_at):
        raise ValueError('Manual selection occurred after declared availability')
    for obj, schema in ((structure,'p03-structure-state/0.1'),(reaction,'multi-reference-reaction-facts/0.1')):
        if obj['schema_version'] != schema or obj['result_id'] != fingerprint({k:v for k,v in obj.items() if k!='result_id'}):
            raise ValueError('Saved layer schema/fingerprint conflict')
        if obj['as_of'] != manual['binding']['as_of'] or obj['as_of'] > decision_at[:10]:
            raise ValueError('Saved as-of mismatch or future snapshot')
        for source_key, choice_key in [('code','code'),('source_id','source_id'),('price_basis_id','price_basis_id'),
                                       ('source_frame_id','frame_id'),('price_mode','price_mode'),('adjustment_version','adjustment_version')]:
            if obj['context'][source_key] != manual['binding'][choice_key]:
                raise ValueError('Saved manual/structure/reaction binding mismatch')
    if structure['original_reaction_result_id'] != reaction['result_id']:
        raise ValueError('Structure belongs to another reaction result')
    if not structure['records'] or not reaction['records']:
        raise ValueError('No saved evidence; never synthesize an event')
    return dict(schema='capital-saved-evidence/0.1',available_at=available_at,
        structure=deepcopy(structure),reaction=deepcopy(reaction),manual_basis=deepcopy(manual),
        formal_resistance=None,entry_qualification='NOT_EVALUATED',
        data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
        policy_authorized=False,live_execution_authorized=False)


def real_source_gate(data, catalog):
    """Retain the formal 0.10 -> 0.4 rejection chain; no numeric replay route."""
    from rotation_research.subsidiary_proposal import qualify
    result=qualify(data,catalog)
    return dict(schema='capital-real-source-gate/0.1',qualification=deepcopy(result),
                research_recommendation='REFUSED_PENDING_SOURCE_QUALIFICATION',
                data_qualified=False,execution_model_qualified=False,historical_signal_eligible=False,
                policy_authorized=False,live_execution_authorized=False)
