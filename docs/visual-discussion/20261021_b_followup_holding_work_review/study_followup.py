"""Observed follow-up facts for three existing B crossings; no hold/success rule."""
from pathlib import Path
from decimal import Decimal as D
import hashlib,json,os

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
PRIOR=Path(os.environ.get('B_PRIOR_PATH','/workspace/scratch/e9363d3b9105/b-breakout-path-research/path-evidence.json'))
EXPECTED='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
END='2026-06-30'
CUTOFFS=['2026-06-04','2026-06-05','2026-06-08','2026-06-09','2026-06-11','2026-06-17','2026-06-18','2026-06-22','2026-06-23','2026-06-24','2026-06-25',END]
QUERIES=[{'name':'lower_first','reference_date':'2026-04-16','reference_field':'high','origin':'2026-06-04'}, {'name':'lower_reclaim','reference_date':'2026-04-16','reference_field':'high','origin':'2026-06-09'}, {'name':'broader_first','reference_date':'2026-02-26','reference_field':'high','origin':'2026-06-22'}]
def write(name,value):
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def price_bar(b):return {k:b[k] for k in ('date','open','high','low','close')}
def rel(x,p):return 'ABOVE'if x>p else 'BELOW'if x<p else 'EQUAL'
def longest(facts,key):
    current=best=0
    for x in facts:
        current=current+1 if x['close_relation']==key else 0;best=max(best,current)
    return best
def trailing(facts,key):
    n=0
    for x in reversed(facts):
        if x['close_relation']!=key:break
        n+=1
    return n
def observe(all_bars,cutoff):
    bs=[b for b in all_bars if b['date']<=cutoff];bydate={b['date']:b for b in bs};episodes=[]
    for query in QUERIES:
        if query['origin']>cutoff:continue
        if query['origin'] not in bydate or query['reference_date'] not in bydate:continue
        origin=bydate[query['origin']];value=bydate[query['reference_date']][query['reference_field']];p=D(value)
        idx=next(i for i,b in enumerate(bs)if b['date']==query['origin']);previous=bs[idx-1]
        assert D(previous['close'])<p<D(origin['close'])
        identity={'reference_date':query['reference_date'],'reference_field':query['reference_field'],'reference_value':value,'origin':query['origin']}
        eid='sha256:'+hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        birth={'id':eid,'query':query,'reference_value':value,'reference_role':'RAW_HIGH_PROXY_NOT_CONFIRMED_FORMAL_BAND_EDGE','origin_price_bar':price_bar(origin),'previous_price_bar':price_bar(previous),'price_cross_observable_on_saved_bar':query['origin'],'selection':'FIXED_RETROSPECTIVE_QUERY_NOT_HISTORICAL_AUTOMATIC_SELECTION'}
        later=[b for b in bs if query['origin']<b['date']<=min(cutoff,END)]
        facts=[]
        for b in later:
            c,h,l=map(D,[b['close'],b['high'],b['low']])
            facts.append({'bar':price_bar(b),'date':b['date'],'close_relation':rel(c,p),'low_strictly_below_close_above':l<p<c,'low_equal_close_above':l==p<c,'high_strictly_above_close_below':c<p<h,'high_equal_close_below':c<p==h,'whole_bar_above':l>p,'whole_bar_below':h<p})
        below=[x['date']for x in facts if x['close_relation']=='BELOW'];above=[x['date']for x in facts if x['close_relation']=='ABOVE'];equal=[x['date']for x in facts if x['close_relation']=='EQUAL']
        first_below=below[0]if below else None
        regain=next((x['date']for x in facts if first_below and x['date']>first_below and x['close_relation']=='ABOVE'),None)
        last_relation=facts[-1]['close_relation']if facts else None
        if not facts:pattern='NO_LATER_SAVED_BAR_YET'
        elif last_relation=='EQUAL':pattern='CURRENT_CLOSE_EQUAL_TO_REFERENCE'
        elif last_relation=='BELOW':pattern='CURRENTLY_BELOW_REFERENCE'
        elif below:pattern='CURRENTLY_ABOVE_AFTER_AN_EARLIER_CLOSE_RETURN'
        else:pattern='FOLLOWUP_CLOSES_ABOVE_WITH_NO_CLOSE_RETURN_OBSERVED'
        summary={'as_of':cutoff,'followup_end':later[-1]['date']if later else None,'followup_saved_bars_excluding_origin':len(later),'close_above_count':len(above),'close_equal_count':len(equal),'close_below_count':len(below),'first_close_below_date':first_below,'first_close_regain_after_first_below':regain,'low_below_close_above_dates':[x['date']for x in facts if x['low_strictly_below_close_above']],'low_equal_close_above_dates':[x['date']for x in facts if x['low_equal_close_above']],'high_above_close_below_dates':[x['date']for x in facts if x['high_strictly_above_close_below']],'high_equal_close_below_dates':[x['date']for x in facts if x['high_equal_close_below']],'whole_bar_below_dates':[x['date']for x in facts if x['whole_bar_below']],'longest_consecutive_saved_closes_above':longest(facts,'ABOVE'),'trailing_consecutive_saved_closes_above':trailing(facts,'ABOVE'),'trailing_consecutive_saved_closes_below':trailing(facts,'BELOW'),'lowest_followup_close':min((b['close']for b in later),key=D)if later else None,'lowest_followup_low':min((b['low']for b in later),key=D)if later else None,'current_close_relation':last_relation or 'ORIGIN_ABOVE_NO_FOLLOWUP_YET','observed_pattern':pattern,'observation_is_open_ended':True,'formal_holding_confirmed':None,'formal_success_or_failure':None,'volume_used_as_veto':False,'holding_confirmation_date':None}
        episodes.append({'birth':birth,'summary':summary,'daily_followup_facts':facts})
    return {'cutoff':cutoff,'selection':'FINITE_RETROSPECTIVE_FOLLOWUP_RESEARCH','episodes':episodes,'price_evidence_independent_of_volume_gate':True,'counts_are_observations_not_confirmation_thresholds':True,'reclaims_are_same_reference_history_not_independent_samples':True,'formal_band_bounds':None,'historical_signal_eligible':False}
