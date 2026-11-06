"""Private bounded storage study: retained real prefixes + SYNTHETIC new days.

Never fetches sources. All real values, result files and charts stay outside Git.
Run prepare once, then run each encoding in separate fresh processes, compare.
"""
import argparse,json,os,resource,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
from graph_core.market_daily import Journal,encode,import_saved
from graph_core import market_increment as m
from graph_core.market_preview import build
from rotation_research import artifact_codec as c


def inventory(root):
    out={};seen=set()
    for p in root.rglob('*'):
        if not p.is_file() or p.is_symlink():continue
        s=p.stat();inode=(s.st_dev,s.st_ino)
        if inode not in seen:out[str(inode)]=dict(path=str(p.relative_to(root)),bytes=s.st_size,allocated=s.st_blocks*512);seen.add(inode)
    return out


def prepare(source,destination):
    source=m.external(source);destination=m.external(destination)
    if destination.exists():raise ValueError('New private study directory required; preserve all earlier evidence')
    destination.mkdir(parents=True)
    original=json.loads((source/'fm3-continuation.json').read_bytes());batch=Journal(source/'runs').read(original['result']['id'])['value']
    selected=[]
    for market in ('TWSE','TPEX'):
        rows=sorted([s for s in batch['stocks'] if s['market']==market and s['status']=='ANALYZED_FINMIND_HISTORY'],key=lambda s:Journal(source/'results').path(s['result_key']).stat().st_size)
        for q in (0.2,0.5,0.9):selected.append(dict(rows[int((len(rows)-1)*q)],study_stratum=market+'-'+str(q)))
    short=min([s for s in batch['stocks'] if s['status']=='INSUFFICIENT_HISTORY'],key=lambda s:s['history_records'])
    selected.append(dict(short,study_stratum='INSUFFICIENT_HISTORY_MINIMUM_RECORDS'))
    parent=dict(batch,stocks=selected,summary=dict(batch['summary'],expected=len(selected),processed=len(selected),evidence_class='REAL_SAVED_PREFIX_WITH_SYNTHETIC_NEW_DAYS_STUDY_NOT_MARKET_BATCH'))
    seed_id='du2-private-selected-seed'
    prepared=[]
    for mode in ('plain','compact'):
        root=destination/mode;root.mkdir()
        for stock in selected:
            for folder,key in [('results',stock['result_key']),('histories',stock['history_key'])]:
                target=Journal(root/folder).path(key);target.parent.mkdir(exist_ok=True);os.link(Journal(source/folder).path(key),target)
        Journal(root/'runs').save(seed_id,parent)
        # Parent projection bytes reuse original byte-identical series when possible.
        import graph_core.market_preview as preview
        real_publish=preview.publish_immutable
        def retained_publish(path,raw):
            if path.name.startswith('series-'):
                candidates=list((source/'preview'/original['result']['id']).glob(path.name))
                if candidates and candidates[0].read_bytes()==raw:
                    path.parent.mkdir(parents=True,exist_ok=True);os.link(candidates[0],path);return 'RETAINED_READ_ONLY_ALIAS'
            return real_publish(path,raw)
        preview.publish_immutable=retained_publish
        try:build(root,seed_id)
        finally:preview.publish_immutable=real_publish
        prepared.append(root)
    captures=[]
    for session in ('2026-11-03','2026-11-04'):
        inputs=destination/('SYNTHETIC-'+session);inputs.mkdir()
        for market,lower in [('TWSE','twse'),('TPEX','tpex')]:
            companies=[];quotes=[];html='最近更新日期:2026/11/02<table><tr><td>CFICode</td></tr>'
            for row in [x for x in selected if x['market']==market]:
                saved=Journal(source/'results').read(row['result_key'])['value'];bar=saved['input']['bars'][-1]
                code=row['code'];name=row['name'];dt=session.replace('-','')
                if market=='TWSE':
                    companies.append({'公司代號':code,'公司簡稱':name});q=dict(Date=dt,Code=code,OpeningPrice=bar['open'],HighestPrice=bar['high'],LowestPrice=bar['low'],ClosingPrice=bar['close'],TradeVolume=bar['volume_shares_scaled'],Change='0')
                else:
                    companies.append(dict(SecuritiesCompanyCode=code,CompanyAbbreviation=name));q=dict(Date=dt,SecuritiesCompanyCode=code,Open=bar['open'],High=bar['high'],Low=bar['low'],Close=bar['close'],TradingShares=bar['volume_shares_scaled'],Change='0')
                q['DU2_SYNTHETIC_NOT_OFFICIAL_NEW_DAY']=True;quotes.append(q)
                html+='<tr>'+''.join('<td>'+str(v)+'</td>' for v in [code+' '+name,row['isin'],row['listed_at'].replace('-','/'),'上市' if market=='TWSE' else '上櫃','',row['cfi'],''])+'</tr>'
            (inputs/(lower+'-universe.json')).write_bytes(encode(companies));(inputs/(lower+'-daily.json')).write_bytes(encode(quotes));(inputs/(market+'-classification.html')).write_bytes((html+'</table>').encode('cp950',errors='xmlcharrefreplace'))
        cap=import_saved(inputs,prepared[0]);captures.append(cap)
        receipt=prepared[0]/'captures'/(cap+'.json');target=prepared[1]/'captures'/receipt.name;target.parent.mkdir(exist_ok=True);os.link(receipt,target)
        for rec in json.loads(receipt.read_bytes()):
            src=prepared[0]/'raw'/rec['sha256'];dst=prepared[1]/'raw'/rec['sha256'];dst.parent.mkdir(exist_ok=True)
            if not dst.exists():os.link(src,dst)
    study=dict(study='SYNTHETIC_NEW_DAY_NOT_REAL_MARKET_VALIDATION',seed=seed_id,captures=captures,selected=[dict(code=s['code'],market=s['market'],stratum=s['study_stratum'],legacy_result_bytes=Journal(source/'results').path(s['result_key']).stat().st_size,history_records=s['history_records']) for s in selected])
    (destination/'STUDY_PRIVATE.json').write_bytes(encode(study))
    print('Prepared bounded study',len(selected),'prefixes; no source requests')


