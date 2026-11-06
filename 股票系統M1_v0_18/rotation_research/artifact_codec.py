"""Optional exact-byte sidecar codec for immutable Journal/preview artifacts.

Plain originals are never replaced. A .du2 manifest references verified spans of
old originals or content-addressed gzip chunks. No engine, database or network.
Readers return the original complete bytes, not a different numeric schema.
"""
import gzip,hashlib,io,json,os,re,secrets,zlib,shutil
from pathlib import Path

VERSION='exact-byte-chunks/0.1'
INTERNED='exact-interned-bytes/0.1'
MIN=65536
MAX=262144
MAX_FILE=512*1024*1024
MAX_MANIFEST=8*1024*1024
ANCHORS=re.compile(rb'[}\]],|\n[ ]{0,24}[}\]]')
HEX=re.compile('[0-9a-f]{64}')


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sidecar(path):return Path(str(path)+'.du2')
def exists(path):return Path(path).exists() or sidecar(path).exists()


def regular(path,root=None):
    p=Path(path)
    if p.is_symlink():raise ValueError('Artifact symlink refused')
    if root:
        root=Path(root).resolve()
        if not p.resolve().is_relative_to(root):raise ValueError('Artifact outside private root')
        for a in (p,*p.parents):
            if a==root:break
            if a.is_symlink():raise ValueError('Artifact ancestor symlink refused')
    return p


def immutable(path,raw):
    p=regular(path);p.parent.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:
        if regular(p).read_bytes()!=raw:raise ValueError('Immutable artifact conflict; existing bytes preserved')
        return
    with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def root_for(path):
    for p in Path(path).absolute().parents:
        marker=p/'.du2-root.json'
        if marker.exists():
            v=json.loads(regular(marker).read_bytes())
            if v.get('schema')!='private-artifact-root/0.1':raise ValueError('Bad artifact root marker')
            return p,v['id']
    raise ValueError('Private artifact root missing')


def prepare_root(root):
    p=Path(root).absolute()
    if any(a.is_symlink() for a in (p,*p.parents)):raise ValueError('Artifact root ancestor symlink refused')
    p=p.resolve()
    if any((a/'.git').exists() for a in (p,*p.parents)):raise ValueError('Private artifact root required outside Git')
    marker=p/'.du2-root.json'
    if not marker.exists():immutable(marker,encoded(dict(schema='private-artifact-root/0.1',id=secrets.token_hex(16))))
    return root_for(p/'placeholder')


def relative(path,root):
    p=regular(path,root)
    value=str(p.absolute().relative_to(root))
    if '\\' in value:raise ValueError('Invalid artifact path')
    return value


def resolve(root,rel):
    if not isinstance(rel,str) or Path(rel).is_absolute() or '..' in Path(rel).parts or '\\' in rel:raise ValueError('Unsafe artifact reference')
    return regular(root/rel,root)


def chunks(raw):
    start=0
    while start<len(raw):
        end=min(start+MAX,len(raw))
        if end<len(raw):
            for m in ANCHORS.finditer(raw,min(start+MIN,len(raw)),end):
                at=m.end()
                if zlib.crc32(raw[at-64:at])&1023==0:end=at;break
        part=raw[start:end]
        yield start,part
        start=end


def manifest(path):
    p=regular(sidecar(path));raw=p.read_bytes()
    if len(raw)>MAX_MANIFEST:raise ValueError('Manifest too large')
    v=json.loads(raw);root,rid=root_for(path)
    if v.get('schema') not in (VERSION,INTERNED) or v.get('root_id')!=rid or not HEX.fullmatch(v.get('sha256','')):raise ValueError('Bad artifact manifest binding')
    if not isinstance(v['bytes'],int) or not 0<=v['bytes']<=MAX_FILE:raise ValueError('Artifact size bound')
    if v['schema']==INTERNED:
        if v.get('format') not in ('journal','chart'):raise ValueError('Bad exact JSON serialization format')
        if resolve(root,v['wire_path'])!=Path(str(path)+'.wire').absolute():raise ValueError('Unexpected interned wire path')
        if not HEX.fullmatch(v.get('wire_sha256','')) or not 0<=v['wire_bytes']<=MAX_FILE:raise ValueError('Bad wire binding')
        resolve(root,v['anchor_path'])
        return root,v
    if len(v['pieces'])>MAX_FILE//MIN+2 or sum(x['bytes'] for x in v['pieces'])!=v['bytes']:raise ValueError('Bad artifact spans')
    for x in v['pieces']:
        if not isinstance(x['bytes'],int) or not 0<x['bytes']<=MAX or not HEX.fullmatch(x.get('sha256','')):raise ValueError('Bad chunk bound')
        if x['kind']=='span':
            resolve(root,x['path'])
            if not isinstance(x['offset'],int) or x['offset']<0:raise ValueError('Bad span offset')
        elif x['kind']=='gzip':
            if not HEX.fullmatch(x.get('stored_sha256','')) or not 0<x['stored_bytes']<=MAX+4096:raise ValueError('Bad gzip descriptor')
        else:raise ValueError('Unknown chunk representation')
    return root,v


