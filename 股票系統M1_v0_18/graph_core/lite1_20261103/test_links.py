"""Synthetic allowlist and reserve tests; no real sources or credentials."""
import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from rotation_research import artifact_codec as c
from graph_core_chart.mobile_private import preview_index
from graph_core.lite1_20261103.build import budget

class LinkedAssets(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.root=self.base/'source';self.folder=self.base/'view';self.folder.mkdir();self.parent=self.root/'preview'/'SYNTHETIC';self.parent.mkdir(parents=True)
  raw=b'{"synthetic_chart_only":true}';sha=c.sha(raw);self.name='series-'+sha+'.json';self.chart=self.parent/self.name;self.chart.write_bytes(raw)
  self.desc=dict(path=self.name,sha256=sha,bytes=len(raw));self.item=dict(route=self.name,source_path=str(self.chart),identity='TWSE:SYN',as_of='2020-01-02',sha256=sha,bytes=len(raw));self.page=self.folder/'index.html';self.freeze()
 def freeze(self,item=None,data=None):
  raw=c.encoded(dict(schema='private-lite-linked-assets/0.1',charts=[item or self.item],data=data or []));sha=c.sha(raw);name='assets-'+sha+'.json';(self.folder/name).write_bytes(raw)
  s=dict(schema='private-lite-workbench/0.1',summary=dict(as_of='2020-01-02'),stocks=[dict(identity='TWSE:SYN',as_of='2020-01-02',preview_series=self.desc)],asset_index=dict(path=name,sha256=sha,bytes=len(raw)))
  self.page.write_text('<script id="market-state" type="application/json">'+json.dumps(s)+'</script>');return self.folder/name
 def test_explicit_root_required_and_original_path_preserved(self):
  with self.assertRaises(ValueError):preview_index(self.page)
  _,files,summary,_=preview_index(self.page,linked_roots=[self.root]);self.assertEqual(files[self.name]['path'],self.chart);self.assertEqual(summary['charts'],1);self.assertFalse((self.folder/self.name).exists())
 def test_hash_correct_manifest_cannot_escape_source_preview_root(self):
  f=self.base/self.name;f.write_bytes(self.chart.read_bytes());item=dict(self.item,source_path=str(f));self.freeze(item)
  with self.assertRaises(ValueError):preview_index(self.page,linked_roots=[self.root])
 def test_non_preview_source_and_symlink_refused(self):
  target=self.root/'raw'/self.name;target.parent.mkdir();target.write_bytes(self.chart.read_bytes());self.freeze(dict(self.item,source_path=str(target)))
  with self.assertRaises(ValueError):preview_index(self.page,linked_roots=[self.root])
  self.chart.unlink();self.chart.symlink_to(target);self.freeze()
  with self.assertRaises(ValueError):preview_index(self.page,linked_roots=[self.root])
 def test_stock_and_date_binding_refused_even_with_new_valid_manifest_sha(self):
  for field,value in [('identity','TPEX:OTHER'),('as_of','2020-01-01')]:
   self.freeze(dict(self.item,**{field:value}))
   with self.assertRaises(ValueError):preview_index(self.page,linked_roots=[self.root])
 def test_manifest_raw_tamper_and_descriptor_size_refused(self):
  p=self.freeze();p.write_bytes(b'CORRUPT')
  with self.assertRaises(ValueError):preview_index(self.page,linked_roots=[self.root])
  self.freeze(dict(self.item,bytes=self.item['bytes']+1))
  with self.assertRaises(ValueError):preview_index(self.page,linked_roots=[self.root])
 def test_local_packet_routes_are_explicit_not_directory_grants(self):
  body=b'{"synthetic_packet":true}';sha=c.sha(body);name='series-'+sha+'.json';(self.folder/name).write_bytes(body);self.freeze(data=[dict(path=name,bytes=len(body),sha256=sha)])
  _,files,_,_=preview_index(self.page,linked_roots=[self.root]);self.assertEqual(files[name]['path'],self.folder/name)
  self.freeze(data=[dict(path='../private.json',bytes=len(body),sha256=sha)])
  with self.assertRaises(ValueError):preview_index(self.page,linked_roots=[self.root])
 def test_reserve_refuses_before_new_file_and_keeps_existing(self):
  old=self.folder/'old';old.write_bytes(b'SYNTHETIC_OLD')
  with patch('graph_core.lite1_20261103.build.shutil.disk_usage',return_value=type('S',(),dict(free=0))()),budget(self.folder),self.assertRaises(OSError):c.immutable(self.folder/'new',b'X')
  self.assertFalse((self.folder/'new').exists());self.assertEqual(old.read_bytes(),b'SYNTHETIC_OLD')
 def test_explicit_new_file_budget_refuses_without_overwrite(self):
  with budget(self.folder,limit=1),self.assertRaises(OSError):c.immutable(self.folder/'new',b'SYNTHETIC')
  self.assertFalse((self.folder/'new').exists())

class LiteOwnerRoot(unittest.TestCase):
 setUp=LinkedAssets.setUp
 freeze=LinkedAssets.freeze
 # Only the new method is counted/run here; inherited allowlist cases run above.
 def test_owner_required_before_same_origin_default_redirect(self):
  import threading,http.client,base64
  from graph_core_chart.mobile_private import create_auth,make_server
  auth=self.base/'auth.json';password='SYNTHETIC_TEST_ONLY_123';create_auth(auth,'owner',password)
  raw=self.page.read_bytes();entry=dict(path=str(self.page),sha256=c.sha(raw),bytes=len(raw),as_of='2020-01-02',run_id='SYNTHETIC')
  catalogue=self.base/'batches.json';catalogue.write_text(json.dumps(dict(schema='private-saved-batches/0.1',batches=[entry])))
  server=make_server(None,auth,batches=catalogue,linked_roots=[self.root]);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   def get(path,authorized=False):
    conn=http.client.HTTPConnection('127.0.0.1',server.server_port);h={}
    if authorized:h['Authorization']='Basic '+base64.b64encode(('owner:'+password).encode()).decode()
    conn.request('GET',path,headers=h);r=conn.getresponse();body=r.read();result=(r.status,dict(r.getheaders()),body);conn.close();return result
   status,h,_=get('/');self.assertEqual(status,401);self.assertNotIn('Location',h)
   status,h,_=get('/',True);self.assertEqual(status,303);self.assertEqual(h['Location'],'/batch-'+entry['sha256']+'/index.html')
   self.assertEqual(get(h['Location'],True)[0],200);self.assertEqual(get('/batches',True)[0],200)
  finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
