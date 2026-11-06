"""Synthetic recovery proof; never substitutes for private 19 GiB backup."""
import json,os,subprocess,sys,tempfile,unittest,fcntl
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from rotation_research import private_portability as p,artifact_codec as c
from rotation_research.store import Journal
from graph_core.port1_20261102.fixture import make

class PortabilityTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name);self.source=make(self.base/'synthetic-source');self.dest=self.base/'isolated'
 def inspect(self):return p.inspect(self.source)
 def source_hashes(self):return {str(x.relative_to(self.source)):p.file_hash(x) for x in self.source.rglob('*') if x.is_file()}
 def test_synthetic_complete_independent_restore_and_relocated_chart(self):
  from graph_core_chart.mobile_private import batch_index
  report=self.inspect();self.assertEqual(report['status'],'PREFLIGHT_COMPLETE',report['issues']);before=self.source_hashes()
  r=p.restore(self.source,self.dest,report);self.assertEqual(r['status'],'VERIFIED_LOCAL_COPY');self.assertEqual(before,self.source_hashes())
  self.assertTrue(r['full_original_bytes_match']);self.assertEqual(r['core_runs'],0)
  overlay=json.loads(Path(r['access_overlay']).read_bytes());self.assertTrue(all(v['path'].startswith(str(self.dest)) for v in overlay['views']))
  _,files,summary,_=batch_index(overlay['mobile_batch_index']);self.assertEqual(summary['charts'],1)
  for record in report['files']:
   src=self.source/record['path'];dst=self.dest/record['path'];self.assertEqual(p.file_hash(src),p.file_hash(dst));self.assertNotEqual(src.stat().st_ino,dst.stat().st_ino)
  a=self.dest/'readonly-aliases/synthetic-original';b=next((self.dest/'source-raw').iterdir());self.assertEqual(a.stat().st_ino,b.stat().st_ino)
  # Only synthetic fixture is hidden; no original private file is moved.
  hidden=self.base/'synthetic-source-hidden';self.source.rename(hidden)
  original_stat=p.os.stat;original_lstat=p.os.lstat
  def deny_source(fn):
   def guard(path,*args,**kw):
    if isinstance(path,(str,os.PathLike)) and Path(path).absolute().is_relative_to(self.source):raise PermissionError('Synthetic old source unavailable')
    return fn(path,*args,**kw)
   return guard
  with patch.object(p.os,'stat',side_effect=deny_source(original_stat)),patch.object(p.os,'lstat',side_effect=deny_source(original_lstat)):
   restored=p.verify_copy(self.dest,report)
  self.assertEqual(restored['status'],'PREFLIGHT_COMPLETE',restored['issues']);self.assertFalse(restored['verification']['source_reads_required'])
  batch_index(overlay['mobile_batch_index'])
 def test_missing_source_no_fake_root_created(self):
  with self.assertRaises(ValueError):p.inspect('/workspace')
  missing=self.base/'missing';r=p.inspect(missing);self.assertEqual(r['status'],'SOURCE_UNAVAILABLE');self.assertFalse(missing.exists())
  with self.assertRaises(ValueError):p.restore(missing,self.dest,r)
 def test_missing_raw_source_and_changed_source_refused_no_repair(self):
  report=self.inspect();raw=next((self.source/'source-raw').iterdir());raw.unlink()
  bad=self.inspect();self.assertEqual(bad['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE')
  with self.assertRaises(ValueError):p.restore(self.source,self.dest,report)
  self.assertFalse(self.dest.exists());self.assertFalse(raw.exists())
 def test_missing_shared_blob_and_future_anchor_block_complete_flag(self):
  report=self.inspect();self.assertTrue(report['counts']['dependency_edges']>0)
  key=Journal(self.source/'runs').read('synthetic-fm3-run')['value']['stocks'][0]['history_key'];logical=Journal(self.source/'histories').path(key);root,m=c.manifest(logical)
  anchor=c.resolve(root,m['anchor_path']);c.sidecar(anchor).unlink()
  # Current read can work with flattened gzip references; future anchor is still required.
  c.read_bytes(logical)
  bad=self.inspect();self.assertEqual(bad['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE')
  self.assertTrue(any(x['code']=='CODEC_DEPENDENCY_OR_CONTENT_INVALID' for x in bad['issues']))
 def test_corrupt_blob_refused_without_repair(self):
  blob=next((self.source/'du2-blobs').rglob('*.gz'));blob.write_bytes(b'BROKEN')
  r=self.inspect();self.assertEqual(r['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE');self.assertEqual(blob.read_bytes(),b'BROKEN')
  with self.assertRaises(ValueError):p.restore(self.source,self.dest,r)
 def test_wrong_saved_core_version_identity_and_fingerprint_refused(self):
  row=Journal(self.source/'runs').read('synthetic-fm3-run')['value']['stocks'][0];key=row['result_key'];value=Journal(self.source/'results').read(key)
  value['value']['result']['schema_version']='UNKNOWN_CORE';path=Journal(self.source/'results').path(key);raw=p.encode(value);path.write_bytes(raw)
  r=self.inspect();self.assertEqual(r['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE');self.assertEqual(path.read_bytes(),raw)
 def test_unsafe_destination_manifest_and_private_credentials_refuse(self):
  report=self.inspect()
  elsewhere=self.base/'elsewhere';elsewhere.mkdir();(self.base/'unsafe.port1-receipt').symlink_to(elsewhere,target_is_directory=True)
  with self.assertRaises(ValueError):p.restore(self.source,self.base/'unsafe',report,resume=True)
  self.dest.mkdir()
  with self.assertRaises(FileExistsError):p.restore(self.source,self.dest,report)
  with self.assertRaises(ValueError):p.restore(self.source,self.source/'inside',report)
  report['files'][0]['path']='../escape';copy=dict(report);copy.pop('manifest_id');report['manifest_id']=p.digest(p.encode(copy))
  with self.assertRaises(ValueError):p.restore(self.source,self.base/'escape',report)
  repo=self.base/'repo';(repo/'.git').mkdir(parents=True)
  with self.assertRaises(ValueError):p.inspect(repo)
  (self.source/'owner-auth.json').write_text('{"synthetic_secret":true}')
  self.assertEqual(self.inspect()['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE')
 def test_symlinks_and_external_codec_dependencies_refused(self):
  outside=self.base/'other';outside.write_bytes(b'outside');(self.source/'unsafe-link').symlink_to(outside)
  self.assertEqual(self.inspect()['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE')
  root=self.base/'container';root.mkdir();sub=root/'subset';sub.mkdir();c.publish(sub/'logical.json',b'SYNTHETIC',root=root)
  self.assertEqual(p.inspect(sub,profile='generic')['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE')
 def test_busy_source_locks_readonly_and_never_removed(self):
  lock=self.source/'daily.lock';lock.write_bytes(b'')
  with lock.open('rb') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaises(BlockingIOError):self.inspect()
  self.assertTrue(lock.exists())
  (self.source/'fm3-writer.lock').write_bytes(b'')
  with self.assertRaises(ValueError):self.inspect()
  self.assertTrue((self.source/'fm3-writer.lock').exists())
 def test_capacity_refused_before_copy_hashing_or_creation(self):
  report=self.inspect()
  original_hash=p.file_hash
  def no_source_rehash(path):
   if Path(path).is_relative_to(self.source):raise AssertionError('No unnecessary source data rehash when capacity unavailable')
   return original_hash(path)
  with patch.object(p.shutil,'disk_usage',return_value=SimpleNamespace(free=0)),patch.object(p,'file_hash',side_effect=no_source_rehash):
   with self.assertRaises(OSError):p.restore(self.source,self.dest,report)
  self.assertFalse(self.dest.exists());self.assertFalse((self.base/'isolated.port1-receipt').exists())
 def test_interruption_resumes_verified_files_only_and_keeps_source(self):
  report=self.inspect();original=os.open;seen=[]
  def fail(path,flags,*args,**kw):
   if str(path).startswith(str(self.dest)+'/') and flags&os.O_EXCL:
    seen.append(path)
    if len(seen)==2:raise OSError('SYNTHETIC interrupted before next file')
   return original(path,flags,*args,**kw)
  before=self.source_hashes()
  with patch.object(p.os,'open',side_effect=fail),self.assertRaises(OSError):p.restore(self.source,self.dest,report)
  state=json.loads((self.base/'isolated.port1-receipt/state.json').read_bytes());self.assertEqual(state['status'],'INCOMPLETE_NOT_READY')
  existing={str(x):x.stat().st_ino for x in self.dest.rglob('*') if x.is_file()}
  r=p.restore(self.source,self.dest,report,resume=True);self.assertEqual(r['status'],'VERIFIED_LOCAL_COPY');self.assertEqual(before,self.source_hashes())
  self.assertTrue(all(Path(x).stat().st_ino==inode for x,inode in existing.items()))
 def test_corrupt_partial_copy_is_preserved_and_refuses_resume(self):
  report=self.inspect();real=p.shutil.copyfileobj
  def fail(src,dst,length):dst.write(b'PARTIAL');raise OSError('SYNTHETIC incomplete copy')
  with patch.object(p.shutil,'copyfileobj',side_effect=fail),self.assertRaises(OSError):p.restore(self.source,self.dest,report)
  partial=next(x for x in self.dest.rglob('*') if x.is_file());before=partial.read_bytes()
  with self.assertRaises(ValueError):p.restore(self.source,self.dest,report,resume=True)
  self.assertEqual(partial.read_bytes(),before)
 def test_historical_checkpoint_missing_dependency_blocks_whole_collection(self):
  Journal(self.source/'checkpoints').save('old-checkpoint',dict(stock=dict(result_key='missing-synthetic-result')))
  r=self.inspect();self.assertEqual(r['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE')
  self.assertTrue(any(x['code']=='JOURNAL_REFERENCE_MISSING_OR_INVALID' for x in r['issues']))
 def test_noncurrent_preview_dependency_missing_is_not_silently_ignored(self):
  folder=self.source/'preview/old-view';folder.mkdir(parents=True)
  state={'stocks':[{'preview_series':{'path':'series-'+'0'*64+'.json','bytes':1,'sha256':'0'*64}}]}
  (folder/'old.html').write_bytes(b'<script id="market-state" type="application/json">'+p.encode(state)+b'</script>')
  r=self.inspect();self.assertEqual(r['status'],'BLOCKED_INCOMPLETE_OR_UNSAFE')
  self.assertTrue(any(x['code']=='PREVIEW_REFERENCE_INVALID' for x in r['issues']))
 def test_unexpected_hardlink_merge_and_reader_version_change_rejected(self):
  (self.source/'separate-one.bin').write_bytes(b'SAME_SYNTHETIC_BYTES');(self.source/'separate-two.bin').write_bytes(b'SAME_SYNTHETIC_BYTES')
  report=self.inspect();wrong=json.loads(p.encode(report));wrong['reader_requirements']['byte_codec']='UNKNOWN';copy=dict(wrong);copy.pop('manifest_id');wrong['manifest_id']=p.digest(p.encode(copy))
  with self.assertRaises(ValueError):p.restore(self.source,self.dest,wrong)
  self.assertFalse(self.dest.exists());p.restore(self.source,self.dest,report)
  a=self.dest/'separate-one.bin';b=self.dest/'separate-two.bin';b.unlink();os.link(a,b)  # synthetic corruption only
  with self.assertRaises(ValueError):p.verify_copy(self.dest,report)
 def test_no_engine_or_network_import_on_fresh_restore_tool(self):
  code="import sys;import rotation_research.private_portability;assert 'graph_core.core' not in sys.modules;assert 'product_candidate.macd' not in sys.modules;assert 'urllib.request' not in sys.modules"
  subprocess.check_call([sys.executable,'-c',code])

if __name__=='__main__':unittest.main(verbosity=2)
