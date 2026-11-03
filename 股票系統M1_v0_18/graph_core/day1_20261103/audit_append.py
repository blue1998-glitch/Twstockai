"""Audit only an authorized DAY1 append; baseline SHA reuse is explicit.
Private inventory, source bytes and references stay outside Git. Not a backup.
"""
import json,math,os,stat
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from rotation_research import private_portability as p,artifact_codec as c
from rotation_research.store import Journal

def audit_append(root,baseline,work,*,label):
 root=p.private(root);work=p.private(work);base=json.loads(p.private(baseline).read_bytes());p.validate_report(base)
 old={x['path']:x for x in base['files']};records=[];known={(x['source_device'],x['source_inode']):(x['sha256'],x['hardlink_group']) for x in old.values()};n=len(set(x['hardlink_group'] for x in old.values()));hashes=0
 for directory,dirs,names in os.walk(root,followlinks=False):
  for name in dirs:
   if (Path(directory)/name).is_symlink():raise ValueError('UNEXPECTED_SOURCE_SYMLINK')
  for name in names:
   q=Path(directory)/name;rel=str(q.relative_to(root));s=q.lstat()
   if not stat.S_ISREG(s.st_mode):raise ValueError('SOURCE_NOT_REGULAR')
   if rel in old:
    o=old[rel]
    if (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev,stat.S_IMODE(s.st_mode))!=(o['bytes'],o['mtime_ns'],o['source_inode'],o['source_device'],o['mode']):raise ValueError('ORIGINAL_CHANGED:'+rel)
    sha,group=o['sha256'],o['hardlink_group']
   else:
    if not (rel=='.du2-root.json' or rel in ('current-increment-run.json','current-increment.pending') or rel.split('/')[0] in ('raw','captures','du2-blobs','du2-intern-anchors','runs','results','histories','du1-checkpoints','preview','du1-batches','du1-failures')):raise ValueError('UNEXPECTED_APPEND_REQUIRES_REVIEW:'+rel)
    key=(s.st_dev,s.st_ino)
    if key not in known:
     sha=p.file_hash(q);group='day1-'+str(n);n+=1;known[key]=(sha,group);hashes+=1
    else:sha,group=known[key]
   records.append(dict(path=rel,bytes=s.st_size,sha256=sha,mode=stat.S_IMODE(s.st_mode),mtime_ns=s.st_mtime_ns,source_inode=s.st_ino,source_device=s.st_dev,source_nlink=s.st_nlink,hardlink_group=group))
 records.sort(key=lambda x:x['path']);files={x['path']:x for x in records}
 if not set(old).issubset(files):raise ValueError('ORIGINAL_REMOVED')
 edges=[];logical=[]
 for entry in records:
  if not entry['path'].endswith('.du2'):continue
  path=root/entry['path'][:-4];anchor,v=c.manifest(path)
  if anchor!=root:raise ValueError('EXTERNAL_CODEC_ROOT')
  needed=[root/'.du2-root.json']
  if v['schema']==c.INTERNED:
   for key in ('wire_path','anchor_path'):
    q=c.resolve(root,v[key]);needed.append(q if q.is_file() else c.sidecar(q))
  else:
   for piece in v['pieces']:
    q=c.resolve(root,piece['path']) if piece['kind']=='span' else c.blob_path(root,piece['sha256']);needed.append(q)
    if piece['kind']=='gzip' and files[str(q.relative_to(root))]['sha256']!=piece['stored_sha256']:raise ValueError('COMPRESSED_FINGERPRINT_DIFFERS')
  c.info(path)
  for q in needed:
   rel=str(q.relative_to(root))
   if rel not in files:raise ValueError('MISSING_APPEND_DEPENDENCY')
   edges.append(dict(artifact=entry['path'],dependency=rel))
  logical.append(dict(path=str(path.relative_to(root)),bytes=v['bytes'],sha256=v['sha256']))
 jrefs,issues=p.journal_references(root,records);views,problems=p.pointer_bindings(root,root);issues+=problems
 preview_refs,problems=p.preview_and_capture_references(root,records,logical);issues+=problems
 if issues:raise ValueError('APPEND_REFERENCE_CLOSURE_INVALID:'+str(Counter(x['code'] for x in issues)))
 head=root/'current-increment-run.json';committed=head.exists();summary=None
 if committed:
  pointer=json.loads(head.read_bytes());batch=Journal(root/'runs').read(pointer['id'])['value'];summary=batch['summary']
  if batch['capture_id']!=json.loads((work/'attempt1/probe-private.json').read_bytes())['capture_id']:raise ValueError('HEAD_CAPTURE_DIFFERS')
  if summary['processed']!=len(batch['stocks']):raise ValueError('TERMINAL_COUNT')
  for stock in batch['stocks']:
   for f in ('data_qualified','execution_qualified','execution_model_qualified','live_execution_authorized','historical_signal_eligible','policy_authorized'):
    if stock[f] is not False:raise ValueError('QUALIFICATION_PROMOTED')
   for f in ('primary_pressure_id','imputed_close','valuation'):
    if stock[f] is not None:raise ValueError('UNKNOWN_FILLED')
   if stock.get('result_key') and stock['current_comparable_records']!=1:raise ValueError('CONTINUITY_PROMOTED')
 report=dict(base);report.pop('manifest_id');groups={x['hardlink_group']:x['bytes'] for x in records}
 report.update(observed_at=datetime.now(timezone.utc).isoformat(),reader_requirements=p.reader_requirements(),files=records,logical_artifacts=logical,dependencies=edges,journal_reference_edges=jrefs,preview_capture_edges=preview_refs,additional_views=views,journal_references_verified=True,issues=[],counts=dict(files=len(records),unique_file_inodes=len(groups),journal_records=sum(1 for _ in p.journal_roots(root)),du2_logical_artifacts=len(logical),dependency_edges=len(edges)),capacity=dict(logical_file_bytes=sum(x['bytes'] for x in records),unique_payload_bytes=sum(groups.values()),source_allocated_bytes=sum((root/x['path']).stat().st_blocks*512 for x in {r['hardlink_group']:r for r in records}.values()),restore_minimum_file_allocation_bytes=sum(math.ceil(v/4096)*4096 for v in groups.values()),extra_safety_reserve_bytes=64*1024*1024),append_verification=dict(baseline_manifest_id=base['manifest_id'],baseline_full_sha_observed_at=base['observed_at'],unchanged_old_paths=len(old),new_physical_files=len(records)-len(old),new_inode_hashes=hashes,method='Unchanged old size/mtime/mode/inode/device plus prior SHA; new physical SHA, DU2 dependency and reference closure',full_old_payload_rehash=False,committed_day1_head=committed,new_head_summary=summary,independent_backup=False))
 report['manifest_id']=p.digest(p.encode(report));p.validate_report(report);destination=work/(label+'-inventory-private.json');p.write_private(destination,report)
 return report,destination
