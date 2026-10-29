"""Read complete saved action receipts; share metrics, never replay the book.

Structural consistency is not source authentication, strategy requalification,
or independent verification of every historical fill/accounting entry.
"""
from copy import deepcopy
from decimal import Context, InvalidOperation, DivisionByZero, Overflow, ROUND_HALF_EVEN, localcontext
from . import account_metrics as metrics
from .lifecycle import _fp, _time, _snapshot, _chain, _account, _signed, _require, FLAGS, TERMINAL
from .fact_lineage import history_at, source_snapshot
from .reassessment_history import declaration_sources, validate_request_binding

INPUT='capital-action-account-metrics-input/0.1'
SCHEMA='capital-action-account-metrics/0.1'
SOURCE='capital-saved-action-source/0.1'


from .saved_action_source import _research, _close, _pair, _account_binding, _action, _continuation, _snapshots


def evaluate_saved(request):
    """Pure bounded READ of saved identities and curves; no producer calls."""
    out=dict(schema=SCHEMA,synthetic=True,status='REFUSED',reasons=[],statistics=None,account=None,source=None,costs=None,
        initial_capital=None,terminal_accrual_equity=None,terminal_net_equity=None,terminal_net_growth=None,
        valuation_basis=metrics.BASIS,validation_scope='SAVED_ACTION_BINDINGS_AND_CURVE_CHECKS_NOT_REPLAY_OR_SOURCE_AUTHENTICATION',
        ranking=None,selected_strategy=None,strategy_validated=False,primary_pressure_id=None,**{k:False for k in FLAGS})
    try:
        with localcontext(Context(prec=50,rounding=ROUND_HALF_EVEN,Emin=-999999,Emax=999999,
                capitals=1,clamp=0,flags=[],traps=[InvalidOperation,DivisionByZero,Overflow])):
            _require(isinstance(request,dict) and set(request)=={'schema','synthetic','evaluation_at','saved_result'}
                and request['schema']==INPUT and request['synthetic'] is True,'EXPLICIT_SAVED_ACTION_METRICS_REQUIRED')
            frames,summary=_snapshots(request['saved_result'])
            out.update(metrics._evaluate_snapshots(request,frames,summary));out['status']='EVALUATED'
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,StopIteration,InvalidOperation,OverflowError) as exc:
        out['reasons']=[dict(reason=str(exc),path=getattr(exc,'path',''),classification='SAVED_ACTION_OR_REQUIRED_VALUE_NOT_SUPPORTED')]
    out['evaluation_id']=_fp(out)
    return out
