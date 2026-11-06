"""Pure comparison boundary over original complete saved-action receipts.

No orders, fills, valuation, return or drawdown calculations here. The original
metrics reader verifies each source; exact common-input equality verifies scope.
Structural consistency does not authenticate a real investor or market source.
"""
from copy import deepcopy
from ..action_account_metrics import evaluate_saved
from ..core import fingerprint

FLAGS = dict(execution_qualified=False, historical_signal_eligible=False,
             policy_authorized=False, primary_pressure_id=None,
             imputed_close=None, valuation=None, ranking=None, strategy_validated=False)


def basis(request):
    saved = request['saved_result']
    if saved['continuation'] is not None:
        raise ValueError('CONTINUATION_COMPARISON_NOT_IMPLEMENTED')
    r = saved['action_request']; i = r['action_input']; s = r['execution_spec']
    return dict(account=i['account_source'], information=i['decision_template'],
                policy=i['policy'], origin=s['origin_ledger'], close=s['ledger_close_proof'],
                tape=s['tape'], observed_until=s['observed_until'],
                evaluation_at=request['evaluation_at'])


def compare(cases):
    """Read-only: refuse the entire comparison on any incomplete/mixed branch."""
    out = dict(schema='capital-action-comparison/0.1', synthetic=True,
               status='REFUSED', reasons=[], basis_id=None, branches={}, **FLAGS)
    try:
        if not isinstance(cases, dict) or not 2 <= len(cases) <= 3:
            raise ValueError('TWO_OR_THREE_EXPLICIT_ACTIONS_REQUIRED')
        common = None; prefix = None; actions = set()
        branches = {}
        for name, request in cases.items():
            m = evaluate_saved(request)
            if m['status'] != 'EVALUATED':
                raise ValueError('METRICS_REFUSED:' + name + ':' + str(m['reasons']))
            b = basis(request)
            if common is not None and b != common:
                raise ValueError('SAME_ACCOUNT_INFORMATION_MODEL_AND_TIMELINE_REQUIRED')
            common = b
            saved = request['saved_result']; r = saved['action_request']
            run = saved['action_result']['run']; action = r['action_input']['action']
            kind = action['kind']
            if kind not in ('HOLD', 'REDUCE_HOLDING', 'EXIT_SELLABLE_HOLDING') or kind in actions:
                raise ValueError('DISTINCT_SUPPORTED_EXPLICIT_ACTIONS_REQUIRED')
            actions.add(kind)
            # Only the post-decision intent/order may differ. No edited old ledger.
            ledger = run['execution']['ledger']
            cutoff = b['information']['data_cutoff'][:10]
            pre = [row for row in ledger['daily'] if row['date'] <= cutoff]
            if not pre or (prefix is not None and prefix != pre):
                raise ValueError('PRE_DECISION_ACCOUNT_PREFIX_CONFLICT')
            prefix = pre
            branches[name] = dict(action=deepcopy(action), metrics=m,
                ledger=deepcopy(ledger), fills=deepcopy(run['execution']['fills']),
                input_id=fingerprint(request), result_id=run['execution']['result_id'])
        out.update(status='COMPARABLE_SYNTHETIC_ACCOUNTS', basis_id=fingerprint(common),
                   common=deepcopy(common), branches=branches)
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as e:
        out['reasons'] = [str(e)]
    out['comparison_id'] = fingerprint(out)
    return out
