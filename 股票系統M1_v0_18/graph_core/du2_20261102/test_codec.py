"""Synthetic byte-preservation, optional Journal and private-reader contracts."""
from pathlib import Path
import gzip,json,tempfile,unittest
from unittest.mock import patch
from rotation_research import artifact_codec as c
from rotation_research.store import Journal

class CodecTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.raw=(b'{"SYNTHETIC": "'+b'abc0123456789'*12000+b'"}\n')*3
 def publish(self,raw=None):
  p=self.root/'results'/'test.json';c.publish(p,raw or self.raw,root=self.root);return p
 def test_exact_bytes_utf8_and_explicit_reversible_export(self):
  raw=('中文🙂𠀀\n'*55000).encode();p=self.publish(raw);self.assertFalse(p.exists());self.assertEqual(c.read_bytes(p),raw)
  out=self.root/'separate-export.json';c.materialize(p,out);self.assertEqual(out.read_bytes(),raw)
  with self.assertRaises(ValueError):c.materialize(p,self.publish(b'OTHER'))
 def test_old_plain_journal_unchanged_new_representation_identical(self):
  j=Journal(self.root/'runs');v={'synthetic':True,'null':None,'precise':'1.00000000000001','items':list(range(2000))}
  j.save('plain',v);before=j.path('plain').read_bytes();j.save('compact',v,compact=True,storage_root=self.root)
  self.assertEqual(j.read('compact')['value'],v);self.assertEqual(j.path('plain').read_bytes(),before)
  self.assertEqual(j.save('compact',v)['value'],v)
  with self.assertRaises(ValueError):j.save('compact',{'different':True})
 def test_legacy_prefix_reuse_no_copy_and_flattened_next_generation(self):
  raw=b''.join(c.encoded({'SYNTHETIC':i,'x':'same'*20}) for i in range(9000));base=self.root/'legacy.json';base.write_bytes(raw)
  p=self.root/'next.json';r=c.publish(p,raw+b'ADDED',root=self.root,bases=[base]);self.assertGreater(r['reference_bytes'],0)
  q=self.root/'later.json';c.publish(q,raw+b'ADDED AGAIN',root=self.root,bases=[p]);_,m=c.manifest(q)
  self.assertTrue(all(x['kind'] in ('span','gzip') for x in m['pieces']));self.assertFalse(any(x.get('path')==str(p) for x in m['pieces']))
  self.assertEqual(c.read_bytes(q),raw+b'ADDED AGAIN');self.assertEqual(base.read_bytes(),raw)
 def test_same_publish_zero_writes_and_conflict_preserves(self):
  p=self.publish();before={str(x):x.read_bytes() for x in self.root.rglob('*') if x.is_file()}
  self.assertEqual(c.publish(p,self.raw,root=self.root)['status'],'EXISTING')
  with self.assertRaises(ValueError):c.publish(p,b'WRONG',root=self.root)
  self.assertEqual(before,{str(x):x.read_bytes() for x in self.root.rglob('*') if x.is_file()})
 def test_corrupt_blob_and_legacy_span_rejected_not_repaired(self):
  p=self.publish();root,m=c.manifest(p);x=next(x for x in m['pieces'] if x['kind']=='gzip');blob=c.blob_path(root,x['sha256']);blob.write_bytes(b'BROKEN')
  with self.assertRaises(ValueError):c.read_bytes(p)
  with self.assertRaises(ValueError):c.publish(p,self.raw,root=self.root)
  self.assertEqual(blob.read_bytes(),b'BROKEN')
  base=self.root/'legacy.json';base.write_bytes(self.raw);q=self.root/'with-base.json';c.publish(q,self.raw+b'TAIL',root=self.root,bases=[base]);base.write_bytes(b'X'+self.raw[1:])
  with self.assertRaises(ValueError):c.read_bytes(q)
 def test_path_traversal_symlink_root_and_manifest_binding_rejected(self):
  p=self.publish();v=json.loads(c.sidecar(p).read_bytes());v['root_id']='WRONG';c.sidecar(p).write_bytes(c.encoded(v))
  with self.assertRaises(ValueError):c.read_bytes(p)
  with self.assertRaises(ValueError):c.resolve(self.root,'../outside')
  link=self.root/'link';link.symlink_to(self.root/'results',target_is_directory=True)
  with self.assertRaises(ValueError):c.publish(link/'test.json',b'x',root=self.root)
 def test_incomplete_write_resumes_without_deleting_or_overwriting(self):
  real=c.immutable;count=[]
  def interrupt(path,raw):
   if str(path).endswith('.du2'):raise OSError('SYNTHETIC descriptor interruption')
   count.append(path);return real(path,raw)
  with patch.object(c,'immutable',side_effect=interrupt),self.assertRaises(OSError):self.publish()
  blobs={p:p.read_bytes() for p in (self.root/'du2-blobs').rglob('*.gz')};self.assertTrue(blobs)
  p=self.publish();self.assertEqual(c.read_bytes(p),self.raw);self.assertTrue(all(p.read_bytes()==v for p,v in blobs.items()))
 def test_actual_capacity_refusal_does_not_publish_descriptor(self):
  from types import SimpleNamespace
  with patch.object(c.shutil,'disk_usage',return_value=SimpleNamespace(free=0)),self.assertRaises(OSError):self.publish()
  self.assertFalse(c.sidecar(self.root/'results'/'test.json').exists())
 def test_existing_valid_gzip_encoding_reused_without_platform_recompression(self):
  c.prepare_root(self.root)
  for at,raw in c.chunks(self.raw):
   blob=c.blob_path(self.root,c.sha(raw));c.immutable(blob,gzip.compress(raw,mtime=123456))
  before={p:p.read_bytes() for p in (self.root/'du2-blobs').rglob('*.gz')}
  p=self.publish();self.assertEqual(c.read_bytes(p),self.raw);self.assertTrue(all(p.read_bytes()==v for p,v in before.items()))
 def test_explicit_materialization_refuses_git_destination(self):
  p=self.publish();repo=self.root/'not-a-delivery';(repo/'.git').mkdir(parents=True)
  with self.assertRaises(ValueError):c.materialize(p,repo/'private.json')
  self.assertFalse((repo/'private.json').exists())
  (repo/'nested').mkdir();alias=self.root/'alias';alias.symlink_to(repo/'nested',target_is_directory=True)
  with self.assertRaises(ValueError):c.prepare_root(alias/'child')
  self.assertFalse((repo/'nested'/'child'/'.du2-root.json').exists())
 def test_descriptor_length_hash_and_size_bounds_rejected(self):
  p=self.publish();root,v=c.manifest(p)
  with self.assertRaises(ValueError):c.read_bytes(p,expected_sha='0'*64)
  with self.assertRaises(ValueError):c.read_bytes(p,expected_bytes=1)
  v['bytes']=c.MAX_FILE+1;c.sidecar(p).write_bytes(c.encoded(v))
  with self.assertRaises(ValueError):c.read_bytes(p)

class ExactInternedTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.value=dict(synthetic=True,precise='99.999999999999999',null=None,rows=[dict(id=i,text='repeat',value=str(i)) for i in range(2000)])
 def test_optional_serializer_default_matches_fixed_old_implementation(self):
  import subprocess
  from technical_chart.interned_json import pack,unpack
  source=subprocess.check_output(['git','show','f7825523a81369dd488c39075d962bd822bfe6ba:股票系統M1_v0_18/technical_chart/build.py'],text=True)
  start=source.index('def pack(value):');end=source.index('\ndef render(',start);env={'json':json};exec(source[start:end],env)
  self.assertEqual(pack(self.value),env['pack'](self.value))
  base=pack(self.value);new=dict(self.value,appended=['new']);self.assertEqual(unpack(pack(new,base=base)),new)
 def test_journal_and_chart_recipes_restore_original_exact_bytes(self):
  from technical_chart.interned_json import pack
  for mode in ('journal','chart'):
   raw=c.journal_bytes(self.value) if mode=='journal' else c.encoded(pack(self.value))
   base=self.root/(mode+'-base.json');base.write_bytes(raw);target=self.root/(mode+'-next.json')
   newer=dict(self.value,appended=['new',None,'0.0000000000000001'])
   newraw=c.journal_bytes(newer) if mode=='journal' else c.encoded(pack(newer))
   c.publish_interned(target,newraw,root=self.root,bases=[base],format=mode)
   self.assertEqual(c.read_bytes(target),newraw);self.assertEqual(c.info(target)['bytes'],len(newraw));self.assertEqual(base.read_bytes(),raw)
   out=self.root/(mode+'-export.json');c.materialize(target,out);self.assertEqual(out.read_bytes(),newraw)
 def test_next_generation_fixed_anchor_no_daily_node_table_accumulation(self):
  base=self.root/'base.json';base.write_bytes(c.journal_bytes(self.value));previous=base;anchors=[]
  for i in range(4):
   p=self.root/('next'+str(i)+'.json');raw=c.journal_bytes(dict(self.value,as_of='SYNTHETIC-'+str(i)))
   c.publish_interned(p,raw,root=self.root,bases=[previous]);_,meta=c.manifest(p);anchors.append(meta['anchor_path']);self.assertEqual(c.read_bytes(p),raw);previous=p
  self.assertEqual(len(set(anchors)),1)
 def test_bad_recipe_wire_tamper_and_noncannonical_input_refused(self):
  p=self.root/'result.json';raw=c.journal_bytes(self.value);c.publish_interned(p,raw,root=self.root);root,m=c.manifest(p)
  wire=c.sidecar(c.resolve(root,m['wire_path']));v=json.loads(wire.read_bytes());v['sha256']='0'*64;wire.write_bytes(c.encoded(v))
  with self.assertRaises(ValueError):c.read_bytes(p)
  with self.assertRaises(ValueError):c.publish_interned(self.root/'other.json',b'{"not": "canonical"}',root=self.root)
 def test_read_side_has_no_numeric_engine_import(self):
  import subprocess,sys
  code="import sys;from graph_core_chart.mobile_private import preview_index;assert 'graph_core.core' not in sys.modules;assert 'product_candidate.macd' not in sys.modules"
  subprocess.check_call([sys.executable,'-c',code])

if __name__=='__main__':unittest.main(verbosity=2)