def run():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    src=json.loads(SOURCE.read_text());bs=src['bars'];prior=json.loads(PRIOR.read_text())
    assert len(bs)==1213==len({b['date']for b in bs}) and bs==sorted(bs,key=lambda b:b['date'])
    existing={e['date']:e for e in prior['events']}
    for q in QUERIES:
        key='lower_activity_high'if q['reference_date']=='2026-04-16'else'broader_high'
        assert existing[q['origin']]['references'][key]['saved_close_cross']=='UP'
    final=observe(bs,END)
    write('followup-evidence.json',final)
    write('cutoff-views.json',{c:observe(bs,c)for c in CUTOFFS})
    write('episode-summaries.json',[{'birth':e['birth'],'summary':e['summary']}for e in final['episodes']])
    write('source-provenance.json',{'base_commit':'2805d811e19ec3eaa439d4104e8ab52b3c3e4ce2','source_repo_path':'docs/visual-discussion/20261020_independent_source_levels_work_review/source-data-2884.json','source_sha256':EXPECTED,'prior_path_repo_path':'docs/visual-discussion/20261021_b_breakout_path_work_review/path-evidence.json','prior_path_sha256':hashlib.sha256(PRIOR.read_bytes()).hexdigest(),'source_gaps':src['source_gaps'],'price_basis_id':src['price_basis_id'],'method':'Reuse three original crossing records and raw OHLC; build later-only price evidence, no new volume statistics, band classifier, holding rule, or market download.'})
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    print(json.dumps([{'query':e['birth']['query']['name'],'summary':e['summary']}for e in final['episodes']],ensure_ascii=False,indent=2))
if __name__=='__main__':run()
