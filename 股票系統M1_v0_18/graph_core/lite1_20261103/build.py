"""Small immutable view/shards over saved DAY1/FM3. No provider/core calls.
Original charts are explicit owner-allowlisted references, never copied.
"""
import argparse,contextlib,json,hashlib,math,re,resource,shutil,time
from pathlib import Path
from collections import Counter,defaultdict
from unittest.mock import patch
from rotation_research import artifact_codec as c
from rotation_research.store import Journal
from rotation_research.private_portability import private,quiet_source,validate_report
from graph_core.lite1_20261103 import decision

RESERVE=512*1024*1024
MAX_NEW=224*1024*1024
HERE=Path(__file__).parent
def encoded(v):return c.encoded(v)
def digest(v):return hashlib.sha256(v).hexdigest()

@contextlib.contextmanager
def budget(root,*,reserve=RESERVE,limit=MAX_NEW):
    original=c.immutable;used=0
    def write(path,raw):
        nonlocal used
        p=Path(path)
        if not p.resolve().is_relative_to(root.resolve()):raise ValueError('LITE_WRITE_OUTSIDE_NEW_ROOT')
        if not p.exists():
            amount=math.ceil(len(raw)/4096)*4096
            if used+amount>limit or shutil.disk_usage(root).free<reserve+amount+65536:raise OSError('LITE_CAPACITY_REFUSAL_ORIGINALS_PRESERVED')
            value=original(p,raw);used+=p.stat().st_blocks*512;return value
        return original(p,raw)
    with patch.object(c,'immutable',write):yield

def state_of(path):
    raw=c.read_bytes(path);match=re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)
    if not match:raise ValueError('SAVED_WORKBENCH_REQUIRED')
    return json.loads(match[1]),digest(raw),len(raw)

