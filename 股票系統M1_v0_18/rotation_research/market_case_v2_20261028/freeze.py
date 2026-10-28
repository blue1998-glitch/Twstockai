"""Freeze exact external context and test cases before implementing v0.2."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from graph_core.core import fingerprint

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
REPO=PROJECT.parent


def load(p):return json.loads(p.read_text())


def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def info(p):
    b=p.read_bytes();return dict(path=str(p.relative_to(REPO)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    old=ROOT.parent/'market_case_20261027';spec=load(old/'source-spec.json')
    save(ROOT/'source-spec.json',spec)
    summary=dict(schema='work-summary-testimony/0.1',research_version='0.24',work_json_version='0.16',
        originals=[dict(library_id='libfile_386a0d7015f08191be9fd63e688d1425',read_by_codex=False),
            dict(library_id='libfile_0935ff42c238819180b5d2fc30a874a6',read_by_codex=False)],
        authority='USER_PROVIDED_SUMMARY_NOT_ORIGINAL_DOCUMENT_OR_HISTORICAL_PUBLICATION',
        statements=[
            '②為2026/4/9的小突破後淺回檔承接機會，使用者已確認。',
            '4/10普通開25.35、零股第一筆25.60只是後續模型素材，均非已成交，不混用①4/9開25.50成本。',
            '③4/10圖形機會已確認，不代表既有持股自動加碼；24.80是本例重要回檔守位，不是自動全退線。',
            '④4/15是較深失守；4/17尚未完成後續新低；⑤4/22才新增回升未收復、再低於④低點的反證。',
            '2884截至4/15可以進場，32.85可作本例局部進場參照，原35.50仍保留。圖形確認不等正式新委託許可、來源合格或成本後優勢。',
            '6488截至4/15圖形可進場，但只在Work附錄，不擴原1101/2884產品案例；不指定494.50為唯一依據、不回填4/13成交。',
            'K/X4/R4_X5/X5未批准；本金、N、股數、減少比例、預留、風險門檻、概率及排名待決。'])
    save(ROOT/'work-summary.json',summary)
    binding=load(old/'input.json')['source_binding']
    def fact(i,day,role,text,refs=()):
        return dict(id=i,code='2884' if i=='B-Apr15' else '1101',case_context_on=day,role=role,
            statement=text,reference_ids=list(refs),evidence_kind='USER_CONFIRMED_CASE_FROM_WORK_SUMMARY',historical_available_at=None)
    facts=[fact('II','2026-04-09','PULLBACK_CATCH_OPPORTUNITY',summary['statements'][0],['A-important']),
        fact('III','2026-04-10','GRAPH_OPPORTUNITY',summary['statements'][2],['A-important']),
        fact('IV','2026-04-15','DEEPER_LOSS',summary['statements'][3],['A-important']),
        fact('Apr17','2026-04-17','FOLLOWUP_NEW_LOW_NOT_COMPLETED','截至4/17尚未完成後續新低。',['IV']),
        fact('V','2026-04-22','RECOVERY_NOT_RECLAIMED_AND_LOWER_THAN_IV','4/22新增回升未收復、再低於④低點反證。',['IV']),
        fact('B-Apr15','2026-04-15','LOCAL_GRAPH_ENTRY_OPPORTUNITY',summary['statements'][4],['B-local','B-original'])]
    def ref(i,c,day,role,value,bar):return dict(id=i,code=c,case_context_on=day,role=role,value=value,raw_bar=bar,
        evidence_kind='USER_CONFIRMED_CASE_FROM_WORK_SUMMARY',historical_role_known_at=None)
    refs=[ref('A-important','1101','2026-04-09','IMPORTANT_PULLBACK_LEVEL','24.80',dict(date='2026-04-09',field='low')),
        ref('B-original','2884','2026-02-26','ORIGINAL_UPPER_REFERENCE','35.50',dict(date='2026-02-26',field='high')),
        ref('B-local','2884','2026-04-15','LOCAL_ENTRY_REFERENCE','32.85',None)]
    materials=[dict(id='II-regular-open',opportunity_id='II',code='1101',case_context_on='2026-04-10',
        channel='REGULAR_OPEN',price_role='SAVED_DAILY_OPEN_MODEL_MATERIAL',price='25.35',raw_bar=dict(date='2026-04-10',field='open'),
        evidence_kind='SAVED_RAW_BAR_MODEL_MATERIAL_NOT_FILL',capacity=None,trade_at=None,historical_available_at=None,fee_model=None,settlement_date=None),
        dict(id='II-odd-first',opportunity_id='II',code='1101',case_context_on='2026-04-10',channel='ODD_LOT_FIRST_PRINT',
        price_role='WORK_REPORTED_FIRST_PRINT_MODEL_MATERIAL',price='25.60',raw_bar=None,
        evidence_kind='WORK_SUMMARY_ONLY_NO_RETAINED_FIRST_PRINT_OR_CAPACITY',capacity=None,trade_at=None,historical_available_at=None,fee_model=None,settlement_date=None)]
    draft=dict(schema='rotation-market-case-context-input/0.2',case_id='1101-II-pullback-with-2884-Apr15',
        data_kind='SAVED_REAL_RAW_WITH_WORK_CASE_CONTEXT_NOT_SYNTHETIC',source_binding=binding,work_summary_id=fingerprint(summary),
        track=dict(id='II',opportunity_id='II'),facts=facts,references=refs,entry_materials=materials,
        excluded_contexts=[dict(track_id='I',ordinary_open_on='2026-04-09',ordinary_open='25.50',adopted_for_main_track=False)],
        selected_entry_material_id=None,as_of_dates=['2026-04-09','2026-04-10','2026-04-15','2026-04-17','2026-04-22'],
        research_parameters={k:None for k in ['opening_cash','N','shares','reduction_ratio','reserved_cash','common_period','risk_thresholds','probability_model','ranking_model','execution_model']},
        research_controls={k:'UNAPPROVED' for k in ['K','X4','R4_X5','X5']})
    save(ROOT/'input.json',draft)
    expected=dict(status='CONTEXT_PREPARED_RESEARCH_INPUTS_PENDING',track='II',main_opportunity_on='2026-04-09',
        ordinary_material_price='25.35',odd_material_price='25.60',B_references=['32.85','35.50'],
        prefix_fact_ids={'2026-04-09':['II'],'2026-04-10':['II','III'],
            '2026-04-15':['II','III','IV','B-Apr15'],'2026-04-17':['II','III','IV','Apr17','B-Apr15'],
            '2026-04-22':['II','III','IV','Apr17','V','B-Apr15']},
        early_materials=[],unqualified_signals=[],numeric_replay='NOT_PERFORMED',formal_flags=False,
        unknown_parameters_preserved=True,policy_automatic_action=False,original_schema_unchanged=True)
    save(ROOT/'expected.json',expected)
    cases=[]
    def add(name,edit,expect):
        x=deepcopy(draft);edit(x);cases.append(dict(name=name,input=x,expected=expect))
    add('selected-regular',lambda x:x.__setitem__('selected_entry_material_id','II-regular-open'),dict(status=expected['status'],selected='II-regular-open'))
    add('selected-odd',lambda x:x.__setitem__('selected_entry_material_id','II-odd-first'),dict(status=expected['status'],selected='II-odd-first'))
    add('wrong-I-opportunity',lambda x:x['entry_materials'][0].__setitem__('opportunity_id','I'),dict(error='MAIN_TRACK_OPPORTUNITY_BINDING_REQUIRED'))
    add('I-price-in-II',lambda x:x['entry_materials'][0].__setitem__('price','25.50'),dict(error='RAW_MODEL_MATERIAL_VALUE_MISMATCH'))
    add('ordinary-as-odd',lambda x:x['entry_materials'][1].__setitem__('price_role','SAVED_DAILY_OPEN_MODEL_MATERIAL'),dict(error='CHANNEL_ROLE_OR_SOURCE_MISMATCH'))
    add('odd-price-from-open',lambda x:x['entry_materials'][1].__setitem__('raw_bar',dict(date='2026-04-10',field='open')),dict(error='CHANNEL_ROLE_OR_SOURCE_MISMATCH'))
    add('daily-volume-as-first-capacity',lambda x:x['entry_materials'][1].__setitem__('capacity','52862166'),dict(error='CAPACITY_OR_EXECUTION_EVIDENCE_NOT_IMPLEMENTED'))
    add('unknown-material',lambda x:x.__setitem__('selected_entry_material_id','I-open'),dict(error='EXPLICIT_SINGLE_KNOWN_MATERIAL_REQUIRED'))
    add('multiple-materials',lambda x:x.__setitem__('selected_entry_material_id',['II-regular-open','II-odd-first']),dict(error='EXPLICIT_SINGLE_KNOWN_MATERIAL_REQUIRED'))
    add('policy-promotion',lambda x:x['research_controls'].__setitem__('X4','APPROVED'),dict(error='RESEARCH_CONTROL_NOT_AUTHORIZED'))
    add('unsupported-6488',lambda x:x['facts'][0].__setitem__('code','6488'),dict(error='ONLY_ORIGINAL_1101_2884_CASE_SUPPORTED'))
    add('synthetic-relabel',lambda x:x.__setitem__('data_kind','SYNTHETIC'),dict(error='EXPLICIT_REAL_CASE_CONTEXT_REQUIRED'))
    save(ROOT/'cases.json',cases)
    save(ROOT/'prefix-spec.json',dict(cases=[dict(as_of=d,expected_fact_ids=expected['prefix_fact_ids'][d]) for d in draft['as_of_dates']],
        future_controls=[dict(name='future-price-up',B_future='99.00',V_statement='later alternative A rise'),
            dict(name='future-price-down',B_future='1.00',V_statement='later alternative A decline')],
        future_price_date='2026-06-22',prefixes_to_compare=['2026-04-15','2026-04-17'],same_prefix_expected=True,
        no_lookahead_into_Apr22=True,source_integrity_metadata_separate=True))
    old_manifest=old/'CHANGE_MANIFEST.json';protected=[]
    roots=['AGENTS.md','CONTINUE_IN_WORK_MODE.md','PROJECT_VISION.md','M1_V019_GRAPH_CORE_RESUME_HANDOFF.md',str(ROOT.parent.relative_to(REPO)/'README.md')]
    for item in load(old_manifest)['files']:
        if item['path'] not in roots:protected.append(info(REPO/item['path']))
    protected.append(info(old_manifest))
    protected += [v for v in spec['files'].values()]
    save(ROOT/'intake.json',dict(baseline='e60649162241b5287496ee7cc66472301a710c29',
        original_files=protected,roots_before=[info(REPO/n) for n in roots],
        original_work_documents_not_obtained=True,no_numeric_dispatch_or_new_strategy=True))
    save(ROOT/'frozen.json',dict(files=[info(ROOT/n) for n in ['CONTRACT.md','source-spec.json','work-summary.json','input.json','expected.json','cases.json','prefix-spec.json','intake.json','freeze.py']]))


if __name__=='__main__':main()
