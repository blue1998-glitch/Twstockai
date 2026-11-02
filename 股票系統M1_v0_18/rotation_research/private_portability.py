"""M-PORT1: private local preflight, immutable inventory and isolated restore.

No engine, provider API, external service, DB, source repair or in-place move.
Detailed file manifests and errors must stay outside Git. CLI stdout is aggregate.
"""
import argparse,contextlib,fcntl,hashlib,json,math,os,re,shutil,stat,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from rotation_research.store import Journal
from rotation_research import artifact_codec as codec
from technical_chart.interned_json import unpack

VERSION='private-portability/0.1'
FINMIND_ENDPOINT='https://api.finmindtrade.com/api/v4/data'
JOURNALS=('runs','results','histories','source-receipts','source-slots','checkpoints','du1-checkpoints')
SECRET=re.compile(r'(^\.env($|\.)|credentials?|(^|[-_.])auth([-_.]|$)|\.(pem|key|p12|pfx)$)',re.I)


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encode(v):return codec.encoded(v)
def fingerprint(v):return 'sha256:'+digest(encode(v)[:-1])
def timestamp():return datetime.now(timezone.utc).isoformat()


def private(path):
    p=Path(path).expanduser().absolute()
    if any(a.is_symlink() for a in (p,*p.parents)):raise ValueError('PRIVATE_PATH_SYMLINK')
    p=p.resolve()
    if any((a/'.git').exists() for a in (p,*p.parents)):raise ValueError('PRIVATE_PATH_INSIDE_GIT')
    return p


def bounded(root,rel):
    if not isinstance(rel,str) or not rel or Path(rel).is_absolute() or '..' in Path(rel).parts or '\\' in rel:raise ValueError('UNSAFE_RELATIVE_PATH')
    p=root/rel
    if not p.resolve().is_relative_to(root) or any(a.is_symlink() for a in (p,*p.parents)):raise ValueError('OUTSIDE_ROOT_OR_SYMLINK')
    return p


def relocate(value,root,original_root):
    p=Path(value)
    if not p.is_absolute():return bounded(root,str(p))
    try:rel=p.relative_to(original_root)
    except ValueError:raise ValueError('ABSOLUTE_BINDING_OUTSIDE_SOURCE') from None
    return bounded(root,str(rel))


