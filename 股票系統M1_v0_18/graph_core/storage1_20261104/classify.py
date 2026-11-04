"""Bounded streaming inode accounting and DU2 reference classification.
No deletions, candidate cleanup or market-file body decoding. Reports PRIVATE
inventory; public output is aggregate only. Unknown purposes are retained U.
"""
import os,json,gzip,time,resource,collections,stat
from pathlib import Path
from rotation_research import artifact_codec as c
from .common import BASE,ROOT,WORK,encode,write,budget
BITS={'A':1,'B':2,'C':4,'D':8,'U':16}
ORDER=['U','A','B','C','D']
def purpose(rel):
    a=rel.parts
    if any(x in ('owner-auth.json','credentials.json','connection-private.json') or 'credential' in x for x in a):return 'U'
    if len(a)>2 and a[:2]==('fm3_20261101','runtime'):
        n=a[2]
        if n in ('raw','source-raw','source-receipts','source-slots','captures','histories'):return 'A'
        if n in ('results','runs','checkpoints','du1-checkpoints','du1-batches','du1-failures'):return 'B'
        if n=='preview':return 'C'
        if n in ('du2-blobs','du2-intern-anchors'):return None
        return 'B'
    if any(x.startswith(('browser','edges-','first-load-benchmark')) or x in ('browser-current','browser-first','browser-second','browser-third','direct-verdict','presentation','positioning') for x in a):return 'D'
    if any(x in ('raw','captures','source-raw','source-receipts') for x in a) or (a and a[0]=='day2_compact_20261104' and len(a)>1 and a[1]=='capture'):return 'A'
    if a and a[0]=='lite1_20261103' and len(a)>1 and a[1] in ('2026-10-30','2026-11-02'):return 'C'
    if a and a[0]=='real1_20261102' and any(x in ('preview','workbench') for x in a[1:]):return 'C'
    if a and a[0] in ('cap1_20261104','cap1_cash_20261104'):return 'B'
    if a and (a[0].startswith('du1_20261102-browser') or a[0] in ('day1_20261103','capacity1_20261104','day2_compact_20261104')):return 'D'
    return 'U'