def source_manifest_check(root,report):
    validate_report(report)
    if report['observed_root']!=str(root):raise ValueError('WRONG_AUDITED_ROOT')
    known={x['path']:x for x in report['files']}
    files={str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
    if set(files)!=set(known):raise ValueError('AUDITED_FILE_SET_CHANGED')
    for rel,p in files.items():
        s=p.stat();f=known[rel]
        if (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)!=(f['bytes'],f['mtime_ns'],f['source_inode'],f['source_device']):raise ValueError('SOURCE_METADATA_CHANGED')
    return known

def prepare(root,output,audit_path,old_workbench):
    root=private(root);output=private(output);audit_path=private(audit_path);old_workbench=private(old_workbench)
    if output.is_relative_to(root) or root.is_relative_to(output):raise ValueError('NEW_SEPARATE_PRIVATE_OUTPUT_REQUIRED')
    if output.exists():raise FileExistsError('PRESERVE_PRIOR_LITE_BUILD_USE_NEW_VERSION')
    if shutil.disk_usage(output.parent).free<RESERVE+MAX_NEW+32*1024*1024:raise OSError('LITE_PREFLIGHT_CAPACITY')
    started=time.monotonic();audit=json.loads(audit_path.read_bytes());before_free=shutil.disk_usage(root).free
    output.mkdir(mode=0o700);all_receipts=[]
    with quiet_source(root):
      known=source_manifest_check(root,audit)
      head=json.loads((root/'current-increment-run.json').read_bytes());fm3=json.loads((root/'fm3-continuation.json').read_bytes())
      sources=[dict(run_id=head['id'],path=head['private_preview']['path'],original=head['private_preview']['path']),
               dict(run_id=fm3['result']['id'],path=str(old_workbench),original=fm3['preview']['path'])]
      with budget(output):
       for source in sources:
        batch=Journal(root/'runs').read(source['run_id'])['value'];state,source_sha,source_bytes=state_of(Path(source['path']))
        if len(state['stocks'])!=len(batch['stocks']):raise ValueError('SOURCE_REFERENCE_COUNT')
        folder=output/batch['as_of'];folder.mkdir(mode=0o700);data=[];charts=[];stocks=[];event_groups={};types=set();original_total=0;restored_total=0;result_reads=0
        dates=set()
        def packet(value):
            body=encoded(value);sha=digest(body);name='series-'+sha+'.json'
            c.publish(folder/name,body,root=folder)
            if c.read_bytes(folder/name,expected_sha=sha,expected_bytes=len(body))!=body:raise ValueError('NEW_SHARD_READBACK')
            desc=dict(path=name,sha256=sha,bytes=len(body));data.append(desc);return desc
        for index,stock in enumerate(state['stocks']):
            s={k:stock[k] for k in ('identity','code','name','market','as_of','status','result_key')}
            idx=state.get('radar',{}).get(s['identity']);result=None
            if not stock.get('result_key'):d=decision.empty(stock)
            else:
                if not idx:raise ValueError('MISSING_EXISTING_RADAR_NOT_RECOMPUTED')
                d=decision.blocked(stock,idx)
                if d is None:
                    saved=Journal(root/'results').read(stock['result_key'])['value'];result_reads+=1;result=saved['result']
                    if result['result_id']!=idx['result_id'] or result['context']['source_id']!=idx['source_id'] or result['context']['price_basis_id']!=idx['price_basis_id']:raise ValueError('RESULT_RADAR_BINDING')
                    d=decision.project(stock,result)
                desc=stock['preview_series'];src=Path(source['original']).parent/desc['path'];rel=str(src.relative_to(root));info=c.info(src)
                if rel+'.du2' not in known and rel not in known:raise ValueError('UNREGISTERED_ORIGINAL_CHART')
                if info['bytes']!=desc['bytes']:raise ValueError('ORIGINAL_CHART_DESCRIPTOR')
                s['preview_series']=desc
                charts.append(dict(route=desc['path'],source_path=str(src),identity=s['identity'],as_of=s['as_of'],bytes=desc['bytes'],sha256=desc['sha256']))
            d.update(batch_id=source['run_id'],source_preview_sha256=source_sha)
            detail=packet(dict(schema='lite-decision/0.1',identity=s['identity'],as_of=s['as_of'],decision=d))
            s.update(decision=decision.card(d),decision_detail=detail);stocks.append(s)
            group=defaultdict(list);events=idx.get('events',[]) if idx else [];original_total+=len(events)
            for i,event in enumerate(events):
                if event['first_observed_at']>s['as_of'] or event['date']>s['as_of']:raise ValueError('FUTURE_RADAR_EVENT')
                types.add(event['type']);dates.add(event['first_observed_at']);group[(event['first_observed_at'],event['type'])].append(dict(source_index=i,event=event))
            pages={};reconstructed=[]
            for (date,kind),records in group.items():
                pages[(date,kind)]=[]
                for start in range(0,len(records),50):
                    piece=records[start:start+50]
                    value=dict(schema='lite-events/0.1',identity=s['identity'],as_of=s['as_of'],batch_id=source['run_id'],source_preview_sha256=source_sha,binding=d['binding'],event_type=kind,observed_date=date,records=piece)
                    desc=packet(value);check=json.loads(c.read_bytes(folder/desc['path']))
                    reconstructed.extend(check['records']);pages[(date,kind)].append(desc)
            actual=[x['event'] for x in sorted(reconstructed,key=lambda x:x['source_index'])]
            if actual!=events:raise ValueError('EVENT_LOSS_OR_CHANGE_AFTER_SHARDING')
            restored_total+=len(actual);event_groups[s['identity']]=dict(pages=pages,counts={k:len(v) for k,v in group.items()})
            if index==0 or (index+1)%100==0:print(json.dumps(dict(phase='SAVED_FACTS_ONLY',as_of=batch['as_of'],processed=index+1,result_reads=result_reads)),flush=True)
        routes={}
        for date in ['ALL',*sorted(dates)]:
         for kind in ['ALL',*sorted(types)]:
          for market in ['ALL','TWSE','TPEX']:
            rows=[];total=0
            for s in stocks:
                if market!='ALL' and s['market']!=market:continue
                group=event_groups[s['identity']];selected=[key for key in group['counts'] if (date=='ALL' or key[0]==date) and (kind=='ALL' or key[1]==kind)]
                count=sum(group['counts'][key] for key in selected)
                if count:
                    rows.append(dict(identity=s['identity'],event_count=count,event_pages=[desc for key in selected for desc in group['pages'][key]]));total+=count
            descriptors=[]
            for start in range(0,len(rows),50):
                value=dict(schema='lite-radar/0.1',as_of=batch['as_of'],batch_id=source['run_id'],source_preview_sha256=source_sha,query=dict(date=date,type=kind,market=market,page=start//50),stock_count=len(rows),event_count=total,rows=rows[start:start+50])
                descriptors.append(packet(value))
            routes['|'.join((date,kind,market))]=dict(stock_count=len(rows),event_count=total,pages=descriptors)
        asset=encoded(dict(schema='private-lite-linked-assets/0.1',charts=charts,data=list({x['path']:x for x in data}.values())))
        ash=digest(asset);aname='assets-'+ash+'.json';c.immutable(folder/aname,asset)
        lite=dict(schema='private-lite-workbench/0.1',summary=dict(as_of=batch['as_of'],expected=len(stocks),charts=len(charts),status=batch['summary']['status']),stocks=stocks,radar_routes=routes,radar_dates=sorted(dates),radar_types=sorted(types),batch_id=source['run_id'],source_preview_sha256=source_sha,asset_index=dict(path=aname,sha256=ash,bytes=len(asset)))
        c.immutable(folder/'prepared-state-private.json',encoded(lite))
        receipt=dict(as_of=batch['as_of'],folder=str(folder),source_run=source['run_id'],source_preview_sha256=source_sha,source_html_bytes=source_bytes,stocks=len(stocks),charts=len(charts),original_events=original_total,restored_events=restored_total,event_stock_count=sum(bool(x['counts']) for x in event_groups.values()),result_reads=result_reads,data_shards=len(data),decision_counts=dict(Counter(s['decision']['headline'] for s in stocks)),all_original_events_exact=True,core_calls=0,indicator_calls=0,provider_calls=0)
        all_receipts.append(receipt);c.immutable(folder/'preparation-private.json',encoded(receipt))
        del state,event_groups
      source_manifest_check(root,audit)
    report=dict(status='PREPARED_ORIGINAL_FACTS_EXACT',batches=all_receipts,elapsed_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,free_before_bytes=before_free,free_after_bytes=shutil.disk_usage(output).free,maximum_new_regular_file_budget=MAX_NEW,minimum_free_bytes=RESERVE,original_sources_unchanged=True)
    c.immutable(output/'preparation-private.json',encoded(report));return report

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--output',required=True);a.add_argument('--audit',required=True);a.add_argument('--old-workbench',required=True);v=a.parse_args();print(json.dumps(prepare(v.root,v.output,v.audit,v.old_workbench)),flush=True)