def file_hash(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            raw=f.read(1024*1024)
            if not raw:break
            h.update(raw)
    return h.hexdigest()


@contextlib.contextmanager
def quiet_source(root):
    """Existing file opened read-only; never create/remove a source lock."""
    for name in ('fm3-writer.lock','fm3-continuation.lock'):
        if (root/name).exists():raise ValueError('SOURCE_WRITER_OR_STALE_LOCK_REQUIRES_REVIEW')
    lock=root/'daily.lock';f=None
    try:
        if lock.exists():
            if lock.is_symlink():raise ValueError('SOURCE_LOCK_SYMLINK')
            f=lock.open('rb');fcntl.flock(f,fcntl.LOCK_SH|fcntl.LOCK_NB)
        yield
    finally:
        if f:f.close()


def inventory(root):
    records=[];errors=[];seen={};groups={};physical=0
    for base,dirs,files in os.walk(root,followlinks=False):
        for name in list(dirs):
            p=Path(base)/name
            if p.is_symlink() or name=='.git':errors.append(dict(path=str(p.relative_to(root)),code='UNSAFE_DIRECTORY'));dirs.remove(name)
        for name in sorted(files):
            p=Path(base)/name;rel=str(p.relative_to(root));s=p.lstat()
            if not stat.S_ISREG(s.st_mode):errors.append(dict(path=rel,code='NONREGULAR_FILE'));continue
            if SECRET.search(name):errors.append(dict(path=rel,code='POTENTIAL_PRIVATE_CREDENTIAL_REQUIRES_REVIEW'));continue
            inode=(s.st_dev,s.st_ino)
            if inode not in seen:
                seen[inode]=file_hash(p);groups[inode]='h'+str(len(groups));physical+=s.st_blocks*512
            after=p.stat()
            if (s.st_size,s.st_mtime_ns,s.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):errors.append(dict(path=rel,code='SOURCE_CHANGED_DURING_HASH'))
            records.append(dict(path=rel,bytes=s.st_size,sha256=seen[inode],mode=stat.S_IMODE(s.st_mode),mtime_ns=s.st_mtime_ns,
                hardlink_group=groups[inode],source_inode=s.st_ino,source_device=s.st_dev,source_nlink=s.st_nlink))
    return sorted(records,key=lambda x:x['path']),errors,physical


def dependencies(root,records):
    """Resolve DU2 read and future-append anchors; no implicit external closure."""
    known={r['path'] for r in records};edges=[];issues=[];logical=[]
    for entry in records:
        if not entry['path'].endswith('.du2'):continue
        rel=entry['path'][:-4];p=bounded(root,rel)
        try:
            anchor,v=codec.manifest(p)
            if not anchor.is_relative_to(root):raise ValueError('EXTERNAL_CODEC_ROOT')
            required=[anchor/'.du2-root.json']
            if v['schema']==codec.INTERNED:
                for key in ('wire_path','anchor_path'):
                    q=codec.resolve(anchor,v[key]);required.append(q if q.is_file() else codec.sidecar(q))
                # All read bytes are still checksum-bound by the codec.
            else:
                for piece in v['pieces']:
                    required.append(codec.resolve(anchor,piece['path']) if piece['kind']=='span' else codec.blob_path(anchor,piece['sha256']))
            for q in required:
                if not q.is_relative_to(root) or str(q.relative_to(root)) not in known:raise ValueError('MISSING_OR_EXTERNAL_CODEC_DEPENDENCY')
                edges.append(dict(artifact=entry['path'],dependency=str(q.relative_to(root))))
            raw=codec.read_bytes(p,expected_bytes=v['bytes'],expected_sha=v['sha256'])
            logical.append(dict(path=rel,bytes=len(raw),sha256=digest(raw)))
        except Exception as e:issues.append(dict(path=entry['path'],code='CODEC_DEPENDENCY_OR_CONTENT_INVALID',error_type=type(e).__name__))
    return edges,logical,issues


def journal_roots(root):
    for folder in JOURNALS:
        directory=root/folder
        if not directory.exists():continue
        keys={p.name[:-5] for p in directory.glob('*.json')}
        keys.update(p.name[:-9] for p in directory.glob('*.json.du2'))
        for key in sorted(keys):yield folder,key


def fm3_bindings(root,original_root,records):
    """Adapt the original FM3 saved-result audit, with stdlib-only reads.
    No indicators, pattern recognition, source acquisition or qualification RUN.
    """
    paths={r['path']:r for r in records};checked=set();counts=Counter();issues=[];views=[]
    def read(folder,key):
        record=Journal(root/folder).read(key);checked.add((folder,key));return record['value']
    def raw_sha(rel,expected):
        p=bounded(root,rel);record=paths.get(str(p.relative_to(root)))
        if not record or record['sha256']!=expected:raise ValueError('RAW_SOURCE_FINGERPRINT_MISSING_OR_CHANGED')
    state=json.loads((root/'fm3-continuation.json').read_bytes())
    if state['status']!='FINISHED_COHORT_WITH_EXPLICIT_QUALIFICATIONS':raise ValueError('FM3_COHORT_NOT_FINISHED')
    batch=read('runs',state['result']['id'])
    if batch.get('version')!='finmind-market-history/0.1':raise ValueError('ORIGINAL_FM3_VERSION_BINDING')
    reference=read('runs',batch['reference_current_run'])
    rows=batch['stocks'];identities=[r['identity'] for r in rows]
    if len(set(identities))!=len(rows) or set(identities)!={r['identity'] for r in reference['stocks']}:raise ValueError('REFERENCE_COHORT_MISMATCH')
    if len(rows)!=batch['summary']['expected'] or len(rows)!=batch['summary']['processed']:raise ValueError('DECLARED_TERMINALS_INCOMPLETE')
    html=relocate(state['preview']['path'],root,original_root)
    page=codec.read_bytes(html,expected_bytes=state['preview']['bytes'],expected_sha=state['preview']['sha256'])
    match=re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',page,re.S)
    if not match:raise ValueError('PREVIEW_STOCK_INDEX_MISSING')
    visible=json.loads(match[1]);display={s['identity']:s for s in visible['stocks']}
    if len(display)!=len(rows) or set(display)!=set(identities):raise ValueError('PREVIEW_COHORT_MISMATCH')
    for stock in rows:
        identity=stock['identity']
        try:
            if stock['status'] not in ('ANALYZED_FINMIND_HISTORY','INSUFFICIENT_HISTORY','DATA_QUALITY_REFUSED','MISSING_ANCHOR_QUOTE'):raise ValueError('UNFINISHED_OR_UNKNOWN_TERMINAL')
            ui={k:v for k,v in display[identity].items() if k!='preview_series'}
            if ui!=stock:raise ValueError('PREVIEW_STOCK_METADATA_DIFFERS')
            params=dict(dataset='TaiwanStockPrice',data_id=stock['code'],start_date=max(batch['summary']['requested_start'],stock['listed_at']),end_date=batch['as_of'])
            key=digest(encode(dict(endpoint=FINMIND_ENDPOINT,parameters=params)))
            receipt=read('source-receipts',key)
            if receipt['parameters']!=params or receipt['endpoint']!=FINMIND_ENDPOINT or receipt['status']!='RECEIVED':raise ValueError('SOURCE_RECEIPT_BINDING')
            raw_sha('source-raw/'+receipt['sha256'],receipt['sha256']);counts['stock_raw_sources']+=1
            for field in ('data_qualified','execution_model_qualified','historical_signal_eligible','policy_authorized','live_execution_authorized'):
                if stock[field] is not False:raise ValueError('QUALIFICATION_CHANGED')
            if stock['primary_pressure_id'] is not None:raise ValueError('PRESSURE_QUALIFICATION_CHANGED')
            if not stock.get('result_key'):counts['terminal_without_chart']+=1;continue
            saved=read('results',stock['result_key']);payload=saved['input'];result=saved['result']
            if stock['result_key']!='fm3-result-'+digest(encode(saved)) or saved['acquisition']!=receipt:raise ValueError('RESULT_RECEIPT_FINGERPRINT')
            if result['schema_version']!='graph-recognition-research/0.2' or result['context']!=payload['context']:raise ValueError('CORE_VERSION_OR_CONTEXT')
            if result['as_of']!=batch['as_of'] or result['context']['code']!=stock['code'] or result['context']['exchange']!=stock['market']:raise ValueError('STOCK_CUTOFF_BINDING')
            rcopy=dict(result);rid=rcopy.pop('result_id')
            if fingerprint(rcopy)!=rid:raise ValueError('SAVED_CORE_FINGERPRINT_CHANGED')
            hist=read('histories',stock['history_key'])
            if hist['bars']!=payload['bars'] or hist['basis_break_dates']!=payload.get('basis_break_dates',[]):raise ValueError('HISTORY_PAYLOAD_MISMATCH')
            if result['source_records']!=len(payload['bars']) or any(b['date']>batch['as_of'] for b in payload['bars']):raise ValueError('SOURCE_PREFIX_CUTOFF')
            if not saved['official_comparison']['matched']:raise ValueError('SAVED_OFFICIAL_PAIR_NOT_MATCHED')
            desc=display[identity]['preview_series']
            if not re.fullmatch('series-[0-9a-f]{64}\\.json',desc['path']) or desc['path'][7:-5]!=desc['sha256']:raise ValueError('UNSAFE_PREVIEW_DESCRIPTOR')
            chunk=codec.read_bytes(html.parent/desc['path'],expected_bytes=desc['bytes'],expected_sha=desc['sha256'])
            series=unpack(json.loads(chunk))
            if series['code']!=stock['code'] or series['exchange']!=stock['market'] or series['bars']!=payload['bars'] or series['results']!=[result]:raise ValueError('CHART_CORE_OR_CANDLES_MISMATCH')
            if series['macd']!=saved['indicators']['macd'] or series['moving_averages']!=saved['indicators']['moving_averages']:raise ValueError('CHART_SAVED_INDICATOR_MISMATCH')
            counts['results_histories_charts']+=1
        except Exception as e:issues.append(dict(identity=identity,code='FM3_BINDING_INVALID',error_type=type(e).__name__))
    if counts['results_histories_charts']!=state['preview']['charts'] or counts['results_histories_charts']!=sum(bool(s.get('result_key')) for s in rows):issues.append(dict(code='CHART_COUNT_INCOMPLETE'))
    views.append(dict(kind='fm3',path=str(html.relative_to(root)),sha256=state['preview']['sha256'],bytes=state['preview']['bytes'],as_of=batch['as_of'],run_id=state['result']['id']))
    return dict(dataset_class=state.get('data_class','ORIGINAL_SAVED_FM3_NOT_NEW_PROVIDER_VALIDATION'),reference_count=len(rows),reference_by_market=dict(Counter(s['market'] for s in rows)),terminal_counts=dict(Counter(s['status'] for s in rows)),checks=dict(counts),views=views),checked,issues


def pointer_bindings(root,original_root):
    views=[];issues=[]
    # Current DU1/DU2 pointer and immutable batch catalogues are copied as-is.
    # Relocated access overlays are written separately after verified restore.
    for head in ('current-increment-run.json','current-finmind-run.json','current-run.json'):
        p=root/head
        if not p.exists():continue
        try:
            state=json.loads(p.read_bytes());bound_batch=Journal(root/'runs').read(state['id'])['value']
            desc=state.get('private_preview')
            if desc and 'path' in desc:
                page=relocate(desc['path'],root,original_root);codec.read_bytes(page,expected_sha=desc['sha256'],expected_bytes=desc['bytes'])
                views.append(dict(kind=head,path=str(page.relative_to(root)),sha256=desc['sha256'],bytes=desc['bytes'],run_id=state['id'],as_of=bound_batch['as_of']))
            if state.get('batch_index'):
                index=relocate(state['batch_index'],root,original_root);v=json.loads(index.read_bytes())
                if v['schema']!='private-saved-batches/0.1':raise ValueError('BATCH_INDEX_SCHEMA')
                for entry in v['batches']:
                    page=relocate(entry['path'],root,original_root);codec.read_bytes(page,expected_sha=entry['sha256'],expected_bytes=entry['bytes'])
        except Exception as e:issues.append(dict(path=head,code='CURRENT_POINTER_INVALID',error_type=type(e).__name__))
    return views,issues


def journal_references(root,files):
    """Known saved-store edges in old runs/checkpoints and DU2 row bindings.
    Excludes IDs that are fingerprints/JSON pointers rather than Journal keys.
    """
    known={f['path'] for f in files};edges=[];issues=[]
    mapping={'result_key':'results','seed_result_key':'results','history_key':'histories',
        'reference_current_run':'runs','parent_run':'runs','seed_run':'runs','correction_of':'runs'}
    def walk(value,source):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in mapping and v:
                    try:
                        target=Journal(root/mapping[k]).path(v)
                        rel=str(target.relative_to(root))
                        if rel not in known and rel+'.du2' not in known:raise ValueError('JOURNAL_TARGET_MISSING')
                        edges.append(dict(artifact=source,field=k,dependency=rel))
                    except Exception:issues.append(dict(path=source,code='JOURNAL_REFERENCE_MISSING_OR_INVALID',field=k))
                elif k not in ('bars','input','result','indicators','macd','moving_averages'):walk(v,source)
        elif isinstance(value,list):
            for item in value:walk(item,source)
    for folder,key in journal_roots(root):
        # Original results are independently content-bound in the FM3 audit;
        # their continuation edges are duplicated in immutable run stock rows.
        if folder in ('results','histories','source-receipts','source-slots'):continue
        try:walk(Journal(root/folder).read(key)['value'],folder+'/'+key)
        except Exception as e:issues.append(dict(path=folder+'/'+key,code='JOURNAL_REFERENCE_CONTAINER_INVALID',error_type=type(e).__name__))
    return edges,issues


def preview_and_capture_references(root,files,logical):
    known={f['path']:f for f in files};known.update({v['path']:v for v in logical});edges=[];issues=[]
    pages=sorted(name for name in known if name.endswith('.html'))
    for name in pages:
        try:
            raw=codec.read_bytes(bounded(root,name));m=re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)
            if not m:raise ValueError('UNRECOGNIZED_SAVED_PREVIEW')
            state=json.loads(m[1]);parent=Path(name).parent
            for row in state['stocks']:
                desc=row.get('preview_series')
                if not desc:continue
                if not re.fullmatch('series-[0-9a-f]{64}\\.json',desc['path']):raise ValueError('UNSAFE_SERIES_PATH')
                rel=str(parent/desc['path']);asset=known.get(rel)
                if not asset or asset['bytes']!=desc['bytes'] or asset['sha256']!=desc['sha256'] or desc['path'][7:-5]!=desc['sha256']:raise ValueError('SAVED_PREVIEW_DEPENDENCY_MISSING_OR_CHANGED')
                edges.append(dict(artifact=name,dependency=rel))
        except Exception as e:issues.append(dict(path=name,code='PREVIEW_REFERENCE_INVALID',error_type=type(e).__name__))
    directory=root/'captures'
    if directory.exists():
        for path in directory.glob('*.json'):
            try:
                receipts=json.loads(path.read_bytes())
                if not re.fullmatch('[0-9a-f]{64}',path.stem) or digest(encode(receipts))!=path.stem:raise ValueError('CAPTURE_MANIFEST_FINGERPRINT')
                for r in receipts:
                    if r['status']!='RECEIVED':continue  # retain rejected acquisition, do not invent raw
                    rel='raw/'+r['sha256'];raw=known.get(rel)
                    if not raw or raw['sha256']!=r['sha256'] or raw['bytes']!=r['bytes']:raise ValueError('CAPTURE_RAW_MISSING_OR_CHANGED')
                    edges.append(dict(artifact=str(path.relative_to(root)),dependency=rel))
            except Exception as e:issues.append(dict(path=str(path.relative_to(root)),code='CAPTURE_REFERENCE_INVALID',error_type=type(e).__name__))
    return edges,issues