def run():
    done=WORK/'classification-private.json'
    if done.exists():return json.loads(done.read_bytes())
    inventory=WORK/'inventory-private.jsonl.gz'
    if inventory.exists():raise FileExistsError('PRIOR_CLASSIFICATION_PARTIAL_PRESERVED')
    start=time.monotonic();inodes={};paths={};manifests=[];symlinks=0;folders=0;files=0;unsafe=[]
    budget(5*1024**2)
    with inventory.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as z:
      stack=[BASE]
      while stack:
        p=stack.pop()
        if p==WORK:continue
        if time.monotonic()-start>180 or files>250000:raise RuntimeError('BOUNDED_CLASSIFICATION_LIMIT')
        with os.scandir(p) as rows:
          for e in rows:
            q=Path(e.path)
            if q==WORK:continue
            s=e.stat(follow_symlinks=False);rel=q.relative_to(BASE);kind=purpose(rel);key=(s.st_dev,s.st_ino)
            if stat.S_ISLNK(s.st_mode):symlinks+=1;unsafe.append(str(rel));continue
            if stat.S_ISDIR(s.st_mode):stack.append(q);folders+=1;continue
            if not stat.S_ISREG(s.st_mode):unsafe.append(str(rel));continue
            files+=1;paths[str(q)]=key
            item=inodes.setdefault(key,[s.st_blocks*512,s.st_size,0,0,s.st_nlink]);item[2]|=BITS.get(kind,0);item[3]+=1
            z.write(encode(dict(path=str(rel),category=kind or 'SHARED_PENDING',bytes=s.st_size,allocated=s.st_blocks*512,inode=s.st_ino,device=s.st_dev,mtime_ns=s.st_mtime_ns,nlink=s.st_nlink,may_delete=False)))
            if e.name.endswith('.du2'):manifests.append((q,kind))
    refs=0;missing=0;cross=0;unverified=0
    for q,kind in manifests:
        # Interpret only bounded metadata descriptors, never logical old results.
        if q.stat().st_size>c.MAX_MANIFEST:raise ValueError('LARGE_DESCRIPTOR_REFUSED')
        try:root,v=c.manifest(Path(str(q)[:-4]))
        except (ValueError,OSError,KeyError,TypeError):
            unverified+=1;inodes[paths[str(q)]][2]|=BITS['U'];continue
        targets=[]
        if v['schema']==c.INTERNED:targets=[c.resolve(root,v['wire_path']),c.resolve(root,v['anchor_path'])]
        else:
            for x in v['pieces']:targets.append(c.resolve(root,x['path']) if x['kind']=='span' else c.blob_path(root,x['sha256']))
        owner_mask=BITS.get(kind,BITS['U'])
        for target in targets:
            if str(target) not in paths and str(c.sidecar(target)) in paths:target=c.sidecar(target)
            key=paths.get(str(target));refs+=1
            if key is None:missing+=1;continue
            item=inodes[key]
            if item[2] and item[2]&owner_mask==0:cross+=1
            item[2]|=owner_mask
    result={k:dict(assigned_unique_allocated_bytes=0,exclusive_allocated_bytes=0,logical_inode_bytes=0,physical_inodes=0,path_count=0,hardlinked_inodes=0,cross_category_shared_inodes=0) for k in BITS}
    shared_bytes=0;hardlinks=0;count=collections.Counter()
    for alloc,logical,mask,n,nlinks in inodes.values():
        if mask==0:mask=BITS['U']
        categories=[k for k in ORDER if mask&BITS[k]];assigned=categories[0];r=result[assigned];r['assigned_unique_allocated_bytes']+=alloc;r['logical_inode_bytes']+=logical;r['physical_inodes']+=1;r['path_count']+=n
        if len(categories)==1:r['exclusive_allocated_bytes']+=alloc
        else:r['cross_category_shared_inodes']+=1;shared_bytes+=alloc
        if nlinks>1:r['hardlinked_inodes']+=1;hardlinks+=1
        count[assigned]+=1
    report=dict(schema='storage1-capacity-classification/0.1',scope=str(BASE),excluded_new_output=str(WORK),category_meanings=dict(A='Raw OHLCV/source/corporate-action/time evidence and histories',B='Immutable core/event/account/decision/replay records',C='Existing preview/presentation derivations; reconstruction requires fixed code and preserved complete inputs',D='Known browser/resource/engineering work products; not certified deletable',U='Unknown purpose, credentials, unclassified shared objects; protected'),categories=result,
        physical_unique_allocated_file_bytes=sum(x[0] for x in inodes.values()),regular_paths=files,physical_file_inodes=len(inodes),directory_count=folders,symlinks_not_followed=symlinks,hardlinked_inodes=hardlinks,cross_category_shared_allocated_bytes=shared_bytes,
        reference_coverage=dict(du2_manifests=len(manifests),references=refs,missing_references=missing,cross_purpose_references=cross,unverified_descriptors_retained=unverified),
        physical_accounting='Unique(device,inode) st_blocks*512; shared inode assigned once with protective U>A>B>C>D priority. No extent/reflink or byte-identical different-inode dedup inferred. Directory metadata not included in file allocation totals.',
        reconstruction=dict(A='Not reconstructible from summaries; original evidence retained',B='Exact historical evidence retained; no deletion authorization',C='Conditional only, no full regeneration performed',D='Engineering purpose does not prove redundancy; all retained',U='Not proven; all retained'),delete_candidates=0,all_categories_retained=True,unsafe_paths_count=len(unsafe),
        future_growth='New source bodies and per-stock daily fact shards dominate quote-only writes; no daily full-history/result/chart duplication is required. Full graph/indicator cache retention requires a later explicit policy.',
        elapsed_seconds=time.monotonic()-start,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write(done,encode(report));print(json.dumps(report,ensure_ascii=False),flush=True);return report
if __name__=='__main__':run()
