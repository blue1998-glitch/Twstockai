"""Finite synthetic inputs and independent expectations; no checker import."""
from copy import deepcopy
from hashlib import sha256

SCHEMA = 'opening-entitlement-evidence-input/0.1'
PATH = 'entitlements.1101.cash_claims'
AS_OF = '2026-01-02T16:00:00+08:00'
AVAILABLE = '2026-01-02T16:10:00+08:00'
DECISION = '2026-01-02T17:00:00+08:00'


def base():
    binding = dict(account_id='SYNTHETIC-ACCOUNT-1', scenario_id='SYNTHETIC-OPENING-1', currency='TWD')
    assets = {c: dict(price_source_id='synthetic-price-'+c, basis_id='RAW', adjustment_version='UNADJUSTED')
              for c in ('1101', '2884')}
    data = dict(schema=SCHEMA, synthetic=True, clock_qualification='EXPLICIT_SYNTHETIC_NOT_REAL_CLOSE',
                binding=binding, assets=assets, as_of=AS_OF, data_cutoff=AS_OF, decision_at=DECISION,
                sources={'fixture': dict(kind='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET',
                    sha256=sha256(b'SYNTHETIC ONLY: no account or market original').hexdigest(),
                    available_at=AVAILABLE, captured_at='2026-10-26T00:00:00+00:00')},
                evidence={}, declarations={})
    fields = {'settled_cash': '0', 'reserved_cash': '0', 'payables': [], 'pending_orders': []}
    for c in assets:
        fields.update({f'holdings.{c}.shares': '20000' if c=='1101' else '0',
                       f'holdings.{c}.sellable': '20000' if c=='1101' else '0',
                       f'entitlements.{c}.cash_claims': [], f'entitlements.{c}.share_claims': []})
    for path, value in fields.items():
        scope=deepcopy(binding)
        if path.startswith(('holdings.', 'entitlements.')):
            c=path.split('.')[1];scope.update(code=c, **assets[c])
        eid='evidence:'+path
        data['declarations'][path]=dict(state='SOURCE_DECLARED', value=deepcopy(value), evidence_ids=[eid])
        data['evidence'][eid]=dict(field=path, scope=scope, as_of=AS_OF, available_at=AVAILABLE,
            source_id='fixture', locator='SYNTHETIC fixture/'+path, declared_value=deepcopy(value),
            complete_outstanding_inventory=isinstance(value,list))
    return data


def set_value(data, path, value):
    data['declarations'][path]['value']=deepcopy(value)
    data['evidence']['evidence:'+path]['declared_value']=deepcopy(value)


def cash_claim():
    return dict(id='SYNTHETIC-PRIOR-CASH-1', event_id='SYNTHETIC-PRIOR-EVENT-1',
                entitlement_at='2025-12-15T16:00:00+08:00', amount_net='9', currency='TWD',
                pay_date='2026-01-08', payment_status='OUTSTANDING')


def share_claim():
    return dict(id='SYNTHETIC-PRIOR-SHARE-1', event_id='SYNTHETIC-PRIOR-EVENT-2',
                entitlement_at='2025-12-15T16:00:00+08:00', shares='10',
                delivery_date='2026-01-08', tradable_date='2026-01-09', delivery_status='PENDING')


