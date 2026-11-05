import io,json,tempfile,unittest
from pathlib import Path
from http.client import HTTPResponse
from graph_core.prod_day2_20261105.transport import receive
from graph_core.prod_source3_20261105 import resume as m
class Sock:
    def __init__(self,b):self.b=b
    def makefile(self,*a):return io.BytesIO(self.b)
class Fake:
    def __init__(self,status,headers,body):self.status=status;self.headers=headers;self.body=body;self.requests=[]
    def open(self,req,timeout):
        url=getattr(req,'full_url',req)
        self.requests.append(req);raw=('HTTP/1.1 '+str(self.status)+' OK\r\n'+''.join(k+': '+v+'\r\n' for k,v in self.headers.items())+'\r\n').encode()+self.body
        response=HTTPResponse(Sock(raw));response.begin();response.geturl=lambda:url;return response
class RangeTests(unittest.TestCase):
    def setUp(self):
        self.prefix=b'[1,';self.tail=b'2]';self.proof=dict(start=3,total=5,missing=2,etag='"version"',last_modified='SYNTHETIC_TIME')
        self.headers={'Content-Range':'bytes 3-4/5','Content-Length':'2','ETag':'"version"','Last-Modified':'SYNTHETIC_TIME'}
    def test_exact_206_and_request_binding(self):
        f=Fake(206,self.headers,self.tail);whole,part,t=m.recover(self.prefix,self.proof,f);self.assertEqual(whole,b'[1,2]');self.assertEqual(part,self.tail);self.assertEqual(len(f.requests),1);self.assertEqual(f.requests[0].get_header('Range'),'bytes=3-');self.assertEqual(f.requests[0].get_header('If-range'),'"version"');self.assertTrue(t['old_prefix_used'])
    def test_default_transport_still_refuses_206(self):
        f=Fake(206,self.headers,self.tail)
        with self.assertRaises(m.TransferFailure) as caught:receive(f,m.URL,stamp=lambda:'SYNTHETIC')
        self.assertEqual(caught.exception.trace['http_status'],206)
    def test_whole_200_never_uses_old_prefix(self):
        f=Fake(200,{'Content-Length':'3','ETag':'"new"'},b'[9]');whole,part,t=m.recover(self.prefix,self.proof,f);self.assertEqual(whole,b'[9]');self.assertFalse(t['old_prefix_used'])
    def test_bad_window_total_etag_or_modified_refused(self):
        for key,value in [('Content-Range','bytes 2-4/5'),('Content-Range','bytes 3-4/6'),('ETag','"different"'),('Last-Modified','different'),('Content-Length','3')]:
            with self.subTest(key=key,value=value):
                h=dict(self.headers);h[key]=value;f=Fake(206,h,self.tail)
                with self.assertRaises(m.TransferFailure):m.recover(self.prefix,self.proof,f)
                self.assertEqual(len(f.requests),1)
    def test_truncated_206_or_200_is_not_completed(self):
        for status,headers in [(206,self.headers),(200,{'Content-Length':'5'})]:
            with self.assertRaises(m.TransferFailure):m.recover(self.prefix,self.proof,Fake(status,headers,b'2'))
    def test_denial_redirect_416_never_retry(self):
        for status in [403,429,302,416]:
            f=Fake(status,{'Content-Length':'0'},b'')
            with self.assertRaises(m.TransferFailure):m.recover(self.prefix,self.proof,f)
            self.assertEqual(len(f.requests),1)
    def test_weak_or_conflicting_prefix_is_refused(self):
        root=Path(tempfile.mkdtemp(prefix='range-',dir=str(m.WORK/'tests')));p=root/'prefix';p.write_bytes(self.prefix)
        t=dict(url=m.URL,http_status=200,complete=False,partial_bytes=3,partial_sha256=m.store.c.sha(self.prefix),headers={'content-length':'5','etag':'W/"version"','last-modified':'SYNTHETIC_TIME'})
        with self.assertRaises(ValueError):m.choose_prefix([(p,t)])
    def test_longest_prefix_verified_from_bytes(self):
        root=Path(tempfile.mkdtemp(prefix='range-',dir=str(m.WORK/'tests')));c=[]
        for i,b in enumerate([b'[1',self.prefix]):
            p=root/str(i);p.write_bytes(b);c.append((p,dict(url=m.URL,http_status=200,complete=False,partial_bytes=len(b),partial_sha256=m.store.c.sha(b),headers={'content-length':'5','etag':'"version"','last-modified':'SYNTHETIC_TIME'})))
        b,proof=m.choose_prefix(c);self.assertEqual(b,self.prefix);self.assertEqual(proof['missing'],2)
    def test_alternative_does_not_borrow_target_date_or_fill_missing_ohlcv(self):
        from .alternative import assess
        a=assess(b'[{"Date":"2026-11-05","SecuritiesCompanyCode":"TEST"}]','2026-11-04')
        self.assertEqual(a['source_dates'],['2026-11-05']);self.assertIn('Open',a['missing_fields']);self.assertFalse(a['normalized_or_relabelled']);self.assertEqual(a['status'],'NOT_ADOPTED')
    def test_cached_range_is_exact_and_zero_network(self):
        from unittest.mock import patch
        root=Path(tempfile.mkdtemp(prefix='repeat-',dir=str(m.WORK/'tests')))
        with patch.object(m,'original_prefix',return_value=(self.prefix,self.proof)):
            f=Fake(206,self.headers,self.tail);r=m.run(work=root,opener=f);self.assertEqual(len(f.requests),1)
            before={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            class NoNetwork:
                def open(self,*a,**k):raise AssertionError('NO_REPEAT_GET')
            again=m.run(work=root,opener=NoNetwork());self.assertEqual(again['this_execution_GETs'],0)
            self.assertEqual(before,{str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()})
if __name__=='__main__':unittest.main(verbosity=2)
