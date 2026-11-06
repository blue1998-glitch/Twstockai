"""Explicit engineered ledger fixtures. Never market input, prices or rules."""
from graph_core.core import fingerprint
from .action_ledger import days


def fixture():
    ds=days('2026-01-05','2026-01-12')
    from datetime import date
    trading={d:date.fromisoformat(d).weekday()<5 for d in ds}
    return dict(schema='rotation-action-input/0.1',mode='RAW',start=ds[0],end=ds[-1],
        sources={'fixture':dict(kind='ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET',url='fixture://explicit-values',
                              sha256='f'*64,captured_at='2026-10-22T00:00:00Z')},
        assets={c:dict(source_id='fixture',basis_id='RAW:fixture:'+c,quote_source_ids=['fixture'],
                       quotes={d:p for d in ds if trading[d]}) for c,p in [('A','10'),('B','20')]},
        calendar=[dict(date=d,trading=trading[d]) for d in ds],events=[],
        coverage={c:dict(status='VERIFIED_COMPLETE',start=ds[0],end=ds[-1],types=['CASH_DIVIDEND','STOCK_DIVIDEND','CAPITAL_REDUCTION'],
                         other_actions_checked=True,source_ids=['fixture'],event_ids=[]) for c in ('A','B')},
        qualification=dict(calendar='VERIFIED_COMPLETE',opening_claims='VERIFIED',net_distributions='VERIFIED',
                           execution_costs='SCENARIO',investor_cashflows='SCENARIO'),
        opening=dict(cash='0',shares={'A':'100','B':'0'},cash_claims=[],share_claims=[]),fills=[],
        terminal_costs=dict(fee_rate='0',minimum_fee='0',sell_tax='0',slippage_bps='0'))


def event(data, kind='CASH_DIVIDEND', **overrides):
    e=dict(type=kind,code='A',basis_id='RAW:fixture:A',ex_date='2026-01-06',source_ids=['fixture'])
    e.update({'CASH_DIVIDEND':dict(gross_per_share='1',net_per_share='0.8',pay_date='2026-01-09'),
              'STOCK_DIVIDEND':dict(shares_per_share='0.1',delivery_date='2026-01-08',tradable_date='2026-01-09'),
              'CAPITAL_REDUCTION':dict(remaining_share_ratio='0.5',gross_cash_per_old_share='5',net_cash_per_old_share='5',
                                       pay_date='2026-01-09',tradable_date='2026-01-08')}[kind])
    e.update(overrides)
    e['field_sources']={k:[dict(source_id='fixture',locator='engineered.'+k)] for k in e if k not in ('source_ids','basis_id','code','type')}
    e['id']=fingerprint(e);data['events'].append(e)
    data['coverage']['A']['event_ids'].append(e['id']);return e


def fill(data, side, when, code='A', shares='100', price='9', fee='0', tax='0', settlement=None):
    d=dict(id='fill-'+str(len(data['fills'])),side=side,date=when,decision_date='2026-01-05',
           code=code,shares=shares,price=price,fee=fee,tax=tax,settlement_date=settlement or when,source_ids=['fixture'])
    data['fills'].append(d);return d
