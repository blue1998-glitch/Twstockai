"""Explicit new synthetic inputs. No old producer is run."""
from copy import deepcopy
import json
from pathlib import Path

ROOT=Path(__file__).parent
CAPITAL=ROOT.parent


def cases():
    base=json.loads((CAPITAL/'conditional_quantity_review_20261026/cases/valid-old-fact/input.json').read_text())
    base['schema']='capital-conditional-quantity-review-input/0.2'
    base['replay_input']['initial_account']['holdings']['B']=dict(shares='5',sellable='5')
    base['replay_input']['origin_ledger']['opening']['shares']['B']='5'
    f=base['replay_input']['rounds'][0];f['quantity_template']['batch_context']['phase']='ADDITIONAL_BATCH';f['quantity_template']['trigger_ids']=['B-event']
    used=['fixture:event_id:B-prior-approved','fixture:formation_id:B-prior-formation','fixture:volume_bar_id:B-prior-bar']
    f['decision_template']['consumed_evidence_tokens']=used
    base['review']['decision_template']['consumed_evidence_tokens']=deepcopy(used)
    out={}
    def add(name,data,**expected):out[name]=dict(input=data,expected=expected)
    add('valid-C-same-order',base,status='REPLAYED_ACCEPTED_REVIEW',B_filled='20',remaining='0',family='C',new_tokens=[],capital='1430')
    x=deepcopy(base);x['replay_input']['rounds'][0]['tape'][-1]['capacity_shares']='7'
    add('partial-C-same-order',x,status='REPLAYED_ACCEPTED_REVIEW',B_filled='7',remaining='13',family='C',new_tokens=[],capital='1430')
    x=deepcopy(base);x['review']['decision_template']['assets']['B']['capital_eligibility']['status']='UNKNOWN'
    add('unknown-current-eligibility',x,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',family='C',capital='1430')
    x=deepcopy(base);d=x['review']['decision_template'];e=d['assets']['B']['evidence'][0]
    e['validity']['invalidation']=dict(evidence_id='C-order-revocation',occurred_at=d['data_cutoff'],available_at=d['data_cutoff'],source_ids=['fixture'])
    add('revoked-trigger',x,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',family='C',capital='1430',order_status='CANCELLED_EVIDENCE')
    x=deepcopy(base);e=x['review']['decision_template']['assets']['B']['evidence'][0];e['value']='CONFLICT_NOT_A_SOURCE_CORRECTION';e['validity']['valid_until']='2026-01-10T16:00:00+08:00'
    add('rejected-conflict-retained',x,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',family='C',capital='1430',order_status='CANCELLED_EVIDENCE')
    x=deepcopy(base);x['review']['order_id']='changed-order-id'
    add('wrong-order-id',x,status='STOPPED_INPUT_ERROR',reason='OWN_LAST_ROUND_CONDITIONAL_ORDER_REQUIRED')
    x=deepcopy(base);x['review']['decision_template']['assets']['B']['basis_id']='Adjusted:foreign'
    add('wrong-basis',x,status='STOPPED_INPUT_ERROR',reason='REVIEW_SOURCE_BASIS_OR_COST_CHANGED')
    x=deepcopy(base);x['schema']='capital-conditional-quantity-review-input/0.1'
    add('old-wrapper-keeps-C-unsupported',x,status='STOPPED_NOT_IMPLEMENTED',reason='ORIGINAL_FAMILY_CONTINUATION_NOT_IMPLEMENTED')
    x=deepcopy(base);x['review']['decision_template']['risk_limits']['single_name_value']['B']='100'
    add('current-risk-limit',x,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',family='C',capital='1430')
    x=deepcopy(base);x['review']['policy']['edge_budget']='0'
    add('current-cost-band',x,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',family='C',capital='1430')
    x=deepcopy(base);d=x['review']['decision_template'];d.update(data_cutoff='2026-01-06T16:00:00+08:00',decision_at='2026-01-06T17:00:00+08:00')
    for a in d['assets'].values():
        a['marks'][0].update(occurred_at=d['data_cutoff'],available_at=d['data_cutoff'])
        a['capital_eligibility'].update(data_cutoff=d['data_cutoff'],assessed_at=d['decision_at'],available_at=d['decision_at'])
    x['review']['policy']['available_at']=d['decision_at']
    add('sale-still-unsettled',x,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',family='C',capital='1430')
    x=deepcopy(base);x['replay_input']['rounds'][0]['tape'][-1]['market_state']='LIMIT_UP_NO_BUY'
    add('valid-review-but-limit-up',x,status='REPLAYED_ACCEPTED_REVIEW',B_filled='0',remaining='20',family='C',new_tokens=[],capital='1430',order_status='OPEN')
    x=deepcopy(base);x['review']['decision_template']['assets']['B']['evidence'][0]['validity']['invalidation']=dict(evidence_id='future-C-revocation',occurred_at='2026-01-12T09:01:00+08:00',available_at='2026-01-12T09:01:00+08:00',source_ids=['fixture'])
    add('future-revocation-prefix',x,status='REPLAYED_ACCEPTED_REVIEW',B_filled='20',remaining='0',family='C',new_tokens=[],capital='1430',same_numeric_as='valid-C-same-order')
    return out


GATEWAY={
 'oversize':(dict(path=['plans',0,'targets','B'],value='26'),'SAME_ORDER_TARGET_OR_QUANTITY_CHANGED'),
 'change-family':(dict(path=['plans',0,'family'],value='E'),'SAME_ORDER_PLAN_OR_TRIGGER_CHANGED'),
 'change-trigger':(dict(path=['plans',0,'trigger_ids'],value=['B-alias']),'SAME_ORDER_PLAN_OR_TRIGGER_CHANGED'),
 'wrong-account':(dict(path=['account','settled_cash'],value='9999'),'Next account/cutoff'),
 'wrong-predecessor':(dict(target='previous',path=['decision','decision_id'],value='sha256:wrong'),'Invalid saved predecessor'),
 'wrong-checkpoint':(dict(target='checkpoint',path=['checkpoint_id'],value='sha256:wrong'),'Checkpoint differs'),
 'wrong-scope-order':(dict(target='order_id',value='r1-A'),'SAME_ORDER_CONDITIONAL_BUY_REQUIRED')}
