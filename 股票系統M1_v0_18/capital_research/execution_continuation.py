"""Continue only an original synthetic order runtime, through the original ledger.

Historical reconstruction verifies the supplied checkpoint. Only the tail uses
the rebuilt runtime; it creates neither a decision nor a new order.
"""
from copy import deepcopy
from decimal import Context, InvalidOperation, DivisionByZero, Overflow, ROUND_HALF_EVEN, localcontext

from graph_core.core import fingerprint
from .core import timestamp
from .close_clock import close_record
from .continuity import validate_checkpoint, make_checkpoint
from .execution import _simulate

VERSION = 'capital-standing-order-resume/0.1'
INPUT = 'capital-standing-order-resume-input/0.1'
_FIELDS = {'schema', 'synthetic', 'root_job', 'checkpoint', 'expected_checkpoint_id',
           'expected_latest_decision_id', 'path', 'expected_path_id', 'segment_tape',
           'observed_until', 'resume_at'}


def _context():
    return Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
                   capitals=1, clamp=0, flags=[], traps=[InvalidOperation, DivisionByZero, Overflow])


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _capture_original(job):
    """Private validation/control hook; never a second posting engine."""
    with localcontext(_context()):
        trace, frame = [], {}
        execution = _simulate(job, _trace=trace, _capture=frame)
        return execution, trace, frame


