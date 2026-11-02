"""Synthetic security controls; no real credentials or market data in Git."""
import base64,hashlib,http.client,json,os,tempfile,threading,unittest
from pathlib import Path
from graph_core_chart.mobile_private import create_auth,make_server,load_auth,external

class PrivateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.password='SYNTHETIC_ONLY_PASSWORD_123';create_auth(self.root/'auth.json','test',self.password)
        raw=b'{"SYNTHETIC_ONLY":true}';sha=hashlib.sha256(raw).hexdigest();self.name='series-'+sha+'.json';(self.root/self.name).write_bytes(raw)
        state={'summary':{'as_of':'2020-01-01'},'stocks':[{'preview_series':{'path':self.name,'sha256':sha,'bytes':len(raw)}}]}
        (self.root/'index.html').write_text('<script id="market-state" type="application/json">'+json.dumps(state)+'</script>')
        self.server=make_server(self.root/'index.html',self.root/'auth.json');self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.auth='Basic '+base64.b64encode(('test:'+self.password).encode()).decode()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def call(self,path='/',*,auth=None,method='GET',headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port);h=dict(headers or {})
        if auth:h['Authorization']=auth
        c.request(method,path,headers=h);r=c.getresponse();data=r.read();result=(r.status,dict(r.getheaders()),data);c.close();return result
    def test_html_and_series_require_identity_not_unguessable_url(self):
        for p in ['/', '/'+self.name, '/auth.json']:
            s,h,b=self.call(p);self.assertEqual(s,401);self.assertNotIn(b'SYNTHETIC_ONLY',b);self.assertEqual(h['Cache-Control'],'no-store, private')
        self.assertEqual(self.call(auth=self.auth)[0],200);self.assertEqual(self.call('/'+self.name,auth=self.auth)[0],200)
    def test_wrong_and_malformed_credentials_refused(self):
        for a in ['Basic invalid@@','Bearer token','Basic '+base64.b64encode('測試:wrong'.encode()).decode()]:self.assertEqual(self.call(auth=a)[0],401)
    def test_host_origin_spoof_and_read_only_methods(self):
        self.assertEqual(self.call(auth=self.auth,headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.call(auth=self.auth,headers={'Origin':'https://evil.example'})[0],403)
        for method in ['POST','PUT','DELETE','OPTIONS']:self.assertEqual(self.call(auth=self.auth,method=method)[0],405)
        self.assertFalse((self.root/'new-file').exists())
    def test_paths_listing_credentials_and_query_not_served(self):
        for p in ['/auth.json','/%FF','/../auth.json','/%2e%2e%2fauth.json','/%252e%252e%252fauth.json','/','/?password=x']:
            code=self.call(p,auth=self.auth)[0];self.assertEqual(code,200 if p=='/' else 404)
        self.assertEqual(self.call('/'+self.name,auth=self.auth,method='HEAD')[0],200)
    def test_tamper_symlink_and_security_headers(self):
        s,h,b=self.call(auth=self.auth);self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy']);self.assertNotIn('Access-Control-Allow-Origin',h)
        self.assertEqual(h['Referrer-Policy'],'no-referrer');self.assertEqual(h['X-Content-Type-Options'],'nosniff')
        p=self.root/self.name;p.write_bytes(b'X'*p.stat().st_size);self.assertEqual(self.call('/'+self.name,auth=self.auth)[0],409)
        p.unlink();p.symlink_to(self.root/'auth.json');self.assertEqual(self.call('/'+self.name,auth=self.auth)[0],404)
    def test_auth_no_overwrite_and_git_path_refusal(self):
        with self.assertRaises(FileExistsError):create_auth(self.root/'auth.json','test',self.password)
        os.chmod(self.root/'auth.json',0o644)
        with self.assertRaises(ValueError):load_auth(self.root/'auth.json')
        (self.root/'.git').mkdir()
        with self.assertRaises(ValueError):external(self.root/'secret')
    def test_failed_auth_throttle(self):
        for _ in range(5):self.assertEqual(self.call(auth='Basic invalid')[0],401)
        s,h,b=self.call(auth=self.auth);self.assertEqual(s,429);self.assertEqual(h['Retry-After'],'60')

if __name__=='__main__':unittest.main()