def cases():
    out={}
    def put(name, data, status, path=PATH, classification=None, gap=None, unsupported=None, value=None):
        expected=dict(status=status, field=path, classification=classification, required_gap=gap,
                      required_unsupported=unsupported, preserved_value=value,
                      authenticity_verified=False, opening_entitlements_verified=False, ledger_called=False,
                      legacy_qualification_updates={})
        out[name]=dict(input=data, expected=expected)
    d=base();put('sourced-zero',d,'STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED',classification='SOURCED_ZERO_DECLARATION',value=[])
    d=base();d['declarations'][PATH]=dict(state='UNKNOWN',value=[],evidence_ids=[])
    put('empty-is-unknown',d,'GAPS_PRESENT',classification='UNKNOWN',gap='UNKNOWN_DECLARATION',value=[])
    d=base();d['declarations'].pop(PATH)
    put('missing-is-unknown',d,'GAPS_PRESENT',classification='UNKNOWN',gap='MISSING_DECLARATION')
    d=base();d['declarations'][PATH]=dict(state='HYPOTHETICAL_ASSUMPTION',value=[],evidence_ids=[],assumption_reason='Explicit synthetic assumption; no private account claim')
    put('hypothetical-zero',d,'ASSUMPTIONS_PRESENT',classification='HYPOTHETICAL_ASSUMPTION',value=[])
    for key,value in [('account_id','OTHER-ACCOUNT'),('scenario_id','OTHER-SCENARIO'),('code','2884'),
                      ('price_source_id','OTHER-PRICE'),('basis_id','ADJUSTED'),('adjustment_version','OTHER-VERSION')]:
        d=base();d['evidence']['evidence:'+PATH]['scope'][key]=value
        put('wrong-'+key,d,'GAPS_PRESENT',classification='UNKNOWN',gap='EVIDENCE_SCOPE_MISMATCH',value=[])
    d=base();d['evidence']['evidence:'+PATH]['complete_outstanding_inventory']=False
    put('incomplete-zero',d,'GAPS_PRESENT',classification='UNKNOWN',gap='OUTSTANDING_INVENTORY_NOT_DECLARED_COMPLETE',value=[])
    d=base();d['evidence']['evidence:'+PATH]['declared_value']=[cash_claim()]
    put('content-conflict',d,'GAPS_PRESENT',classification='UNKNOWN',gap='EVIDENCE_VALUE_MISMATCH',value=[])
    d=base();set_value(d,'holdings.1101.shares','0');set_value(d,'holdings.1101.sellable','0');set_value(d,PATH,[cash_claim()])
    put('prior-right-without-holding',d,'STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED',classification='SOURCED_NONZERO_DECLARATION',value=[cash_claim()])
    d=base();d['evidence']['evidence:'+PATH]['available_at']='2026-01-05T08:00:00+08:00'
    put('late-proof',d,'GAPS_PRESENT',classification='UNKNOWN',gap='EVIDENCE_NOT_YET_AVAILABLE',value=[])
    d=base();d['evidence']['evidence:'+PATH]['available_at']='2026-01-02T09:00:00+00:00'
    put('equal-timezone-boundary',d,'STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED',classification='SOURCED_ZERO_DECLARATION',value=[])
    d=base();claim=cash_claim();claim.update(amount_net=None,pay_date=None);set_value(d,PATH,[claim])
    put('unknown-net-and-pay-date',d,'GAPS_PRESENT',classification='UNKNOWN',gap='NET_AMOUNT_UNKNOWN',value=[claim])
    d=base();p='entitlements.1101.share_claims';claim=share_claim();claim.update(delivery_date=None,tradable_date=None);set_value(d,p,[claim])
    put('unknown-share-dates',d,'GAPS_PRESENT',path=p,classification='UNKNOWN',gap='DELIVERY_DATE_UNKNOWN',value=[claim])
    d=base();p='entitlements.1101.share_claims';claim=share_claim();claim['shares']='0.5';set_value(d,p,[claim])
    put('fractional-right',d,'STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED',path=p,classification='SOURCED_NONZERO_DECLARATION',unsupported='FRACTIONAL_SHARE_RIGHT_REPLAY_NOT_IMPLEMENTED',value=[claim])
    for p,value,code in [('payables',[dict(id='SYNTHETIC-PAYABLE-1',amount='9')],'OPENING_PAYABLE_REPLAY_NOT_IMPLEMENTED'),
                         ('pending_orders',[dict(id='SYNTHETIC-ORDER-1',code='1101',side='BUY',remaining_shares='10',reserved_cash='101')],'EXTERNAL_EXISTING_ORDER_REPLAY_NOT_IMPLEMENTED')]:
        d=base();set_value(d,p,value)
        put('nonempty-'+p,d,'STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED',path=p,classification='SOURCED_NONZERO_DECLARATION',unsupported=code,value=value)
    d=base();claim=cash_claim();claim['entitlement_at']='2026-01-05T08:00:00+08:00';set_value(d,PATH,[claim])
    put('future-entitlement',d,'GAPS_PRESENT',classification='UNKNOWN',gap='CLAIM_AFTER_OPENING_CUTOFF',value=[claim])
    d=base();set_value(d,PATH,[cash_claim()]);p='entitlements.1101.share_claims';claim=share_claim();claim['id']=cash_claim()['id'];set_value(d,p,[claim])
    put('duplicate-right',d,'GAPS_PRESENT',path=p,classification='UNKNOWN',gap='DUPLICATE_ACCOUNT_ITEM_ID',value=[claim])
    return out