def blob_path(root,digest):return root/'du2-blobs'/digest[:2]/(digest+'.gz')


def piece_bytes(root,x):
    if x['kind']=='span':
        with resolve(root,x['path']).open('rb') as f:f.seek(x['offset']);raw=f.read(x['bytes'])
    else:
        p=regular(blob_path(root,x['sha256']),root);stored=p.read_bytes()
        if len(stored)!=x['stored_bytes'] or sha(stored)!=x['stored_sha256']:raise ValueError('Stored compressed chunk changed')
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(stored)) as f:raw=f.read(x['bytes']+1)
        except (EOFError,zlib.error) as e:raise ValueError('Invalid compressed artifact') from e
    if len(raw)!=x['bytes'] or sha(raw)!=x['sha256']:raise ValueError('Artifact chunk fingerprint mismatch')
    return raw


def read_bytes(path,*,expected_bytes=None,expected_sha=None):
    p=regular(path)
    if p.exists():raw=p.read_bytes()
    else:
        root,v=manifest(p)
        if expected_bytes is not None and v['bytes']!=expected_bytes:raise ValueError('Logical length mismatch')
        if expected_sha is not None and v['sha256']!=expected_sha:raise ValueError('Logical fingerprint mismatch')
        if v['schema']==INTERNED:
            from technical_chart.interned_json import pack,unpack
            wire_path=resolve(root,v['wire_path'])
            if not wire_path.exists() and manifest(wire_path)[1]['schema']!=VERSION:raise ValueError('Nested interned recipes refused')
            wire=read_bytes(wire_path,expected_bytes=v['wire_bytes'],expected_sha=v['wire_sha256'])
            value=unpack(json.loads(wire))
            raw=journal_bytes(value) if v['format']=='journal' else encoded(pack(value))
        else:
            stream=io.BytesIO()
            for x in v['pieces']:stream.write(piece_bytes(root,x))
            raw=stream.getvalue()
        if len(raw)!=v['bytes'] or sha(raw)!=v['sha256']:raise ValueError('Reconstructed bytes changed')
    if expected_bytes is not None and len(raw)!=expected_bytes:raise ValueError('Logical length mismatch')
    if expected_sha is not None and sha(raw)!=expected_sha:raise ValueError('Logical fingerprint mismatch')
    return raw


def info(path):
    p=regular(path)
    if p.exists():return dict(bytes=p.stat().st_size,sidecar=False)
    root,v=manifest(p)
    if v['schema']==INTERNED:
        wire_path=resolve(root,v['wire_path'])
        if not wire_path.exists() and manifest(wire_path)[1]['schema']!=VERSION:raise ValueError('Nested interned recipes refused')
        wire=info(wire_path)
        if wire['bytes']!=v['wire_bytes']:raise ValueError('Interned wire length changed')
        return dict(bytes=v['bytes'],sha256=v['sha256'],sidecar=True,interned=True)
    # Metadata availability check only; full SHA verification happens on READ.
    for x in v['pieces']:
        q=resolve(root,x['path']) if x['kind']=='span' else regular(blob_path(root,x['sha256']),root)
        if not q.is_file() or (q.stat().st_size<x['offset']+x['bytes'] if x['kind']=='span' else q.stat().st_size!=x['stored_bytes']):raise ValueError('Artifact dependency missing/truncated')
    return dict(bytes=v['bytes'],sha256=v['sha256'],sidecar=True)


def base_index(path,root):
    p=regular(path,root)
    if not p.exists():
        anchor,v=manifest(p)
        if anchor!=root:raise ValueError('Cross-root compact reference refused')
        if v['schema']!=VERSION:raise ValueError('Exact-byte base required, not a recipe')
        return {x['sha256']:x for x in v['pieces']}
    raw=p.read_bytes();rel=relative(p,root)
    return {sha(b):dict(kind='span',sha256=sha(b),bytes=len(b),path=rel,offset=at) for at,b in chunks(raw)}