def reader_requirements():
    here=Path(__file__).resolve().parent;project=here.parent
    modules=[here/'store.py',here/'artifact_codec.py',project/'technical_chart/interned_json.py']
    return dict(journal='rotation-record/0.1',byte_codec=codec.VERSION,interned_codec=codec.INTERNED,
        graph_result='graph-recognition-research/0.2',fm3_producer='finmind-market-history/0.1',
        module_sha256={str(p.relative_to(project)):file_hash(p) for p in modules},
        restore_tool=VERSION,opaque_unknown_producer_business_rules='NOT_CERTIFIED')


def complete_reference_audit(root,report):
    """Supplement an already hashed in-session private inventory without
    repeating the full numerical-object read. Requires unchanged file metadata.
    Not a new independent SHA audit: original observed_at remains recorded.
    """
    validate_report(report,require_reference_audit=False);root=private(root)
    if str(root)!=report['observed_root']:raise ValueError('SUPPLEMENT_ROOT_MISMATCH')
    with quiet_source(root):
        current={str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
        if set(current)!={f['path'] for f in report['files']}:raise ValueError('SOURCE_SET_CHANGED_REINSPECTION_REQUIRED')
        for f in report['files']:
            s=current[f['path']].stat()
            if (s.st_size,s.st_mtime_ns,s.st_ino)!=(f['bytes'],f['mtime_ns'],f['source_inode']):raise ValueError('SOURCE_CHANGED_REINSPECTION_REQUIRED')
        edges,issues=journal_references(root,report['files'])
        other_edges,problems=preview_and_capture_references(root,report['files'],report['logical_artifacts']);issues.extend(problems)
    result=dict(report);result.pop('manifest_id');result['issues']=report['issues']+issues
    result.update(reader_requirements=reader_requirements(),journal_reference_edges=edges,preview_capture_edges=other_edges,journal_references_verified=True,reference_audit_at=timestamp(),base_private_manifest_id=report['manifest_id'])
    result['status']='PREFLIGHT_COMPLETE' if not result['issues'] else 'BLOCKED_INCOMPLETE_OR_UNSAFE'
    result['manifest_id']=digest(encode(result));return result


def inspect(root,*,profile='fm3',original_root=None):
    started=time.monotonic();root=private(root);original_root=Path(original_root).absolute() if original_root else root
    if root in (Path('/'),Path('/workspace'),Path('/tmp'),Path('/home'),Path('/proc'),Path('/sys'),Path('/etc'),Path.home()):raise ValueError('SPECIFIC_PRIVATE_DATA_ROOT_REQUIRED')
    if not root.is_dir():return dict(schema=VERSION,status='SOURCE_UNAVAILABLE',source_root=str(root),observed_at=timestamp(),issues=[dict(code='SOURCE_ROOT_NOT_FOUND')],files=[],profile=profile)
    with quiet_source(root):
        files,issues,allocated=inventory(root);edges,logical,problems=dependencies(root,files);issues.extend(problems)
        checks=set();semantics={}
        if profile=='fm3':
            try:semantics,checks,problems=fm3_bindings(root,original_root,files);issues.extend(problems)
            except Exception as e:issues.append(dict(code='FM3_PROFILE_INVALID',error_type=type(e).__name__))
        elif profile!='generic':raise ValueError('UNKNOWN_PROFILE')
        for folder,key in journal_roots(root):
            if (folder,key) in checks:continue
            try:Journal(root/folder).read(key);checks.add((folder,key))
            except Exception as e:issues.append(dict(path=folder+'/'+key,code='JOURNAL_INVALID',error_type=type(e).__name__))
        # Validate content-addressed raw/capture links independently of UI counts.
        mapped={f['path']:f for f in files}
        for folder,key in journal_roots(root):
            if folder!='source-receipts':continue
            try:
                v=Journal(root/folder).read(key)['value']
                if v.get('status')=='RECEIVED' and (mapped.get('source-raw/'+v['sha256'],{}).get('sha256')!=v['sha256']):raise ValueError('MISSING_OR_CORRUPT_RAW')
            except Exception as e:issues.append(dict(path=folder+'/'+key,code='SOURCE_RECEIPT_RAW_INVALID',error_type=type(e).__name__))
        views,problems=pointer_bindings(root,original_root);issues.extend(problems)
        journal_edges,problems=journal_references(root,files);issues.extend(problems)
        other_edges,problems=preview_and_capture_references(root,files,logical);issues.extend(problems)
        # Detect additions/removal/metadata change during semantic checks.
        after={str(p.relative_to(root)):p.stat() for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
        if set(after)!={f['path'] for f in files}:issues.append(dict(code='SOURCE_TREE_CHANGED_OR_UNSAFE_FILES'))
        for f in files:
            s=after.get(f['path'])
            if s is None or (s.st_size,s.st_mtime_ns,s.st_ino)!=(f['bytes'],f['mtime_ns'],f['source_inode']):issues.append(dict(path=f['path'],code='SOURCE_CHANGED_DURING_INSPECTION'))
    per_group={}
    for f in files:per_group.setdefault(f['hardlink_group'],f['bytes'])
    result=dict(schema=VERSION,status='PREFLIGHT_COMPLETE' if not issues else 'BLOCKED_INCOMPLETE_OR_UNSAFE',profile=profile,source_root=str(original_root),observed_root=str(root),observed_at=timestamp(),
        reader_requirements=reader_requirements(),files=files,logical_artifacts=logical,dependencies=edges,journal_reference_edges=journal_edges,preview_capture_edges=other_edges,journal_references_verified=True,semantics=semantics,additional_views=views,issues=issues,
        counts=dict(files=len(files),unique_file_inodes=len(per_group),journal_records=len(checks),du2_logical_artifacts=len(logical),dependency_edges=len(edges)),
        capacity=dict(logical_file_bytes=sum(f['bytes'] for f in files),unique_payload_bytes=sum(per_group.values()),source_allocated_bytes=allocated,
            restore_minimum_file_allocation_bytes=sum(math.ceil(n/4096)*4096 for n in per_group.values()),extra_safety_reserve_bytes=64*1024*1024),
        wall_seconds=time.monotonic()-started,source_requests=0,core_runs=0,independent_backup_verified=False)
    result['manifest_id']=digest(encode(result));return result


def public_summary(report):
    return {k:v for k,v in report.items() if k in ('schema','status','profile','observed_at','counts','capacity','wall_seconds','source_requests','core_runs','independent_backup_verified')} | dict(
        issue_count=len(report.get('issues',[])),issue_codes=dict(Counter(e['code'] for e in report.get('issues',[]))),
        semantic_counts={k:v for k,v in report.get('semantics',{}).items() if k not in ('views',)},journal_reference_edges_checked=len(report.get('journal_reference_edges',[])),preview_capture_edges_checked=len(report.get('preview_capture_edges',[])),private_manifest_not_public=True)


def write_private(path,value):
    p=private(path);codec.immutable(p,encode(value));return p


def validate_report(report,*,require_reference_audit=True):
    expected=report.get('manifest_id');copy=dict(report);copy.pop('manifest_id',None)
    if expected!=digest(encode(copy)) or report.get('schema')!=VERSION or report.get('status')!='PREFLIGHT_COMPLETE':raise ValueError('COMPLETE_FINGERPRINTED_PREFLIGHT_REQUIRED')
    if report.get('issues'):raise ValueError('INCOMPLETE_SOURCE_CANNOT_RESTORE')
    if require_reference_audit and (not report.get('journal_references_verified') or 'preview_capture_edges' not in report):raise ValueError('JOURNAL_REFERENCE_AUDIT_REQUIRED')
    seen=set();groups={}
    for f in report['files']:
        rel=f['path']
        if not isinstance(rel,str) or rel in ('','.','..') or Path(rel).is_absolute() or '..' in Path(rel).parts or '\\' in rel or str(Path(rel))!=rel:raise ValueError('UNSAFE_INVENTORY_RELATIVE_PATH')
        if f['path'] in seen or type(f['bytes']) is not int or f['bytes']<0 or not re.fullmatch('[0-9a-f]{64}',f['sha256']):raise ValueError('INVALID_INVENTORY_RECORD')
        seen.add(f['path']);signature=(f['bytes'],f['sha256'])
        if f['hardlink_group'] in groups and groups[f['hardlink_group']]!=signature:raise ValueError('CONFLICTING_HARDLINK_GROUP')
        groups[f['hardlink_group']]=signature


def verify_copy(root,report):
    """Verify independently using the snapshot manifest, without reading source."""
    validate_report(report);root=private(root)
    if report.get('reader_requirements')!=reader_requirements():raise ValueError('READER_VERSION_OR_SOURCE_BINDING_DIFFERS')
    restored=inspect(root,profile=report['profile'],original_root=report['source_root'])
    if restored['status']!='PREFLIGHT_COMPLETE':raise ValueError('RESTORED_DEPENDENCY_OR_PROFILE_INVALID')
    expected=[(f['path'],f['bytes'],f['sha256']) for f in report['files']]
    if [(f['path'],f['bytes'],f['sha256']) for f in restored['files']]!=expected:raise ValueError('RESTORED_FULL_MANIFEST_DIFFERS')
    aliases={};reverse={}
    for f in report['files']:
        p=bounded(root,f['path']);st=p.stat();inode=(st.st_dev,st.st_ino)
        if f['hardlink_group'] in aliases and aliases[f['hardlink_group']]!=inode:raise ValueError('RESTORED_HARDLINK_GROUP_DIFFERS')
        if inode in reverse and reverse[inode]!=f['hardlink_group']:raise ValueError('RESTORED_DISTINCT_GROUPS_MERGED')
        aliases[f['hardlink_group']]=inode;reverse[inode]=f['hardlink_group']
    restored['verification']=dict(full_original_bytes_match=True,hardlink_groups_match=True,source_reads_required=False,
        original_snapshot_manifest_id=report['manifest_id'],external_backup=False)
    copy=dict(restored);copy.pop('manifest_id');restored['manifest_id']=digest(encode(copy));return restored


def fsync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def restore(source,destination,report,*,resume=False):
    """Local isolated copy only. Never link destination files back to source."""
    validate_report(report);source=private(source);dest=private(destination)
    if source==dest or dest.is_relative_to(source) or source.is_relative_to(dest):raise ValueError('SOURCE_DESTINATION_OVERLAP')
    if str(source)!=report['observed_root']:raise ValueError('MANIFEST_SOURCE_ROOT_MISMATCH')
    state_dir=private(dest.parent/(dest.name+'.port1-receipt'));state_path=state_dir/'state.json'
    if not resume:
        if dest.exists() or state_dir.exists():raise FileExistsError('NEW_ISOLATED_DESTINATION_REQUIRED')
    else:
        saved=json.loads(state_path.read_bytes())
        if saved['manifest_id']!=report['manifest_id'] or saved['destination']!=str(dest) or saved['source']!=str(source):raise ValueError('RESUME_BINDING_MISMATCH')
    if not source.is_dir():raise ValueError('SOURCE_UNAVAILABLE_NO_REPAIR')
    if report.get('reader_requirements')!=reader_requirements():raise ValueError('READER_VERSION_OR_SOURCE_BINDING_DIFFERS')
    if not dest.parent.is_dir():raise ValueError('EXISTING_PRIVATE_DESTINATION_PARENT_REQUIRED')
    present={};first={}
    if resume:
        if not dest.is_dir():raise ValueError('OWNED_PARTIAL_DESTINATION_MISSING')
        for f in report['files']:
            target=bounded(dest,f['path'])
            if not target.exists():continue
            if not target.is_file() or target.stat().st_size!=f['bytes'] or file_hash(target)!=f['sha256']:raise ValueError('DESTINATION_PARTIAL_OR_CHANGED_FILE_PRESERVED')
            group=f['hardlink_group']
            if group in first and (target.stat().st_dev,target.stat().st_ino)!=(first[group].stat().st_dev,first[group].stat().st_ino):raise ValueError('DESTINATION_HARDLINK_GROUP_CHANGED')
            first[group]=target;present[f['path']]=target
    unique={f['hardlink_group']:f['bytes'] for f in report['files'] if f['hardlink_group'] not in first}
    block=max(4096,os.statvfs(dest.parent).f_frsize)
    required=sum(math.ceil(v/block)*block for v in unique.values())+max(report['capacity']['extra_safety_reserve_bytes'],len(report['files'])*512)
    if shutil.disk_usage(dest.parent).free<required:raise OSError('INSUFFICIENT_DESTINATION_CAPACITY_NO_COPY')
    # Full source must still match snapshot; no source writes or repair.
    current=set()
    for base,dirs,names in os.walk(source,followlinks=False):
        if any((Path(base)/d).is_symlink() for d in dirs):raise ValueError('SOURCE_DIRECTORY_CHANGED_OR_SYMLINK')
        current.update(str((Path(base)/n).relative_to(source)) for n in names)
    if current!={f['path'] for f in report['files']}:raise ValueError('SOURCE_FILE_SET_CHANGED_SINCE_PREFLIGHT')
    seen={}
    for entry in report['files']:
        path=bounded(source,entry['path']);st=path.stat();inode=(st.st_dev,st.st_ino)
        if not path.is_file() or st.st_size!=entry['bytes']:raise ValueError('SOURCE_CHANGED_SINCE_PREFLIGHT')
        if inode not in seen:seen[inode]=file_hash(path)
        if seen[inode]!=entry['sha256']:raise ValueError('SOURCE_CHANGED_SINCE_PREFLIGHT')
    if not resume:state_dir.mkdir(mode=0o700);dest.mkdir(mode=0o700)
    def save_state(status,**fields):
        v=dict(schema=VERSION,manifest_id=report['manifest_id'],source=str(source),destination=str(dest),status=status,**fields)
        pending=state_dir/'state.pending'
        if pending.is_symlink() or state_path.is_symlink():raise ValueError('RESTORE_RECEIPT_SYMLINK')
        with pending.open('wb') as f:f.write(encode(v));f.flush();os.fsync(f.fileno())
        os.replace(pending,state_path);fsync_directory(state_dir)
    copied=linked=0
    with (state_dir/'restore.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save_state('COPYING_NOT_READY')
        try:
            with quiet_source(source):
                for entry in report['files']:
                    src=bounded(source,entry['path']);target=bounded(dest,entry['path']);target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                    group=entry['hardlink_group']
                    if target.exists():
                        if file_hash(target)!=entry['sha256'] or target.stat().st_size!=entry['bytes']:raise ValueError('DESTINATION_PARTIAL_OR_CHANGED_FILE_PRESERVED')
                        if group in first and target.stat().st_ino!=first[group].stat().st_ino:raise ValueError('DESTINATION_HARDLINK_GROUP_CHANGED')
                    elif group in first:os.link(first[group],target);linked+=1
                    else:
                        fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                        with src.open('rb') as r,os.fdopen(fd,'wb') as w:shutil.copyfileobj(r,w,1024*1024);w.flush();os.fsync(w.fileno())
                        os.utime(target,ns=(entry['mtime_ns'],entry['mtime_ns']));copied+=1
                    if file_hash(target)!=entry['sha256']:raise ValueError('DESTINATION_READBACK_CHANGED')
                    if src.stat().st_ino==target.stat().st_ino and src.stat().st_dev==target.stat().st_dev:raise ValueError('DESTINATION_NOT_INDEPENDENT_OF_SOURCE')
                    first.setdefault(group,target)
            for directory,subdirs,names in os.walk(dest,topdown=False):fsync_directory(Path(directory))
            fsync_directory(dest.parent)
            restored=verify_copy(dest,report)
            access=make_access_overlay(dest,report,state_dir)
            restored_receipt=state_dir/('restored-manifest-'+restored['manifest_id']+'.json')
            write_private(restored_receipt,restored)
            save_state('VERIFIED_LOCAL_COPY',copied_files=copied,linked_files=linked,restored_manifest_id=restored['manifest_id'],restored_manifest=str(restored_receipt),access_overlay=str(access),
                full_original_bytes_match=True,independent_files=True,external_backup=False)
            return dict(status='VERIFIED_LOCAL_COPY',files=len(report['files']),copied_files=copied,linked_files=linked,full_original_bytes_match=True,
                original_source_preserved=True,core_runs=0,source_requests=0,access_overlay=str(access),external_backup=False)
        except Exception as e:
            save_state('INCOMPLETE_NOT_READY',error_type=type(e).__name__,copied_files=copied,linked_files=linked)
            raise


def make_access_overlay(dest,report,state_dir):
    """Relocate outer absolute pointers without changing any copied original SHA."""
    old=Path(report['source_root']);entries=[]
    for view in report.get('semantics',{}).get('views',[])+report.get('additional_views',[]):
        entries.append(dict(run_id=view['run_id'],path=str(bounded(dest,view['path'])),sha256=view['sha256'],bytes=view['bytes'],as_of=view.get('as_of')))
    head=dest/'current-increment-run.json'
    if head.exists():
        state=json.loads(head.read_bytes())
        if state.get('batch_index'):
            src=relocate(state['batch_index'],dest,old);v=json.loads(src.read_bytes())
            for entry in v['batches']:
                item=dict(entry,path=str(relocate(entry['path'],dest,old)))
                if not any(x['path']==item['path'] for x in entries):entries.append(item)
    entries=list({x['path']:x for x in entries}.values())
    batch_index=None
    if entries:
        batch_index=state_dir/'relocated-batches.json'
        write_private(batch_index,dict(schema='private-saved-batches/0.1',batches=entries))
    # Keep original records intact; this is a separate, private read access recipe.
    path=state_dir/'access-overlay.json'
    write_private(path,dict(schema='private-restored-access/0.1',root=str(dest),original_source_root=str(old),views=entries,
        mobile_batch_index=str(batch_index) if batch_index else None,original_pointers_preserved=True,restart_restore='NOT_TESTED',external_backup=False))
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['inspect','restore','verify']);p.add_argument('--root',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--profile',choices=['fm3','generic'],default='fm3');p.add_argument('--destination');p.add_argument('--original-root');p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='inspect':
        if private(a.manifest).is_relative_to(private(a.root)):raise ValueError('PRIVATE_MANIFEST_MUST_BE_OUTSIDE_SNAPSHOT_ROOT')
        result=inspect(a.root,profile=a.profile,original_root=a.original_root);write_private(a.manifest,result);print(json.dumps(public_summary(result),ensure_ascii=False,indent=2))
        if result['status']!='PREFLIGHT_COMPLETE':raise SystemExit(2)
    elif a.action=='verify':
        report=json.loads(private(a.manifest).read_bytes());result=verify_copy(a.root,report);print(json.dumps(public_summary(result)|dict(verification=result['verification']),ensure_ascii=False,indent=2))
    else:
        if not a.destination:p.error('--destination required for isolated local restore')
        report=json.loads(private(a.manifest).read_bytes());print(json.dumps(restore(a.root,a.destination,report,resume=a.resume),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
