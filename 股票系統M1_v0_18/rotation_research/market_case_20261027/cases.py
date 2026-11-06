"""Freeze exact counterexamples before production implementation exists."""
from copy import deepcopy
from .freeze import ROOT,PROJECT,load,save,info


def main():
    base=load(ROOT/'controls/explicit-input.json');manifest=load(PROJECT/'rotation_research/generated/sources.json')
    quote_id='quote-'+str(next(i for i,s in enumerate(manifest) if s['path'].endswith('1101_2026-04.json')))
    # Input self-review: quote-0 is retained as a wrong-period source control.
    # No execution or production code has run; freeze the corrected positive separately.
    base['common_entry']['source_ids']=[quote_id]
    for p in base['paths']:
        for fill in p['fills']:fill['source_ids']=[quote_id]
    save(ROOT/'controls/source-bound-input.json',base)
    save(ROOT/'diagnostics/pre-implementation-input-review.json',dict(original='controls/explicit-input.json',
        issue='quote-0 is an existing archive identifier but outside April; cannot certify a fill source by existence only',
        original_preserved=True,positive='controls/source-bound-input.json',replacement_source_id=quote_id,
        no_actual_or_oracle_overwritten=True,numeric_calls=0))
    variants=[]
    def case(name,fn,reason):
        x=deepcopy(base);fn(x);save(ROOT/'cases'/name/'input.json',x);save(ROOT/'cases'/name/'expected.json',dict(error=reason));variants.append(name)
    case('wrong-opening',lambda x:x['paths'][1]['common']['account'].__setitem__('cash','10001'),'COMMON_CONDITIONS_MISMATCH')
    case('wrong-period',lambda x:x['paths'][1]['common']['period'].__setitem__('end','2026-06-24'),'COMMON_CONDITIONS_MISMATCH')
    for key,value in [('price','25.51'),('capacity','9'),('market_state','MODEL_LIMIT_UP_NO_BUY'),('available_at','2026-04-09T09:01:00+08:00'),('basis_id','WRONG'),('source_id','WRONG')]:
        case('wrong-market-'+key,lambda x,k=key,v=value:x['paths'][1]['common']['market_observations'][0].__setitem__(k,v),'COMMON_CONDITIONS_MISMATCH')
    case('wrong-cost-model',lambda x:x['paths'][1]['common']['execution_model']['terminal_costs'].__setitem__('minimum_fee','0'),'COMMON_CONDITIONS_MISMATCH')
    case('april-borrows-june',lambda x:x['decisions'][1]['evidence_ids'].append('B-breakout'),'FUTURE_EVIDENCE_REFERENCE')
    case('reset-opening',lambda x:x['paths'][1].__setitem__('opening',{'cash':'20000'}),'EXACT_PATH_FIELDS_REQUIRED')
    case('entry-rewritten',lambda x:x['paths'][1]['fills'][0].__setitem__('shares','11'),'COMMON_A_ENTRY_MISMATCH')
    case('wrong-fill-source',lambda x:x['paths'][0]['fills'][0].__setitem__('source_ids',['quote-0']),'COMMON_A_ENTRY_MISMATCH')
    case('synthetic-relabelling',lambda x:x.__setitem__('synthetic',True),'EXACT_CASE_FIELDS_REQUIRED')
    case('wrong-source-binding',lambda x:x['source_binding'].__setitem__('catalog','WRONG'),'SOURCE_BINDING_MISMATCH')
    case('b-buy-before-opportunity',lambda x:x['paths'][0]['fills'].append(dict(x['common_entry'],id='early-B',code='2884',date='2026-04-10',decision_date='2026-04-09')),'B_FILL_BEFORE_EXPLICIT_OPPORTUNITY')
    save(ROOT/'cases/index.json',dict(rejected_cases=variants,positive='controls/source-bound-input.json',
        positive_expected=load(ROOT/'expected.json')['explicit_status'],draft='input.json',draft_expected=load(ROOT/'expected.json')['draft_status']))
    save(ROOT/'frozen-cases.json',dict(files=[info(p) for p in sorted((ROOT/'cases').rglob('*.json'))]+[
        info(ROOT/'cases.py'),info(ROOT/'controls/source-bound-input.json'),info(ROOT/'diagnostics/pre-implementation-input-review.json')]))


if __name__=='__main__':main()
