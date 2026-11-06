"""Four explicit paths, same source-bound information/model/account/time window."""
from copy import deepcopy
from ..cap1_20261104.compare import basis, FLAGS
from ..action_account_metrics import evaluate_saved
from ..saved_action_source import _action
from ..core import fingerprint
from . import basket
from .audit import audit


def compare(cases):
    out=dict(schema='cap1-four-account-actions/0.2',synthetic=True,status='REFUSED',reasons=[],branches={},**FLAGS)
    try:
        basket.require(set(cases)=={'hold','reduce','partial','cash'},'EXACT_FOUR_ACTIONS_REQUIRED')
        common=None;prefix=None;branches={}
        for name,case in cases.items():
            if name=='cash':
                receipt=case['receipt'];frames=basket.read_frames(receipt);m=basket.metrics(receipt,case['evaluation_at'])
                i=receipt['request']['seed_action_input'];spec=receipt['execution_spec'];run=receipt
                request={'saved_result':{'action_request':{'action_input':i,'execution_spec':spec},'continuation':None},'evaluation_at':case['evaluation_at']}
                b=basis(request);action=dict(kind='EXIT_ALL_TO_CASH',sales=receipt['request']['sales'])
            else:
                m=evaluate_saved(case);frames,_=_action(case['saved_result'])
                run=case['saved_result']['action_result']['run'];request=case
                b=basis(request);action=request['saved_result']['action_request']['action_input']['action']
                expected={'hold':'HOLD','reduce':'REDUCE_HOLDING','partial':'EXIT_SELLABLE_HOLDING'}[name]
                basket.require(action['kind']==expected,'WRONG_NAMED_ACTION_SCOPE')
            basket.require(m['status']=='EVALUATED','METRICS_REFUSED:'+name+':'+str(m['reasons']))
            basket.require(common is None or b==common,'SAME_ACCOUNT_INFORMATION_MODEL_AND_PERIOD_REQUIRED');common=b
            e=run['execution'];rows=e['ledger']['daily'];cutoff=b['information']['data_cutoff'][:10]
            prior=[r for r in rows if r['date']<=cutoff]
            basket.require(prior and (prefix is None or prior==prefix),'COMMON_PRE_DECISION_PREFIX_REQUIRED');prefix=prior
            branches[name]=dict(action=deepcopy(action),metrics=m,ledger=deepcopy(e['ledger']),fills=deepcopy(e['fills']),
                liquidation=audit(e),input_id=fingerprint(case),result_id=e['result_id'])
        out.update(status='COMPARABLE_SYNTHETIC_ACCOUNTS',common=deepcopy(common),basis_id=fingerprint(common),branches=branches)
    except (ValueError,KeyError,TypeError,IndexError,AttributeError,StopIteration) as exc:out['reasons']=[str(exc)]
    out['comparison_id']=fingerprint(out);return out
