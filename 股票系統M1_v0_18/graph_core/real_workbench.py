"""M-REAL1: reuse immutable FM3 charts, project saved radar/comparison only.
No recognition, indicator calculation, provider calls or source writes.
"""
import argparse,hashlib,json,os,re,shutil,time
from collections import Counter
from pathlib import Path
from rotation_research import artifact_codec as codec
from rotation_research.store import Journal
from rotation_research.private_portability import private,validate_report,quiet_source
from graph_core.event_radar import project as event_project
from graph_core.stock_comparison import project as comparison_project
from technical_chart.interned_json import unpack

VERSION='real-market-workbench/0.1'
def encode(v):return codec.encoded(v)
def digest(v):return hashlib.sha256(v).hexdigest()

def capacity(root,reserve):
    if shutil.disk_usage(root).free<reserve:raise OSError('CAPACITY_RESERVE_REFUSED_SOURCE_PRESERVED')

def source_check(root,report):
    validate_report(report)
    if str(root)!=report['observed_root']:raise ValueError('AUDITED_SOURCE_ROOT_MISMATCH')
    files={v['path']:v for v in report['files']}
    paths={str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
    if set(paths)!=set(files):raise ValueError('AUDITED_SOURCE_FILE_SET_CHANGED')
    for rel,p in paths.items():
        s=p.stat();r=files[rel]
        if (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)!=(r['bytes'],r['mtime_ns'],r['source_inode'],r['source_device']):raise ValueError('AUDITED_SOURCE_METADATA_CHANGED')
    return files

def bind_chart(chart,saved,stock):
    r=saved['result'];a=r['as_of']
    if chart['code']!=stock['code'] or chart['exchange']!=stock['market'] or stock['as_of']!=a or chart['results']!=[r]:raise ValueError('ORIGINAL_CHART_STOCK_DATE_OR_CORE_MISMATCH')
    if chart['bars']!=saved['input']['bars'] or chart['source']['id']!=r['context']['source_id'] or chart['price_basis_id']!=r['context']['price_basis_id']:raise ValueError('ORIGINAL_CHART_SOURCE_OR_BASIS_MISMATCH')
    if chart['macd']!=saved['indicators']['macd'] or chart['moving_averages']!=saved['indicators']['moving_averages']:raise ValueError('ORIGINAL_INDICATORS_MISMATCH_NO_FALLBACK')

def alias(source,target,descriptor,files,root):
    if not re.fullmatch(r'series-[a-f0-9]{64}\.json',descriptor['path']) or descriptor['path'][7:-5]!=descriptor['sha256']:raise ValueError('INVALID_ORIGINAL_DESCRIPTOR')
    entry=files.get(str(source.relative_to(root)))
    if not entry or entry['bytes']!=descriptor['bytes'] or entry['sha256']!=descriptor['sha256']:raise ValueError('ORIGINAL_DESCRIPTOR_NOT_AUDITED')
    if source.is_symlink():raise ValueError('SOURCE_SYMLINK')
    if not target.exists():os.link(source,target)  # same immutable bytes, never a new multi-GB copy
    if target.is_symlink() or (target.stat().st_ino,target.stat().st_dev)!=(source.stat().st_ino,source.stat().st_dev):raise ValueError('ALIAS_NOT_THE_AUDITED_ORIGINAL')

def projection(saved,stock,chart,descriptor):
    bind_chart(chart,saved,stock)
    radar=event_project(saved['result'],stock)
    comparison=comparison_project(saved,stock,chart['source'])
    r=saved['result']
    overlay=dict(schema='private-workbench-evidence/0.1',identity=stock['identity'],code=stock['code'],market=stock['market'],as_of=stock['as_of'],result_id=r['result_id'],source_id=r['context']['source_id'],price_basis_id=r['context']['price_basis_id'],source_prefix_fingerprint=r['source_prefix_fingerprint'],original_series_sha256=descriptor['sha256'],comparison_evidence=comparison)
    return radar,overlay

def scripts():
    here=Path(__file__).parent
    return '\n'.join((here/p).read_text() for p in ['fm3_20261101/lazy_series.js','fm1_20261101/search.js','obs1_20261102/radar.js','comp1_20261102/compare.js'])

def render_saved_shell(original,state):
    marker=b'<script id="market-state" type="application/json">'
    if original.count(marker)!=1:raise ValueError('ORIGINAL_SHELL_STRUCTURE_UNSUPPORTED')
    prefix=original.split(marker)[0].decode('utf-8')
    # Keep saved payload/canvas/indicator values verbatim; replace only workbench addon.
    payload=json.dumps(state,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('&','\\u0026')
    return (prefix+'<script id="market-state" type="application/json">'+payload+'</script><script>'+scripts()+'</script></body></html>').encode()

def build(source,outbase,audit_manifest,*,reserve_bytes=512*1024*1024,max_new_bytes=512*1024*1024):
    started=time.monotonic();source=private(source);outbase=private(outbase);audit_manifest=private(audit_manifest)
    if source==outbase or outbase.is_relative_to(source) or source.is_relative_to(outbase):raise ValueError('NEW_EXTERNAL_OUTPUT_REQUIRED')
    if not outbase.parent.is_dir():raise ValueError('EXISTING_PRIVATE_PARENT_REQUIRED')
    capacity(outbase.parent,reserve_bytes+16*1024*1024)
    report=json.loads(audit_manifest.read_bytes())
    with quiet_source(source):
        files=source_check(source,report)
        original_state=json.loads((source/'fm3-continuation.json').read_bytes())
        if original_state['status']!='FINISHED_COHORT_WITH_EXPLICIT_QUALIFICATIONS':raise ValueError('FM3_NOT_FINISHED')
        batch=Journal(source/'runs').read(original_state['result']['id'])['value']
        page=Path(original_state['preview']['path']);raw=codec.read_bytes(page,expected_bytes=original_state['preview']['bytes'],expected_sha=original_state['preview']['sha256'])
        state=json.loads(re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)[1])
        if [{k:v for k,v in s.items() if k!='preview_series'} for s in state['stocks']]!=batch['stocks']:raise ValueError('ORIGINAL_REFERENCE_OR_TERMINAL_MISMATCH')
        code_binding=digest(Path(__file__).read_bytes()+scripts().encode()+Path(comparison_project.__code__.co_filename).read_bytes()+Path(event_project.__code__.co_filename).read_bytes())
        build_id=digest(encode(dict(version=VERSION,original_preview_sha256=digest(raw),code_binding=code_binding)))
        output=outbase/build_id;output.mkdir(mode=0o700,parents=True,exist_ok=True)
        if output.stat().st_dev!=source.stat().st_dev:raise ValueError('SAME_FILESYSTEM_ALIAS_REQUIRED_NO_IMPLICIT_COPY')
        completed=output/'integration-private.json'
        if completed.is_file():
            old=json.loads(completed.read_bytes())
            if old['build_id']!=build_id or old['original_preview_sha256']!=digest(raw):raise ValueError('PUBLISHED_BUILD_BINDING_MISMATCH')
            from graph_core_chart.mobile_private import preview_index
            codec.read_bytes(Path(old['preview']['path']),expected_bytes=old['preview']['bytes'],expected_sha=old['preview']['sha256'])
            _,_,summary,_=preview_index(old['preview']['path'])
            if summary['stocks']!=len(state['stocks']) or summary['charts']!=old['charts_bound']:raise ValueError('PUBLISHED_BUILD_INCOMPLETE')
            return dict(old,reused_completed_build=True)
        state['radar']={};state['workbench_integration']=dict(version=VERSION,original_preview_sha256=digest(raw),saved_core_only=True,formal_signal=False)
        # Original historical summary may say PARTIAL; retain it explicitly, do not silently mislabel new UI.
        state['summary']=dict(batch['summary'],original_saved_summary=batch['summary'],status=original_state['status'],integration_version=VERSION)
        aliases=overlay_bytes=events=event_stocks=0;stock_counts=Counter();radar_refused=[]
        for i,stock in enumerate(state['stocks']):
            stock_counts[stock['status']]+=1
            if not stock.get('result_key'):continue
            capacity(output,reserve_bytes)
            descriptor=stock['preview_series'];original=page.parent/descriptor['path']
            chart=unpack(json.loads(codec.read_bytes(original,expected_bytes=descriptor['bytes'],expected_sha=descriptor['sha256'])))
            saved=Journal(source/'results').read(stock['result_key'])['value']
            radar,overlay=projection(saved,stock,chart,descriptor)
            state['radar'][stock['identity']]=radar
            events+=len(radar['events']);event_stocks+=bool(radar['events'])
            data=encode(overlay);name='series-'+digest(data)+'.json'
            codec.publish(output/name,data,root=output)
            stock['preview_evidence']=dict(path=name,sha256=digest(data),bytes=len(data))
            alias(original,output/descriptor['path'],descriptor,files,source);aliases+=1;overlay_bytes+=len(data)
            if i%50==0:print(json.dumps(dict(phase='SAVED_PROJECTION_ONLY',processed=i+1,charts=aliases)),flush=True)
            # Account for stored new payloads only, not hardlink aliases to old data.
            if i%50==0 and allocated_new(output,files)>max_new_bytes:raise OSError('NEW_ARTIFACT_BUDGET_REFUSED_PARTIAL_PRESERVED')
            del chart,saved,overlay
        html=render_saved_shell(raw,state);name='market-real1-v01.html';codec.publish(output/name,html,root=output)
        preview=dict(path=str(output/name),bytes=len(html),sha256=digest(html),stocks=len(state['stocks']),charts=aliases,as_of=batch['as_of'])
        metrics=dict(status='PASS_REAL_SAVED_INTEGRATION',version=VERSION,build_id=build_id,original_preview_sha256=digest(raw),reused_completed_build=False,source_run=original_state['result']['id'],as_of=batch['as_of'],reference_count=len(state['stocks']),terminal_counts=dict(stock_counts),charts_bound=aliases,chart_sha_and_complete_saved_values_verified=aliases,comparison_projections=aliases,current_candidate_event_records=events,current_event_stock_count=event_stocks,radar_projection_refused=radar_refused,original_payload_copies=0,reused_hardlinks=aliases,overlay_logical_bytes=overlay_bytes,html_logical_bytes=len(html),new_allocated_bytes=allocated_new(output,files),wall_seconds=time.monotonic()-started,core_runs=0,provider_requests=0,formal_trade_signals=0,android='NOT_TESTED_NEW_BUILD',external_deployment=False,preview=preview)
        codec.immutable(output/'integration-private.json',encode(metrics))
        # Metadata check excludes nlink: the only source change is additional read-only aliases.
        source_check(source,report)
        return metrics

def allocated_new(root,files):
    old={(f['source_device'],f['source_inode']) for f in files.values()};seen=set();n=0
    for p in [root,*root.rglob('*')]:
        s=p.lstat();key=(s.st_dev,s.st_ino)
        if key not in old and key not in seen:n+=s.st_blocks*512;seen.add(key)
    return n

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--audit-manifest',required=True);p.add_argument('--receipt',required=True);a=p.parse_args()
    result=build(a.source,a.output,a.audit_manifest);codec.immutable(private(a.receipt),encode(result));print(json.dumps({k:v for k,v in result.items() if k!='preview'},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
