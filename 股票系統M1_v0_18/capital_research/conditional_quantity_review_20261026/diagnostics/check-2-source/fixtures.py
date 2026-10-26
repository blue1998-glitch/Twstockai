"""New explicit synthetic inputs; load saved originals without old producers."""
from copy import deepcopy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def positive():
    replay=json.loads((ROOT/'quantity_replay_20261026/cases/settled-not-reapproved/input.json').read_text())
    f=replay['rounds'][-1]
    d=deepcopy(f['decision_template'])
    d.update(data_cutoff='2026-01-08T16:00:00+08:00',decision_at='2026-01-08T17:00:00+08:00')
    for a in d['assets'].values():
        m=deepcopy(a['marks'][0]);m.update(occurred_at=d['data_cutoff'],available_at=d['data_cutoff']);a['marks']=[m]
        a['capital_eligibility'].update(data_cutoff=d['data_cutoff'],assessed_at=d['decision_at'],available_at=d['decision_at'])
    policy=deepcopy(f['quantity_template']['policy']);policy['available_at']=d['decision_at']
    return dict(schema='capital-conditional-quantity-review-input/0.1',synthetic=True,replay_input=replay,
                review=dict(id='same-order-current-review',order_id='r1-B',decision_template=d,policy=policy))


def cases():
    out={}
    def add(name,r,**expected):out[name]=dict(input=r,expected=expected)
    r=positive()
    add('valid-old-fact',r,status='REPLAYED_ACCEPTED_REVIEW',B_filled='20',remaining='0',attempt='ACCEPTED',new_tokens=[])
    r=positive();r['replay_input']['rounds'][0]['tape'][-1]['capacity_shares']='7'
    add('partial-original-order',r,status='REPLAYED_ACCEPTED_REVIEW',B_filled='7',remaining='13',attempt='ACCEPTED',new_tokens=[])
    r=positive();d=r['review']['decision_template'];fact=d['assets']['B']['evidence'][0]
    fact['validity']['invalidation']=dict(evidence_id='review-revocation',occurred_at=d['data_cutoff'],available_at=d['data_cutoff'],source_ids=['fixture'])
    add('rejected-restriction-retained',r,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',attempt='REJECTED',order_status='CANCELLED_EVIDENCE')
    r=positive();r['review']['decision_template']['assets']['B']['capital_eligibility']['status']='UNKNOWN'
    add('unknown-current-qualification',r,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',attempt='REJECTED')
    r=positive();d=r['review']['decision_template'];d.update(data_cutoff='2026-01-06T16:00:00+08:00',decision_at='2026-01-06T17:00:00+08:00')
    for a in d['assets'].values():
        a['marks'][0].update(occurred_at=d['data_cutoff'],available_at=d['data_cutoff'])
        a['capital_eligibility'].update(data_cutoff=d['data_cutoff'],assessed_at=d['decision_at'],available_at=d['decision_at'])
    r['review']['policy']['available_at']=d['decision_at']
    add('sale-unsettled',r,status='REPLAYED_REJECTED_REVIEW',B_filled='0',remaining='20',attempt='REJECTED')
    r=positive();r['review']['order_id']='forged-B'
    add('unknown-order-refused',r,status='STOPPED_INPUT_ERROR',reason='OWN_LAST_ROUND_CONDITIONAL_ORDER_REQUIRED')
    r=positive();r['review']['decision_template']['plans']=[dict(id='forged-extra',targets=dict(B='999'))]
    add('target-injection-refused',r,status='STOPPED_INPUT_ERROR',reason='TEMPLATE_ACCOUNT_OR_PLANS_FORBIDDEN')
    r=positive();r['review']['decision_template']['assets']['B']['basis_id']='Adjusted:forged'
    add('basis-change-refused',r,status='STOPPED_INPUT_ERROR',reason='REVIEW_SOURCE_BASIS_OR_COST_CHANGED')
    r=positive();r['replay_input']['rounds'][0]['quantity_template']['batch_context']['phase']='UNKNOWN'
    add('outer-gate-refused',r,status='STOPPED_ORIGINAL_GATE',reason='BATCH_PHASE_UNKNOWN')
    r=positive();orders=r['replay_input']['rounds'][0]['orders'];orders[1]['shares']='10';second=deepcopy(orders[1]);second['id']='r1-B-other';orders.append(second)
    add('multiple-live-orders-unsupported',r,status='STOPPED_NOT_IMPLEMENTED',reason='SINGLE_OWN_CONDITIONAL_BUY_ONLY')
    r=positive();r['replay_input']['rounds'][0]['tape'][-1]['market_state']='LIMIT_UP_NO_BUY'
    add('limit-up-after-review',r,status='REPLAYED_ACCEPTED_REVIEW',B_filled='0',remaining='20',attempt='ACCEPTED',order_status='OPEN')
    r=positive();r['replay_input']['ledger_close_proof']['closes']['2026-01-08']['available_at']='2026-01-08T17:30:00+08:00'
    add('close-not-yet-known',r,status='STOPPED_INPUT_ERROR',reason='LEDGER_CLOSE_NOT_YET_AVAILABLE')
    for name,prices in [('future-A-wins',('100','1')),('future-B-wins',('1','100')),('future-both-fall',('1','1'))]:
        r=positive()
        for c,p in zip(('A','B'),prices):r['replay_input']['origin_ledger']['assets'][c]['quotes']['2026-01-12']=p
        add(name,r,status='REPLAYED_ACCEPTED_REVIEW',B_filled='20',remaining='0',attempt='ACCEPTED',same_numeric_as='valid-old-fact')
    r=positive();f=r['replay_input']['rounds'][0];f['tape'][-1]['capacity_shares']='7'
    fact=r['review']['decision_template']['assets']['B']['evidence'][0]
    fact['validity']['invalidation']=dict(evidence_id='future-revocation',occurred_at='2026-01-12T09:01:00+08:00',available_at='2026-01-12T09:01:00+08:00',source_ids=['fixture'])
    for o in deepcopy(f['tape'][-3:]):
        o.update(at=o['at'].replace('01-09','01-12'),available_at=o['available_at'].replace('01-09','01-12'),capacity_shares='20' if o['code']=='B' else '0');f['tape'].append(o)
    f['observed_until']='2026-01-12T16:00:00+08:00'
    add('partial-then-known-cancel',r,status='REPLAYED_ACCEPTED_REVIEW',B_filled='7',remaining='13',attempt='ACCEPTED',order_status='CANCELLED_EVIDENCE')
    return out
