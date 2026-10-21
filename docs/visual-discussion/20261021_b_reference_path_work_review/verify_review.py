"""Check fixed saved-data queries, time cutoffs, and existing June continuity."""
from pathlib import Path
from decimal import Decimal as D
from datetime import date
import json,hashlib,importlib.util,copy
from pypdf import PdfReader
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('build_review',R/'build_review.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
raw=mod.S.read_bytes();s=json.loads(raw);bs=s['bars'];by={b['date']:b for b in bs}
e=json.loads((R/'evidence.json').read_text());m=json.loads((R/'figure-manifest.json').read_text())
assert hashlib.sha256(raw).hexdigest()==mod.SHA==e['source_sha256']
assert len(bs)==len(by)==1213 and list(by)==sorted(by)
prefix_checks=0
for key,q in e['queries'].items():
    args=(q['reference_date'],q['reference_field'],q['start'])
    expected=mod.make_query(bs,q['as_of'],*args);assert q==expected
    for cutoff in [q['start']]+[row['bar']['date'] for row in q['rows']]:
        full=mod.make_query(bs,cutoff,*args)
        prefix=mod.make_query([b for b in bs if b['date']<=cutoff],cutoff,*args)
        assert full==prefix
        polluted=copy.deepcopy(bs)
        for b in polluted:
            if b['date']>cutoff:
                for f in ['open','high','low','close','volume_shares_scaled']:b[f]='999999999'
        assert mod.make_query(polluted,cutoff,*args)==full
        prefix_checks+=1
j=e['queries']['july_local']['rows'];assert len(j)==5
assert [x['bar']['date'] for x in j]==['2026-07-20','2026-07-21','2026-07-22','2026-07-23','2026-07-24']
assert all(x['close_relation']=='ABOVE' for x in j)
assert [x['bar']['date'] for x in j if x['low_relation']=='BELOW']==['2026-07-20','2026-07-23','2026-07-24']
# Origin low is kept separately from subsequent returns, not counted as an extra reaction.
assert len(e['queries']['july_new_high']['rows'])==3
assert all(x['close_relation']=='BELOW' for x in e['queries']['july_new_high']['rows'])
assert e['queries']['july_new_high']['rows'][0]['high_relation']=='EQUAL'
v=e['frozen_july_volume'];src=[b for b in bs if v['reading_scope'][0]<=b['date']<=v['reading_scope'][1]]
assert len(src)==v['saved_rows']==12
assert D(v['max_shares'])==max(D(b['volume_shares_scaled']) for b in src)==D('97753866')
assert v['max_dates']==['2026-07-17']
assert all(D(x['bar']['volume_shares_scaled'])<D(v['max_shares']) for x in j)
for name,origin,ref in [('june_lower','2026-06-04','2026-04-16'),('june_broader','2026-06-22','2026-02-26')]:
    q=e['queries'][name];assert q['start']==origin and q['reference_date']==ref
    old=json.loads((R.parent/'b-followup-holding-research/episode-summaries.json').read_text())
    record=next(x for x in old if x['birth']['query']['origin']==origin)
    rows=q['rows'][1:]
    assert len(rows)==record['summary']['followup_saved_bars_excluding_origin']
    for role,field in [('ABOVE','close_above_count'),('EQUAL','close_equal_count'),('BELOW','close_below_count')]:assert sum(x['close_relation']==role for x in rows)==record['summary'][field]
assert e['queries']['june_broader']['value']==e['queries']['july_local']['value']=='35.50'
assert e['queries']['june_broader']['reference_date']!=e['queries']['july_local']['reference_date']
assert e['unadjusted_old_reference_after_july_1']=='NOT_PROMOTED_TO_REACTION_EVIDENCE'
assert all(e[k] is None for k in ['formal_bounds','formal_merge','holding_threshold','volume_baseline_formula'])
assert e['historical_signal_eligible'] is False
for x in m['figures']:
    assert (date.fromisoformat(x['last'])-date.fromisoformat(x['first'])).days>183
    assert len([b for b in bs if x['first']<=b['date']<=x['last']])==x['bars']
    assert hashlib.sha256((R/x['image']).read_bytes()).hexdigest()==x['sha256']
p=R/'output/pdf/b-reference-path-review.pdf';assert hashlib.sha256(p.read_bytes()).hexdigest()==m['pdf_sha256']
assert len(PdfReader(p).pages)==2 and all(len(p.images)==0 for p in PdfReader(p).pages)
out={'status':'PASS_FIXED_SAVED_EVIDENCE_ONLY','cutoff_prefix_and_future_price_volume_pollution_checks':prefix_checks,'existing_june_summary_continuity':True,'july_local_source_and_origin_vs_followup_separated':True,'strict_equal_high_not_exceeded':True,'same_price_different_date_not_same_reference':True,'no_adjusted_series_created':True,'original_source_gaps_preserved':e['source_gaps']==s['source_gaps'],'windows_saved_bars':[x['bars'] for x in m['figures']],'vector_pages':2,'builder_runs':2,'render_runs':2,'verification_runs':1,'new_market_price_fetches':0,'core_classifier_product_tests':0,'android':'NOT_TESTED_NEW_BUILD','historical_signal_eligible':False}
mod.dump('verification.json',out);print(json.dumps(out,ensure_ascii=False))
