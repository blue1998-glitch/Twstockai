"""Freeze the specified case and finite control inputs before implementation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from graph_core.core import fingerprint

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
PROJECT=ROOT.parents[1]


def load(p):return json.loads(p.read_text())


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    r=ROOT.parent
    paths=dict(quotes=r/'generated/input.json',quote_manifest=r/'generated/sources.json',
        catalog=r/'subsidiary_proposal_20261023/catalog-v010.json',calendar=r/'source_qualification_20261022/observed-calendar.json')
    bundle={k:load(p) for k,p in paths.items()};binding={k:fingerprint(v) for k,v in bundle.items()}
    save(ROOT/'source-spec.json',dict(schema='rotation-market-source-spec/0.1',files={k:info(p) for k,p in paths.items()}))
    names=[('A-breakout','2026-04-08',['A-reference','A-breakout']),('A-return','2026-04-09',['A-reference','A-return']),
        ('B-opportunity','2026-06-22',['B-reference','B-breakout'])]
    decisions=[dict(id=k,market_date=d,decision_at=None,data_cutoff=None,evidence_ids=ids) for k,d,ids in names]
    common=dict(period=None,account=dict(kind='NEW_HYPOTHETICAL_CASH_NOT_USER_ACCOUNT',account_id=None,
        cash=None,shares={'1101':'0','2884':'0'},cash_claims=[],share_claims=[],
        rights_basis='EXPLICIT_NEW_ACCOUNT_ASSUMPTION_NOT_PRIVATE_EVIDENCE'),execution_model=None,
        market_observations=None)
    draft=dict(schema='rotation-market-case-input/0.1',case_id='1101-return-then-2884-opportunity',
        data_kind='SAVED_REAL_RAW_WITH_EXPLICIT_HYPOTHETICAL_ACCOUNT',source_binding=binding,
        common=common,decisions=decisions,common_entry=None,paths=[dict(id=k,intent=intent,common=None,fills=None,b_intent=None)
            for k,intent in [('hold','HOLD_A'),('reduce','REDUCE_A'),('cash','EXIT_A_TO_CASH')]])
    save(ROOT/'input.json',draft)
    # Only a preparation/validation control: these parameters are not adopted for the market case.
    explicit=deepcopy(draft);c=explicit['common'];c['period']=dict(start='2026-04-07',end='2026-06-23')
    c['account'].update(account_id='TEST-ONLY-new-cash',cash='10000')
    c['execution_model']=dict(id='TEST-ONLY-model',description='NON_EXECUTABLE_BINDING_CONTROL_NOT_SELECTED_MARKET_MODEL',
        parameter_source='fixture:explicit-readiness-control',declared_at='2026-10-27T00:00:00+00:00',
        fill_role='HYPOTHETICAL_EXPLICIT_NOT_ACTUAL',settlement='EXPLICIT_DATES_NOT_VERIFIED_REAL_CALENDAR',
        terminal_costs=dict(fee_rate='0.001425',minimum_fee='20',sell_tax='0.003',slippage_bps='10'))
    c['market_observations']=[dict(code='1101',at='2026-04-09T09:00:00+08:00',available_at='2026-04-09T09:00:00+08:00',
        price='25.50',capacity='10',market_state='MODEL_OPEN_NOT_ACTUAL_FILL',source_id=explicit['source_binding']['quotes'],
        basis_id=bundle['quotes']['assets']['1101']['basis_id'],qualification='TEST_ONLY_ASSUMPTION_NOT_HISTORICAL_AUTHENTICATION')]
    for d in explicit['decisions']:
        d['decision_at']=d['market_date']+'T17:00:00+08:00';d['data_cutoff']=d['market_date']+'T16:00:00+08:00'
    entry=dict(id='TEST-entry-A',code='1101',side='BUY',date='2026-04-09',decision_date='2026-04-08',shares='10',
        price='25.50',fee='1',tax='0',settlement_date='2026-04-10',source_ids=['quote-0'])
    explicit['common_entry']=entry
    for path in explicit['paths']:
        path['common']=deepcopy(c);path['fills']=[deepcopy(entry)];path['b_intent']='HOLD_CURRENT_FOR_PREPARATION_CONTROL'
        if path['id']!='hold':path['fills'].append(dict(entry,id='TEST-sell-'+path['id'],side='SELL',date='2026-04-10',
            decision_date='2026-04-09',settlement_date='2026-04-13',shares='5' if path['id']=='reduce' else '10',price='25.10'))
    save(ROOT/'controls/explicit-input.json',explicit)
    save(ROOT/'expected.json',dict(draft_status='AWAITING_EXPLICIT_INPUT',draft_compiled_accounts=None,
        explicit_status='REFUSED_SOURCE_QUALIFICATION',explicit_numeric_replay_calls=0,paths=['hold','reduce','cash'],
        old_qualification_reasons_include=['OPENING_ENTITLEMENTS_UNKNOWN','NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN',
            'ACTION_COVERAGE_INCOMPLETE:1101','ACTION_COVERAGE_INCOMPLETE:2884'],
        milestones=[dict(code='1101',date='2026-03-12',field='high',value='25.20'),
            dict(code='1101',date='2026-04-08',field='close',value='25.40'),dict(code='1101',date='2026-04-09',field='close',value='25.10'),
            dict(code='2884',date='2026-02-26',field='high',value='35.50'),dict(code='2884',date='2026-06-22',field='close',value='35.80')],
        april_cannot_reference_june=True,all_formal_flags_false=True,primary_pressure_id=None,all_returns=None,
        future_changes_do_not_change_april_prefix=True,oracle_written_before_implementation=True))
    parent=[];v=bundle['catalog']
    while v:
        parent.append(dict(schema=v['schema'],id=v['id']));v=v.get('parent_catalog')
    oldfiles=list(paths.values())+[r/'action_ledger.py',r/'action_resolution.py',r/'subsidiary_proposal.py',
        r/'subsidiary_proposal_sources.py',r/'action_study.py',r/'core.py',r/'store.py',
        PROJECT/'capital_research/execution.py',PROJECT/'capital_research/account_metrics.py',
        r/'subsidiary_proposal_20261023/window-qualification.json']
    save(ROOT/'intake.json',dict(baseline='74e7c8e07d9d2446376305ace68b56c76f6732f3',work_known_ancestor='3b472ae8575f4f4f6c5acaf504f29d0ded078bdd',
        unchanged_originals=[info(p) for p in oldfiles],source_parent_chain=parent,
        roots_before=[info(REPO/n) for n in ['AGENTS.md','CONTINUE_IN_WORK_MODE.md','PROJECT_VISION.md','M1_V019_GRAPH_CORE_RESUME_HANDOFF.md']],
        historic_evidence_not_rerun=True,control_parameters_not_adopted_for_market_case=True))
    save(ROOT/'frozen.json',dict(files=[info(ROOT/n) for n in ['CONTRACT.md','source-spec.json','input.json','controls/explicit-input.json','expected.json','intake.json','freeze.py']]))


if __name__=='__main__':main()
