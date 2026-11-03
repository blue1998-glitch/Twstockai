"""M-REAL1 synthetic integration controls; no new market/core execution."""
import base64,copy,json,os,tempfile,threading,unittest,http.client
from pathlib import Path
from unittest.mock import patch
from graph_core import real_workbench as w
from graph_core.port1_20261102.fixture import make
from rotation_research import private_portability as p,artifact_codec as c
from rotation_research.store import Journal
from graph_core_chart.mobile_private import preview_index,create_auth,make_server
from technical_chart.interned_json import unpack

class IntegrationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name);self.root=make(self.base/'source');state=json.loads((self.root/'fm3-continuation.json').read_bytes());self.page=Path(state['preview']['path']);self.raw=c.read_bytes(self.page)
  self.state=json.loads(__import__('re').search(rb'<script id="market-state" type="application/json">(.*?)</script>',self.raw,__import__('re').S)[1]);self.stock=self.state['stocks'][0];self.desc=self.stock['preview_series'];self.chunk=self.page.parent/self.desc['path'];self.chart=unpack(json.loads(c.read_bytes(self.chunk)))
  # Real FM3 uses full immutable original chunks; make that explicit in tiny synthetic fixture.
  self.chunk.write_bytes(c.read_bytes(self.chunk));self.stock['as_of']=self.chart['results'][0]['as_of']
  # PORT1 fixture is an old storage-only envelope; REAL1 adds the actual FM3 stock cutoff before freezing synthetic inputs.
  for path in (self.root/'runs').glob('*.json'):
   v=json.loads(path.read_bytes());v['value']['stocks'][0]['as_of']=self.stock['as_of'];path.write_bytes(c.encoded(v))
  marker=b'<script id="market-state" type="application/json">';self.raw=self.raw.split(marker)[0]+marker+c.encoded(self.state)+b'</script>'
  self.page.write_bytes(self.raw);c.sidecar(self.page).unlink();state['preview'].update(bytes=len(self.raw),sha256=w.digest(self.raw));(self.root/'fm3-continuation.json').write_bytes(c.encoded(state))
  catalog=self.root/'saved-batches.json';v=json.loads(catalog.read_bytes());v['batches'][0].update(bytes=len(self.raw),sha256=w.digest(self.raw));catalog.write_bytes(c.encoded(v))
  head=self.root/'current-increment-run.json';v=json.loads(head.read_bytes());v['private_preview'].update(bytes=len(self.raw),sha256=w.digest(self.raw));head.write_bytes(c.encoded(v))
  self.audit=p.inspect(self.root);self.assertEqual(self.audit['status'],'PREFLIGHT_COMPLETE',self.audit['issues']);self.manifest=self.base/'audit-private.json';self.manifest.write_bytes(c.encoded(self.audit));self.saved=Journal(self.root/'results').read(self.stock['result_key'])['value']
 def test_builder_reuses_exact_originals_and_saved_values_without_engine(self):
  before={f['path']:f['sha256'] for f in self.audit['files']}
  with patch('graph_core.core.analyze',side_effect=AssertionError('No recognition run')):
   x=w.build(self.root,self.base/'output',self.manifest,reserve_bytes=0)
  self.assertEqual(x['charts_bound'],1);self.assertEqual(x['core_runs'],0);self.assertEqual(x['original_payload_copies'],0)
  folder=Path(x['preview']['path']).parent;self.assertEqual((folder/self.desc['path']).stat().st_ino,self.chunk.stat().st_ino)
  self.assertEqual(before,{f['path']:f['sha256'] for f in p.inspect(self.root)['files']})
  _,allowed,summary,_=preview_index(x['preview']['path']);self.assertEqual(summary['charts'],1);self.assertEqual(len(allowed),3)
 def test_same_binding_repeat_reuses_artifacts_not_duplicate_full_graph(self):
  x=w.build(self.root,self.base/'output',self.manifest,reserve_bytes=0)
  # Completed immutable build is reused without reprojecting or re-saving charts.
  with patch.object(w,'projection',side_effect=AssertionError('No duplicate projection')):
   repeat=w.build(self.root,self.base/'output',self.manifest,reserve_bytes=0)
  self.assertTrue(repeat['reused_completed_build']);self.assertEqual(repeat['preview'],x['preview'])
  self.assertTrue(c.exists(x['preview']['path']))
 def test_capacity_refusal_no_source_repair_or_output(self):
  with patch.object(w.shutil,'disk_usage',return_value=type('S',(),{'free':0})()),self.assertRaises(OSError):w.build(self.root,self.base/'output',self.manifest)
  self.assertFalse((self.base/'output').exists());self.assertTrue(self.chunk.exists())
 def test_missing_original_or_audit_mismatch_refuses(self):
  self.chunk.unlink()
  with self.assertRaises(ValueError):w.build(self.root,self.base/'output',self.manifest,reserve_bytes=0)
  self.assertFalse((self.base/'output').exists())
 def test_identity_cutoff_basis_and_indicators_do_not_fallback(self):
  for field,value in [('code','OTHER'),('exchange','OTHER'),('price_basis_id','OTHER'),('macd',{})]:
   chart=copy.deepcopy(self.chart);chart[field]=value
   with self.assertRaises(ValueError):w.projection(self.saved,self.stock,chart,self.desc)
  bad=copy.deepcopy(self.stock);bad['as_of']='1900-01-01'
  with self.assertRaises(ValueError):w.projection(self.saved,bad,self.chart,self.desc)
 def test_projection_exact_existing_helpers_and_current_event_coverage(self):
  radar,overlay=w.projection(self.saved,self.stock,self.chart,self.desc)
  self.assertEqual(radar,w.event_project(self.saved['result'],self.stock));self.assertEqual(overlay['comparison_evidence'],w.comparison_project(self.saved,self.stock,self.chart['source']))
  self.assertEqual(radar['coverage']['first_observed_dates'],[self.stock['as_of']]);self.assertFalse(overlay['comparison_evidence']['policy_authorized'])
 def test_alias_rejects_changed_or_unregistered_source(self):
  with self.assertRaises(ValueError):w.alias(self.chunk,self.base/'copy',self.desc,{},self.root)
  target=self.base/'copy';target.write_bytes(b'SYNTHETIC_OTHER')
  with self.assertRaises(ValueError):w.alias(self.chunk,target,self.desc,{str(self.chunk.relative_to(self.root)):dict(bytes=self.desc['bytes'],sha256=self.desc['sha256'])},self.root)
  self.assertEqual(target.read_bytes(),b'SYNTHETIC_OTHER')
 def test_shell_preserves_original_payload_and_escapes_new_state(self):
  state=copy.deepcopy(self.state);state['test']='<script>&'
  x=w.render_saved_shell(self.raw,state);marker=b'<script id="market-state" type="application/json">'
  self.assertEqual(x.split(marker)[0],self.raw.split(marker)[0]);text=x.split(marker)[1].split(b'</script>')[0];self.assertEqual(json.loads(text)['test'],'<script>&')
 def test_evidence_requires_owner_and_allowlisted_sha(self):
  x=w.build(self.root,self.base/'output',self.manifest,reserve_bytes=0);page=Path(x['preview']['path']);raw=c.read_bytes(page);state=json.loads(raw.split(b'<script id="market-state" type="application/json">')[1].split(b'</script>')[0]);desc=state['stocks'][0]['preview_evidence']
  auth=self.base/'auth.json';password='SYNTHETIC_REAL1_TEST_PASSWORD_123';create_auth(auth,'test',password);server=make_server(page,auth);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  def close():server.shutdown();server.server_close();thread.join()
  self.addCleanup(close)
  def get(path,headers={}):
   conn=http.client.HTTPConnection('127.0.0.1',server.server_port);conn.request('GET',path,headers=headers);r=conn.getresponse();body=r.read();code=r.status;conn.close();return code,body
  self.assertEqual(get('/'+desc['path'])[0],401);headers={'Authorization':'Basic '+base64.b64encode(('test:'+password).encode()).decode()}
  code,body=get('/'+desc['path'],headers);self.assertEqual(code,200);self.assertEqual(w.digest(body),desc['sha256']);self.assertEqual(get('/integration-private.json',headers)[0],404);self.assertEqual(get('/'+desc['path'],headers|{'Origin':'https://evil.example'})[0],403)

if __name__=='__main__':unittest.main()