def _validate(request):
    _require(set(request) == _FIELDS and request['schema'] == INPUT and request['synthetic'] is True,
             'EXACT_STANDING_CONTINUATION_REQUIRED')
    j, cp, path = request['root_job'], request['checkpoint'], request['path']
    _require(request['expected_checkpoint_id'] == cp['checkpoint_id'] and
             request['expected_latest_decision_id'] == cp['execution_result']['latest_decision_id'],
             'EXACT_LATEST_PREDECESSOR_REQUIRED')
    origin = cp['origin_ledger_input']
    _require(j['ledger_input'] == origin and path['origin_ledger_input_id'] == fingerprint(origin),
             'ORIGIN_LEDGER_BINDING_REQUIRED')
    validate_checkpoint(cp)
    _require(j['ledger_close_proof'] == cp['execution_result']['ledger_close_proof'],
             'ORIGINAL_CLOSE_PROOF_REQUIRED')
    _require(set(path) == {'schema', 'version', 'qualification', 'source_ids', 'origin_ledger_input_id',
                          'start_at', 'through_at', 'observations', 'session_coverage'} and
             path['schema'] == 'capital-synthetic-order-path/0.1' and
             path['version'] == 'frozen-synthetic-path/0.1' and
             path['qualification'] == 'EXPLICIT_SYNTHETIC_COMPLETE_PATH_NOT_MARKET_PROOF' and
             request['expected_path_id'] == fingerprint(path), 'COMPLETE_PATH_BINDING_REQUIRED')

    def bound_sources(ids):
        return bool(ids) and len(ids) == len(set(ids)) and all(
            s in origin['sources'] and origin['sources'][s]['kind'] ==
            'ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in ids)

    _require(bound_sources(path['source_ids']) and all(s['kind'] ==
             'ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET' for s in origin['sources'].values()),
             'BOUND_SYNTHETIC_PATH_SOURCE_REQUIRED')
    _require(j['tape'] == path['observations'] and path['start_at'] == j['decision_input']['data_cutoff'] and
             path['through_at'] == j['observed_until'], 'ROOT_JOB_PATH_BINDING_REQUIRED')
    times = [timestamp(o['at']) for o in path['observations']]
    _require(times == sorted(set(times)) and all(timestamp(path['start_at']) < t <=
             timestamp(path['through_at']) for t in times), 'DUPLICATE_OR_UNORDERED_PATH_OBSERVATIONS')
    days = [r['date'] for r in origin['calendar'] if r['trading'] and
            path['start_at'][:10] < r['date'] <= path['through_at'][:10]]
    coverage = path['session_coverage']
    _require([r['date'] for r in coverage] == days and all(
        set(r) == {'date', 'source_ids', 'qualification', 'observation_ids', 'no_other_execution_opportunities'} and
        bound_sources(r['source_ids']) and r['qualification'] ==
        'EXPLICIT_SYNTHETIC_COMPLETE_EXECUTION_OPPORTUNITIES' and r['no_other_execution_opportunities'] is True and
        r['observation_ids'] == [fingerprint(o) for o in path['observations'] if o['at'][:10] == r['date']]
        for r in coverage) and all(o['at'][:10] in days for o in path['observations']),
        'COMPLETE_SESSION_COVERAGE_REQUIRED')
    cut, end = cp['state']['through_at'], request['observed_until']
    _require(timestamp(cut) < timestamp(end) <= timestamp(path['through_at']) and
             origin['start'] < end[:10] <= origin['end'], 'IN_WINDOW_ADVANCING_WATERMARK_REQUIRED')
    close_record(origin, j['ledger_close_proof'], end)
    _require(timestamp(request['resume_at']) >= timestamp(cut) and
             timestamp(request['resume_at']) >= timestamp(cp['state']['ledger_close']['available_at']),
             'CHECKPOINT_NOT_YET_KNOWN')
    remaining = [o for o in path['observations'] if timestamp(o['at']) > timestamp(cut)]
    _require(timestamp(request['resume_at']) <= timestamp(end) and (not remaining or
             timestamp(request['resume_at']) <= timestamp(remaining[0]['at'])), 'NO_SKIPPED_EXECUTION_INTERVAL')
    tail = [o for o in remaining if timestamp(o['at']) <= timestamp(end)]
    _require(request['segment_tape'] == tail, 'SEGMENT_TAPE_MUST_MATCH_COMPLETE_PATH')
    _require(all(timestamp(r['decision_input']['decision_at']) <= timestamp(cut)
                 for r in j.get('reassessments', [])), 'NEW_REASSESSMENT_NOT_IMPLEMENTED')
    received = {a['id']: a['request'] for a in cp['execution_result']['reassessment_attempts']}
    _require(all(received.get(r['id']) == r for r in j.get('reassessments', [])),
             'UNRECEIVED_REASSESSMENT_NOT_IMPLEMENTED')
    return j, cp, cut, tail


def resume_orders(request):
    """Pure bounded RUN. Fail closed before the tail on unverified history."""
    with localcontext(_context()):
        trace = []
        tail_started = False
        try:
            j, cp, cut, tail = _validate(request)
            prefix = deepcopy(j)
            prefix['tape'] = [o for o in j['tape'] if timestamp(o['at']) <= timestamp(cut)]
            prefix['observed_until'] = cut
            rebuilt, prefix_trace, frame = _capture_original(prefix)
            _require(rebuilt == cp['execution_result'], 'PREFIX_EXECUTION_MISMATCH')
            job = deepcopy(j)
            job.update(tape=deepcopy(tail), observed_until=request['observed_until'])
            tail_started = True
            execution = _simulate(job, _carry=frame, _trace=trace)
            checkpoint = make_checkpoint(j['ledger_input'], execution, through_at=request['observed_until'])
            out = dict(schema=VERSION, status='CONTINUED_ORIGINAL_ORDERS', synthetic=True,
                execution=execution, checkpoint=checkpoint, observation_trace=trace,
                prefix_observation_trace=prefix_trace,
                new_fill_ids_this_segment=[f['id'] for f in execution['fills'][len(rebuilt['fills']):]],
                history_reconstruction_observations=len(prefix['tape']), tail_observations_processed=len(tail),
                integrity=dict(root_job_id=fingerprint(j), path_id=request['expected_path_id'],
                    predecessor_checkpoint_id=cp['checkpoint_id'], predecessor_latest_id=request['expected_latest_decision_id']),
                data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
                policy_authorized=False, live_execution_authorized=False)
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            out = dict(schema=VERSION, status='REFUSED', refusal_reasons=[str(exc)],
                       execution=None, checkpoint=None, tail_observations_processed=len(trace),
                       tail_processing_started=tail_started,
                       data_qualified=False, execution_model_qualified=False, historical_signal_eligible=False,
                       policy_authorized=False, live_execution_authorized=False)
        out['result_id'] = fingerprint(out)
        return out