def publish(path,raw,*,root,bases=()):
    p=Path(path).absolute();root=Path(root).absolute();regular(p,root)
    if len(raw)>MAX_FILE:raise ValueError('Artifact exceeds bounded codec size')
    if exists(p):
        if read_bytes(p)!=raw:raise ValueError('Immutable logical artifact conflict')
        return dict(status='EXISTING',logical_bytes=len(raw),new_blob_bytes=0,reference_bytes=0)
    root,rid=prepare_root(root);index={}
    for base in bases:
        if exists(base):index.update(base_index(base,root))
    entries=[];new_bytes=0;reused=0
    for at,part in chunks(raw):
        digest=sha(part);entry=index.get(digest)
        if entry and entry['bytes']==len(part):reused+=len(part)
        else:
            target=blob_path(root,digest);was=target.exists()
            if was:
                stored=regular(target,root).read_bytes()
                if len(stored)>MAX+4096:raise ValueError('Existing compressed chunk exceeds bound')
                with gzip.GzipFile(fileobj=io.BytesIO(stored)) as f:decoded=f.read(len(part)+1)
                if decoded!=part:raise ValueError('Existing chunk corrupt; preserved without repair')
            else:
                stored=gzip.compress(part,compresslevel=6,mtime=0)
                if shutil.disk_usage(root).free<len(stored)+64*1024*1024:raise OSError('Private artifact capacity reserve reached; originals preserved')
                immutable(target,stored);new_bytes+=len(stored)
            entry=dict(kind='gzip',sha256=digest,bytes=len(part),stored_sha256=sha(stored),stored_bytes=len(stored))
        entries.append(entry)
    v=dict(schema=VERSION,root_id=rid,bytes=len(raw),sha256=sha(raw),pieces=entries)
    # Validate referenced and new chunks before committing the descriptor.
    check=hashlib.sha256()
    for x in entries:check.update(piece_bytes(root,x))
    if check.hexdigest()!=v['sha256']:raise ValueError('Precommit artifact readback failed')
    body=encoded(v)
    if shutil.disk_usage(root).free<len(body)+64*1024*1024:raise OSError('Private manifest capacity reserve reached')
    immutable(sidecar(p),body)
    return dict(status='CREATED',logical_bytes=len(raw),new_blob_bytes=new_bytes,reference_bytes=reused,manifest_bytes=sidecar(p).stat().st_size)


def materialize(path,destination):
    """Explicit reversible export; never overwrite any existing original."""
    destination=regular(destination)
    resolved=destination.resolve()
    if any((a/'.git').exists() for a in (resolved,*resolved.parents)):raise ValueError('Private materialization inside Git refused')
    raw=read_bytes(path);immutable(destination,raw)
    return dict(bytes=len(raw),sha256=sha(raw))


def journal_bytes(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def publish_interned(path,raw,*,root,bases=(),format='journal'):
    """Reuse original serializer node IDs against a fixed anchor, not yesterday's
    ever-growing table. Full original bytes are restored and SHA checked on READ.
    This is an optional at-rest encoding; no numeric fields or UI protocol change.
    """
    from technical_chart.interned_json import pack,unpack
    p=Path(path).absolute();root=Path(root).absolute();regular(p,root)
    if exists(p):
        if read_bytes(p)!=raw:raise ValueError('Immutable exact-interned artifact conflict')
        return dict(status='EXISTING',logical_bytes=len(raw))
    if len(raw)>MAX_FILE:raise ValueError('Artifact exceeds bounded codec size')
    root,rid=prepare_root(root)
    parsed=json.loads(raw)
    value=parsed if format=='journal' else unpack(parsed)
    canonical=journal_bytes(value) if format=='journal' else encoded(pack(value))
    if canonical!=raw:raise ValueError('Noncanonical bytes cannot use exact-interned encoding')
    anchor=None
    for base in bases:
        if not exists(base):continue
        if sidecar(base).exists() and not Path(base).exists():
            _,desc=manifest(base)
            if desc['schema']==INTERNED and desc['format']==format:
                anchor=resolve(root,desc['anchor_path']);break
        old=read_bytes(base);obj=json.loads(old)
        if format=='chart':
            if obj.get('schema_version')!='chart-interned-json/0.1':raise ValueError('Legacy chart transport required')
            anchor=Path(base).absolute()
        else:
            anchor=root/'du2-intern-anchors'/(sha(old)+'.json')
            publish(anchor,encoded(pack(obj)),root=root)
        break
    if anchor is None:
        anchor=root/'du2-intern-anchors'/(sha(canonical)+'.json')
        publish(anchor,encoded(pack(value)),root=root)
    anchor_raw=read_bytes(anchor);base_transport=json.loads(anchor_raw)
    wire=encoded(pack(value,base=base_transport));wire_path=Path(str(p)+'.wire')
    publish(wire_path,wire,root=root,bases=[anchor])
    v=dict(schema=INTERNED,root_id=rid,format=format,bytes=len(raw),sha256=sha(raw),wire_path=relative(wire_path,root),
        wire_bytes=len(wire),wire_sha256=sha(wire),anchor_path=relative(anchor,root))
    # Prove exact reconstruction before making the logical artifact discoverable.
    reconstructed=unpack(json.loads(read_bytes(wire_path)))
    check=journal_bytes(reconstructed) if format=='journal' else encoded(pack(reconstructed))
    if check!=raw:raise ValueError('Interned reconstruction differs from original bytes')
    body=encoded(v)
    if shutil.disk_usage(root).free<len(body)+64*1024*1024:raise OSError('Private recipe capacity reserve reached')
    immutable(sidecar(p),body)
    return dict(status='CREATED',logical_bytes=len(raw),wire_bytes=len(wire),recipe_bytes=len(body))
