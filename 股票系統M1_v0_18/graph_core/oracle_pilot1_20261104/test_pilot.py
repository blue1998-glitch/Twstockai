"""New synthetic pilot controls only; no FM3 reads or live infrastructure."""
import base64,hashlib,json,os,re,secrets,shutil,tempfile,threading,unittest,urllib.request,urllib.error,zipfile,subprocess,sys,socket,select,time
from pathlib import Path
from unittest.mock import patch
from graph_core.oracle_pilot1_20261104 import build as b
from graph_core.oracle_pilot1_20261104.serve import verify,server
from graph_core_chart.mobile_private import create_auth
from technical_chart.build import unpack
from graph_core.core import analyze
from graph_core.lite1_20261103.decision import project
from product_candidate.macd import macd
from graph_core.market_preview import source_segment_ma

class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=Path(os.environ['PILOT_BUNDLE'])
        cls.html=(cls.bundle/'Twstockai_SYNTHETIC_PILOT.html').read_text()
        def embedded(id):return json.loads(re.search('<script id="'+id+'" type="application/json">(.*?)</script>',cls.html,re.S)[1])
        cls.states=embedded('pilot-states');cls.mapping=embedded('synthetic-demo-series')
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='pilot-unit-',dir=os.environ['PILOT_WORK']);self.addCleanup(self.tmp.cleanup);self.work=Path(self.tmp.name)
    def copy(self):
        target=self.work/'isolated';shutil.copytree(self.bundle,target);return target
    def credentials(self):
        auth=self.work/'owner.json';pw=secrets.token_urlsafe(24);create_auth(auth,'owner',pw)
        return auth,'Basic '+base64.b64encode(('owner:'+pw).encode()).decode()
    def http(self):
        auth,header=self.credentials();s=server(self.bundle,auth);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
        self.addCleanup(lambda:(s.shutdown(),s.server_close(),t.join()))
        return s,'http://127.0.0.1:'+str(s.server_port),header
    def request(self,url,auth=None,**kw):
        headers=kw.pop('headers',{})
        if auth:headers['Authorization']=auth
        try:return urllib.request.urlopen(urllib.request.Request(url,headers=headers,**kw),timeout=10)
        except urllib.error.HTTPError as e:return e
    def test_archive_and_manifest_all_original_bytes(self):
        self.assertTrue(verify(self.bundle).is_file())
        m=json.loads((self.bundle/'MANIFEST.json').read_bytes())
        with zipfile.ZipFile(self.bundle/'Twstockai_ORACLE_PILOT1_SYNTHETIC.zip') as z:
            self.assertIsNone(z.testzip());self.assertEqual(set(z.namelist()),{f['path'] for f in m['files']}|{'MANIFEST.json'})
            for name in z.namelist():self.assertEqual(z.read(name),(self.bundle/name).read_bytes())
    def test_engine_and_indicators_exact_for_all_synthetic_snapshots(self):
        snapshots=json.loads((self.bundle/'synthetic-snapshots.json').read_bytes())['snapshots']
        for x in snapshots:
            desc=x['series_descriptor'];raw=self.mapping[desc['path']].encode();self.assertEqual(b.sha(raw),desc['sha256']);self.assertEqual(len(raw),desc['bytes']);series=unpack(json.loads(raw));r=analyze(x['input'],as_of=x['as_of'])
            self.assertEqual(series['results'],[r]);self.assertEqual(b.sha(b.encoded(r)),x['result_sha256']);self.assertEqual(series['macd'],macd([bar['close'] for bar in series['bars']]));self.assertEqual(series['moving_averages'],source_segment_ma(series['bars'],[]))
            stock=next(s for s in self.states[x['as_of']]['stocks'] if s['identity']==x['identity']);self.assertEqual(project(stock,r),x['decision'])
            self.assertTrue(all(z['date']<=x['as_of'] for z in series['bars']));self.assertIsNone(r['comparison']['primary_pressure_id'])
    def test_two_dates_and_complete_synthetic_identity_bindings(self):
        self.assertEqual(len(self.states),2)
        for day,state in self.states.items():
            self.assertEqual(len(state['stocks']),5);self.assertTrue(state['synthetic_only'])
            for s in state['stocks']:
                d=json.loads(self.mapping[s['decision_detail']['path']]);self.assertEqual((d['identity'],d['as_of']),(s['identity'],day));self.assertEqual(d['decision']['batch_id'],state['batch_id'])
                if s.get('preview_series'):
                    series=unpack(json.loads(self.mapping[s['preview_series']['path']]));self.assertEqual(series['code'],s['code']);self.assertEqual(series['exchange'],s['market']);self.assertEqual(series['results'][0]['as_of'],day)
    def test_no_private_market_or_credentials_in_bundle(self):
        for f in json.loads((self.bundle/'MANIFEST.json').read_bytes())['files']:
            raw=(self.bundle/f['path']).read_bytes()
            for marker in [b'/workspace/twstockai-local-data',b'finmind_20261101',b'BEGIN PRIVATE KEY',b'BEGIN RSA PRIVATE KEY',b'tskey-auth-',b'owner-auth.json']:
                self.assertNotIn(marker,raw)
        self.assertIn(b.LABEL,self.html);self.assertNotIn('https://',self.html)
    def test_changed_original_bytes_rejected(self):
        c=self.copy();entry=c/'Twstockai_SYNTHETIC_PILOT.html';entry.write_bytes(entry.read_bytes()+b'corrupt')
        with self.assertRaisesRegex(ValueError,'BYTES_CHANGED'):verify(c)
    def test_missing_original_rejected(self):
        c=self.copy();(c/'synthetic-snapshots.json').unlink()
        with self.assertRaises(FileNotFoundError):verify(c)
    def test_symlink_source_refused(self):
        c=self.copy();p=c/'synthetic-snapshots.json';raw=p.read_bytes();p.unlink();other=self.work/'outside.json';other.write_bytes(raw);p.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'SYMLINK'):verify(c)
    def test_manifest_traversal_and_real_data_flag_refused(self):
        c=self.copy();m=json.loads((c/'MANIFEST.json').read_bytes());m['files'][0]['path']='../outside';(c/'MANIFEST.json').write_bytes(b.encoded(m))
        with self.assertRaisesRegex(ValueError,'BUNDLE_PATH'):verify(c)
        m['contains_private_market_data']=True;(c/'MANIFEST.json').write_bytes(b.encoded(m))
        with self.assertRaisesRegex(ValueError,'SYNTHETIC_MANIFEST'):verify(c)
    def test_capacity_and_existing_output_refuse(self):
        with patch.object(b.shutil,'disk_usage',return_value=shutil._ntuple_diskusage(1,1,0)):
            with self.assertRaisesRegex(OSError,'CAPACITY'):b.build(self.work/'new')
        self.assertFalse((self.work/'new').exists())
        with self.assertRaisesRegex(FileExistsError,'OUTPUT'):b.build(self.bundle)
    def test_http_owner_challenge_and_valid_access(self):
        s,url,auth=self.http();self.assertEqual(s.server_address[0],'127.0.0.1')
        self.assertEqual(self.request(url).code,401);r=self.request(url,auth);self.assertEqual(r.code,200);self.assertEqual(r.read(),(self.bundle/'Twstockai_SYNTHETIC_PILOT.html').read_bytes());self.assertIn("default-src 'none'",r.headers['Content-Security-Policy'])
    def test_host_origin_paths_and_write_refuse(self):
        _,url,auth=self.http()
        for kwargs in [{'headers':{'Host':'evil.example'}},{'headers':{'Origin':'https://evil.example'}}]:self.assertEqual(self.request(url,auth,**kwargs).code,403)
        for path in ['/../owner.json','/MANIFEST.json','/?x=1','/%252e%252e/owner.json']:self.assertEqual(self.request(url+path,auth).code,404)
        self.assertEqual(self.request(url,auth,method='POST',data=b'x').code,405)
    def test_live_tamper_refused_not_served(self):
        c=self.copy();auth,header=self.credentials();s=server(c,auth);t=threading.Thread(target=s.serve_forever,daemon=True);t.start();self.addCleanup(lambda:(s.shutdown(),s.server_close(),t.join()))
        p=c/'Twstockai_SYNTHETIC_PILOT.html';p.write_bytes(p.read_bytes().replace(b'Twstockai',b'Xwstockai',1));self.assertEqual(self.request('http://127.0.0.1:'+str(s.server_port),header).code,409)
    def test_non_tailnet_host_and_credential_mode_refuse(self):
        auth,_=self.credentials()
        for h in ['example.com','public.ts.net','host.tail.ts.net:443','host.tail.ts.net/']:
            with self.assertRaisesRegex(ValueError,'TAILNET_HOST'):server(self.bundle,auth,private_host=h)
        auth.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'owner-only'):server(self.bundle,auth)
    def test_copied_isolated_bundle_reads_without_engine(self):
        c=self.copy();auth,header=self.credentials()
        with patch('graph_core.core.analyze',side_effect=AssertionError('Serving must never recalculate')):
            s=server(c,auth);self.assertEqual(s.preview_summary['stocks'],5);s.server_close()

    def test_bundle_standalone_without_repo_or_engine_imports(self):
        c=self.copy()
        r=subprocess.run([sys.executable,str(c/'serve.py'),'verify','--bundle',str(c)],cwd=c,env={'PATH':os.environ['PATH']},capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr.decode());self.assertIn(b'SYNTHETIC_BUNDLE_VERIFIED',r.stdout)
        auth,header=self.credentials()
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        process=subprocess.Popen([sys.executable,str(c/'serve.py'),'serve','--bundle',str(c),'--credentials',str(auth),'--port',str(port)],cwd=c,env={'PATH':os.environ['PATH']},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            ready=select.select([process.stdout],[],[],8)[0];self.assertTrue(ready,'Standalone service not ready');self.assertIn('LOOPBACK_READY',process.stdout.readline())
            started=time.monotonic();response=self.request('http://127.0.0.1:'+str(port),header);self.assertEqual(response.code,200);self.assertEqual(response.read(),(c/'Twstockai_SYNTHETIC_PILOT.html').read_bytes())
            memory={}
            for line in Path('/proc/'+str(process.pid)+'/status').read_text().splitlines():
                key=line.split(':')[0]
                if key in ['VmRSS','VmHWM','Threads']:memory[key]=line.split(':',1)[1].strip()
            Path(os.environ['PILOT_WORK'],'standalone-service-resources.json').write_text(json.dumps({'status':'PASS_STANDALONE_SYNTHETIC_HTTP','no_repository_pythonpath':True,'request_seconds':time.monotonic()-started,'process_memory':memory,'real_oracle_measurement':False}))
        finally:
            process.terminate();process.communicate(timeout=8)

    def test_embedded_json_cannot_break_script_boundary(self):
        value={'label':'</script><script>alert(1)</script>&'}
        raw=b.script_json(value);self.assertNotIn('</script>',raw);self.assertEqual(json.loads(raw),value)

if __name__=='__main__':unittest.main(verbosity=2)
