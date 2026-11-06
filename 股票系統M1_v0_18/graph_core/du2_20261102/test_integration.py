"""New compact storage behavior; synthetic inputs, no source API requests."""
import json,tempfile,unittest,threading,base64
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from graph_core.du1_20261102.test_increment import seed_fixture
from graph_core.fm1_20261101.test_daily import sources
from graph_core.market_daily import import_saved,Journal
from graph_core import market_increment as m
from rotation_research import artifact_codec as c
from graph_core_chart.mobile_private import create_auth,make_server,batch_index

class CompactIntegration(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
  self.root=self.base/'compact';self.root.mkdir();self.input=self.base/'input';self.input.mkdir()
  self.seed=seed_fixture(self.root);self.clock=datetime(2026,11,5,tzinfo=timezone.utc)
 def capture(self,dt='1151030',**kw):sources(self.input,dt=dt,**kw);return import_saved(self.input,self.root)
 def update(self,cap):return m.update(self.root,seed_run=self.seed,capture_id=cap,now=self.clock)
 def files(self):return {str(p):c.sha(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}
 def test_plain_vs_compact_exact_result_history_and_preview_series(self):
  import shutil,re
  from graph_core.du2_20261102.benchmark import prepare
  fake=self.base/'repo';(fake/'.git').mkdir(parents=True)
  with self.assertRaises(ValueError):prepare(self.root,fake/'must-not-copy-private')
  self.assertFalse((fake/'must-not-copy-private').exists())
  cap=self.capture();plain=self.base/'plain';shutil.copytree(self.root,plain)
  a=m.update(plain,seed_run=self.seed,capture_id=cap,now=self.clock,storage_mode='plain');b=self.update(cap)
  self.assertNotEqual(a.get('status'),'BLOCKED',a.get('reason'));self.assertNotEqual(b.get('status'),'BLOCKED',b.get('reason'))
  old=Journal(plain/'runs').read(a['id'])['value'];new=Journal(self.root/'runs').read(b['id'])['value']
  self.assertEqual(a['id'],b['id'])
  for x,y in zip(old['stocks'],new['stocks']):
   self.assertEqual(x,y)
   self.assertEqual(c.read_bytes(Journal(plain/'results').path(x['result_key'])),c.read_bytes(Journal(self.root/'results').path(y['result_key'])))
   self.assertEqual(c.read_bytes(Journal(plain/'histories').path(x['history_key'])),c.read_bytes(Journal(self.root/'histories').path(y['history_key'])))
  def state(r):return json.loads(re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',c.read_bytes(r['private_preview']['path']),re.S)[1])
  for row in state(a)['stocks']:
   desc=row['preview_series'];left=Path(a['private_preview']['path']).parent/desc['path'];right=Path(b['private_preview']['path']).parent/desc['path']
   self.assertEqual(c.read_bytes(left),c.read_bytes(right));self.assertFalse(right.exists());self.assertTrue(c.sidecar(right).exists())
 def test_same_source_zero_core_zero_artifact_writes_and_old_head_readable(self):
  cap=self.capture();first=self.update(cap);before=self.files()
  with patch.object(m,'analyze',side_effect=AssertionError('No repeated core')):again=self.update(cap)
  self.assertTrue(again['reused']);self.assertEqual(before,self.files());self.assertEqual(again['new_core_calls'],0)
 def test_new_compact_revision_keeps_old_exact_bytes_and_seed(self):
  first=self.update(self.capture());head=(self.root/'current-increment-run.json').read_bytes();before=self.files();cap=self.capture(close='10.5')
  rejected=self.update(cap);self.assertEqual(rejected['status'],'BLOCKED');self.assertEqual(head,(self.root/'current-increment-run.json').read_bytes())
  second=m.update(self.root,capture_id=cap,now=self.clock,correction_of=first['id'],correction_reason='SYNTHETIC correction')
  self.assertNotEqual(second.get('status'),'BLOCKED',second.get('reason'));self.assertNotEqual(first['id'],second['id'])
  self.assertTrue(all(Path(p).read_bytes() and c.sha(Path(p).read_bytes())==v for p,v in before.items() if not p.endswith('current-increment-run.json') and not p.endswith('daily.lock')))
 def test_mid_stock_io_failure_resume_only_unfinished_and_preview_failure_preserves_head(self):
  cap=self.capture();real=c.immutable;hit=[]
  def fail(path,raw):
   if str(path).endswith('.json.du2') and '/results/' in str(path):
    hit.append(path)
    if len(hit)==2:raise OSError('SYNTHETIC interrupted descriptor commit')
   return real(path,raw)
  with patch.object(c,'immutable',side_effect=fail):blocked=self.update(cap)
  self.assertEqual(blocked['status'],'BLOCKED');self.assertFalse((self.root/'current-increment-run.json').exists())
  with patch.object(m,'analyze',wraps=m.analyze) as analyze:second=self.update(cap)
  self.assertEqual(analyze.call_count,1);self.assertNotEqual(second.get('status'),'BLOCKED',second.get('reason'))
  head=(self.root/'current-increment-run.json').read_bytes();nextcap=self.capture(dt='1151102')
  with patch('graph_core.market_preview.build',side_effect=ValueError('SYNTHETIC preview failure')):blocked=self.update(nextcap)
  self.assertEqual(blocked['status'],'BLOCKED');self.assertEqual(head,(self.root/'current-increment-run.json').read_bytes())
  with patch.object(m,'analyze',side_effect=AssertionError('Saved run reuse')):fixed=self.update(nextcap)
  self.assertFalse(fixed['head_unchanged'])
 def test_capacity_zero_rejects_without_computation_and_preserves_last_head(self):
  from types import SimpleNamespace
  self.update(self.capture());head=(self.root/'current-increment-run.json').read_bytes();cap=self.capture(dt='1151102')
  with patch.object(m.shutil,'disk_usage',return_value=SimpleNamespace(free=0)),patch.object(m,'analyze',side_effect=AssertionError('No core on capacity failure')):blocked=self.update(cap)
  self.assertEqual(blocked['status'],'BLOCKED');self.assertEqual(head,(self.root/'current-increment-run.json').read_bytes())
 def test_mobile_serves_old_plain_and_new_compact_batches_with_exact_auth_bytes(self):
  first=self.update(self.capture());second=self.update(self.capture(dt='1151102'));self.assertNotEqual(second.get('status'),'BLOCKED',second.get('reason'))
  auth=self.base/'auth.json';create_auth(auth,'owner','SYNTHETIC-PASSWORD-ONLY')
  server=make_server(None,auth,head=self.root/'current-increment-run.json');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  token=base64.b64encode(b'owner:SYNTHETIC-PASSWORD-ONLY').decode();base='http://127.0.0.1:'+str(server.server_port)
  try:
   with self.assertRaises(HTTPError) as error:urlopen(base+'/batches')
   self.assertEqual(error.exception.code,401)
   for route,item in server.allowed_files.items():
    raw=urlopen(Request(base+'/'+route,headers={'Authorization':'Basic '+token})).read();self.assertEqual(c.sha(raw),item['sha256'])
    if item.get('path') and c.sidecar(item['path']).exists():self.assertEqual(raw,c.read_bytes(item['path']))
   self.assertEqual(len(server.preview_summary['batches']),2)
  finally:server.shutdown();server.server_close();thread.join()
 def test_fixed_du1_plain_producer_read_and_explicit_storage_only_continuation(self):
  import importlib.util,subprocess
  path=self.base/'original-du1.py';path.write_bytes(subprocess.check_output(['git','show','f7825523a81369dd488c39075d962bd822bfe6ba:股票系統M1_v0_18/graph_core/market_increment.py']))
  spec=importlib.util.spec_from_file_location('fixed_du1_test_only',path);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  old_run=old.process(self.root,self.capture(),seed_run=self.seed,now=self.clock)
  saved=Journal(self.root/'runs').read(old_run['id'])['value'];self.assertEqual(saved['producer_sha256'],m.LEGACY_DU1_SHA)
  before=self.files();new_run=m.process(self.root,self.capture(dt='1151102'),seed_run=old_run['id'],now=self.clock)
  self.assertEqual(new_run['new_core_calls'],2);self.assertTrue(all(c.sha(Path(p).read_bytes())==v for p,v in before.items()))
  bad=dict(saved,producer_sha256='UNKNOWN_PRODUCER');Journal(self.root/'runs').save('wrong-producer',bad)
  with self.assertRaisesRegex(ValueError,'Unrecognized'):m.process(self.root,self.capture(dt='1151102'),seed_run='wrong-producer',now=self.clock)
 def test_private_server_bounds_concurrent_full_reassembly_to_one(self):
  from concurrent.futures import ThreadPoolExecutor
  import time
  result=self.update(self.capture());auth=self.base/'auth.json';create_auth(auth,'owner','SYNTHETIC-PASSWORD-ONLY')
  server=make_server(None,auth,head=self.root/'current-increment-run.json');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  token=base64.b64encode(b'owner:SYNTHETIC-PASSWORD-ONLY').decode();route=next(k for k in server.allowed_files if k.endswith('.json'))
  original=c.read_bytes;counter={'active':0,'maximum':0};guard=threading.Lock()
  def observe(path,**kw):
   is_series=Path(path).name.startswith('series-') and str(path).endswith('.json')
   if is_series:
    with guard:counter['active']+=1;counter['maximum']=max(counter['maximum'],counter['active'])
    time.sleep(.03)
   try:return original(path,**kw)
   finally:
    if is_series:
     with guard:counter['active']-=1
  def read(_):return urlopen(Request('http://127.0.0.1:'+str(server.server_port)+'/'+route,headers={'Authorization':'Basic '+token})).read()
  try:
   with patch.object(c,'read_bytes',side_effect=observe),ThreadPoolExecutor(max_workers=2) as pool:values=list(pool.map(read,range(2)))
   self.assertEqual(values[0],values[1]);self.assertEqual(counter['maximum'],1)
  finally:server.shutdown();server.server_close();thread.join()
 def test_missing_blob_http409_never_stale_other_stock(self):
  result=self.update(self.capture());auth=self.base/'auth.json';create_auth(auth,'owner','SYNTHETIC-PASSWORD-ONLY')
  server=make_server(None,auth,head=self.root/'current-increment-run.json');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  token=base64.b64encode(b'owner:SYNTHETIC-PASSWORD-ONLY').decode()
  try:
   route,item=next((k,v) for k,v in server.allowed_files.items() if k.endswith('.json'))
   root,recipe=c.manifest(item['path']);wire_path=c.resolve(root,recipe['wire_path']);wire_manifest=c.sidecar(wire_path);original=wire_manifest.read_bytes()
   malformed=json.loads(original);malformed['pieces'][0]['bytes']='INVALID_SYNTHETIC_LENGTH';wire_manifest.write_bytes(c.encoded(malformed))
   with self.assertRaises(HTTPError) as error:urlopen(Request('http://127.0.0.1:'+str(server.server_port)+'/'+route,headers={'Authorization':'Basic '+token}))
   self.assertEqual(error.exception.code,409)
   wire_manifest.write_bytes(original)  # synthetic fixture reset only; reader never repairs
   root,man=c.manifest(wire_path);piece=next(x for x in man['pieces'] if x['kind']=='gzip');c.blob_path(root,piece['sha256']).unlink()
   with self.assertRaises(HTTPError) as error:urlopen(Request('http://127.0.0.1:'+str(server.server_port)+'/'+route,headers={'Authorization':'Basic '+token}))
   self.assertEqual(error.exception.code,409)
  finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main(verbosity=2)