def run(destination,mode):
    root=destination/mode;study=json.loads((destination/'STUDY_PRIVATE.json').read_bytes());measure=[]
    for i,cap in enumerate(study['captures']):
        before=inventory(root);start=time.monotonic();r=m.update(root,seed_run=study['seed'],capture_id=cap,now=datetime(2026,11,6,tzinfo=timezone.utc),storage_mode=mode);wall=time.monotonic()-start
        if r.get('status')=='BLOCKED':raise ValueError(r['reason'])
        after=inventory(root);added=[v for k,v in after.items() if k not in before]
        batch=Journal(root/'runs').read(r['id'])['value']
        measure.append(dict(day=i+1,id=r['id'],new_core_calls=r['new_core_calls'],wall_seconds=wall,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            new_file_bytes=sum(v['bytes'] for v in added),new_allocated_bytes=sum(v['allocated'] for v in added),new_inode_files=len(added),
            by_group={g:sum(v['allocated'] for v in added if v['path'].split('/')[0]==g) for g in {v['path'].split('/')[0] for v in added}},private_preview=r['private_preview'],
            original_sample_qualifications_unchanged=all(not s['data_qualified'] and not s['execution_qualified'] and s['primary_pressure_id'] is None for s in batch['stocks'])))
    before=inventory(root)
    with __import__('unittest.mock',fromlist=['patch']).patch.object(m,'analyze',side_effect=AssertionError('Same source must not calculate')):
        repeat=m.update(root,seed_run=study['seed'],capture_id=study['captures'][-1],now=datetime(2026,11,6,tzinfo=timezone.utc),storage_mode=mode)
    after=inventory(root);assert before==after and repeat['new_core_calls']==0
    (destination/(mode+'-measurement-private.json')).write_bytes(encode(dict(mode=mode,study=study['study'],measurements=measure,repeat_zero_core_and_inode_changes=True)))
    print(mode,'PASS',[(x['day'],x['new_allocated_bytes'],round(x['wall_seconds'],3)) for x in measure])


def compare(destination):
    reports={mode:json.loads((destination/(mode+'-measurement-private.json')).read_bytes()) for mode in ('plain','compact')};comparisons=[]
    for i in range(2):
        batches={mode:Journal(destination/mode/'runs').read(reports[mode]['measurements'][i]['id'])['value'] for mode in reports}
        for a,b in zip(batches['plain']['stocks'],batches['compact']['stocks']):
            assert a==b
            for folder,key in [('results',a['result_key']),('histories',a['history_key'])]:
                left=c.read_bytes(Journal(destination/'plain'/folder).path(key));right=c.read_bytes(Journal(destination/'compact'/folder).path(key));assert left==right
            # Logical series filenames carry exact unchanged raw fingerprints.
            import re
            pages={mode:c.read_bytes(reports[mode]['measurements'][i]['private_preview']['path']) for mode in reports}
            states={mode:json.loads(re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',pages[mode],re.S)[1]) for mode in reports}
            desc=next(s['preview_series'] for s in states['plain']['stocks'] if s['identity']==a['identity'])
            paths={mode:Path(reports[mode]['measurements'][i]['private_preview']['path']).parent/desc['path'] for mode in reports}
            raw=c.read_bytes(paths['plain']);assert raw==c.read_bytes(paths['compact']);assert c.sha(raw)==desc['sha256']
        comparisons.append(dict(day=i+1,stocks=len(batches['plain']['stocks']),results_histories_preview_exact=True,all_null_and_false_qualifications_preserved=True))
    (destination/'comparison-private.json').write_bytes(encode(dict(status='PASS',study='SYNTHETIC_NEW_DAYS_WITH_RETAINED_REAL_PREFIXES',comparisons=comparisons)))
    print('Exact result/history/series comparisons PASS',len(comparisons))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run','compare']);p.add_argument('--source');p.add_argument('--destination',required=True);p.add_argument('--mode',choices=['plain','compact']);a=p.parse_args();dest=m.external(a.destination)
    if a.action=='prepare':prepare(Path(a.source),dest)
    elif a.action=='run':run(dest,a.mode)
    else:compare(dest)
