"""Only the changed transport/source IO; synthetic HTTP is not live success."""
import io,json,tempfile,time,signal,unittest
from pathlib import Path
from http.client import HTTPResponse
from urllib.error import HTTPError
from . import transport as t,capture as m
from graph_core import market_daily as d
class Socket:
    def __init__(self,b):self.b=b
    def makefile(self,*args):return io.BytesIO(self.b)
class Opener:
    def __init__(self,body=b'[]',headers=None,data=None,deny=False):self.body=body;self.headers=headers;self.data=data;self.calls=[];self.deny=deny
    def open(self,req,timeout):
        url=getattr(req,"full_url",req)
        self.calls.append(url)
        if self.deny:raise HTTPError(url,403,'SYNTHETIC DENIED',{},None)
        body=self.data[url] if self.data else self.body
        headers=self.headers if self.headers is not None else {'Content-Length':str(len(body))}
        raw=b'HTTP/1.1 200 OK\r\n'+''.join(k+': '+v+'\r\n' for k,v in headers.items()).encode()+b'\r\n'+body
        response=HTTPResponse(Socket(raw));response.begin();response.geturl=lambda:url;return response
class TransportTests(unittest.TestCase):
    def test_exact_length_and_single_request(self):
        b=b'1234567890'*10000;o=Opener(b);raw,tr=t.receive(o,'https://official.example/data',stamp=lambda:'SYNTHETIC')
        self.assertEqual(raw,b);self.assertTrue(tr['complete']);self.assertEqual(len(o.calls),1);self.assertEqual(tr['bytes'],len(b));self.assertLessEqual(tr['read_calls'],4)
    def test_short_content_length_remains_partial(self):
        o=Opener(b'{"not":"finished',{'Content-Length':'1000'})
        with self.assertRaises(t.TransferFailure) as caught:t.receive(o,'https://official.example/data',stamp=lambda:'SYNTHETIC')
        self.assertEqual(caught.exception.partial,b'{"not":"finished');self.assertFalse(caught.exception.trace['complete']);self.assertEqual(caught.exception.trace['shortfall_bytes'],1000-len(o.body));self.assertEqual(len(o.calls),1)
    def test_real_http_chunk_parser_requires_terminal(self):
        o=Opener(b'2\r\n[]\r\n0\r\n\r\n',{'Transfer-Encoding':'Chunked'});raw,tr=t.receive(o,'https://official.example/data',stamp=lambda:'SYNTHETIC');self.assertEqual(raw,b'[]');self.assertEqual(tr['framing'],'CHUNKED_TERMINAL')
        o=Opener(b'2\r\n[]\r\n',{'Transfer-Encoding':'chunked'})
        with self.assertRaises(t.TransferFailure):t.receive(o,'https://official.example/data',stamp=lambda:'SYNTHETIC')
        self.assertEqual(len(o.calls),1)
    def test_ambiguous_or_unproven_framing_and_encoding_refused(self):
        for headers in [{'Content-Length':'2','Transfer-Encoding':'chunked'},{},{'Content-Length':'2','Content-Encoding':'gzip'}]:
            with self.subTest(headers=headers):
                with self.assertRaises(t.TransferFailure):t.receive(Opener(b'[]',headers),'https://official.example/data',stamp=lambda:'SYNTHETIC')
    def test_body_size_bound_before_acceptance(self):
        with self.assertRaises(t.TransferFailure):t.receive(Opener(b'123456'),'https://official.example/data',stamp=lambda:'SYNTHETIC',max_body=3)
    def test_custom_opener_read_override_remains_honored(self):
        from graph_core.daily_chain1_20261104.test_intake import Fake
        url=next(iter(d.URLS.values()));opener=Fake({url:b'[]'},partial=True)
        with self.assertRaises(t.TransferFailure) as caught:t.receive(opener,url,stamp=lambda:'SYNTHETIC')
        self.assertEqual(caught.exception.partial,b'[]');self.assertEqual(len(opener.calls),1)
    def test_denied_has_no_retry(self):
        o=Opener(deny=True)
        with self.assertRaises(t.TransferFailure) as caught:t.receive(o,'https://official.example/data',stamp=lambda:'SYNTHETIC')
        self.assertEqual(caught.exception.trace['http_status'],403);self.assertEqual(len(o.calls),1)
    def test_hard_wall_alarm_restored_after_blocked_read(self):
        before=signal.getsignal(signal.SIGALRM)
        with self.assertRaises(TimeoutError):
            with t.wall_deadline(.01):time.sleep(.1)
        self.assertEqual(signal.getsignal(signal.SIGALRM),before);self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0],0)
    def test_exact_codec_io_and_repeat_preserve_source_gate(self):
        from graph_core.daily_chain1_20261104.test_intake import GateTests
        root=Path(tempfile.mkdtemp(prefix='source-fixture-',dir=str(m.WORK/'tests')));old=root/'old';old.mkdir();work=root/'new'
        data=GateTests.data(None,dt='2026-01-02');receipts=[]
        for name,url in list(d.URLS.items())[:3]:
            body=data[url];h=m.c.sha(body);q=old/'capture/raw'/h;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(body);receipts.append(dict(name=name,url=url,status='RECEIVED',sha256=h,bytes=len(body),fetched_at='SYNTHETIC'))
        (old/'result-private.json').write_bytes(d.encode(dict(target_date='2026-01-02',receipts=receipts,http_trace=[dict(http_status=200)])))
        o=Opener(data=data);r=m.run('2026-01-02',work=work,old=old,opener=o)
        self.assertEqual(r['qualification']['status'],'SOURCE_QUALIFIED');self.assertEqual(r['qualification']['markets'],{'TWSE':1,'TPEX':1});self.assertEqual(len(o.calls),3)
        before={str(q):q.read_bytes() for q in work.rglob('*') if q.is_file()};again=m.run('2026-01-02',work=work,old=old,opener=o)
        self.assertEqual(again['this_execution_GETs'],0);self.assertEqual(len(o.calls),3);self.assertEqual(before,{str(q):q.read_bytes() for q in work.rglob('*') if q.is_file()})
    def test_formal_intake_uses_repaired_transport_and_preserves_original_gate(self):
        from graph_core.daily_chain1_20261104 import intake
        from graph_core.daily_chain1_20261104.test_intake import GateTests
        from unittest.mock import patch
        root=Path(tempfile.mkdtemp(prefix='formal-intake-',dir=str(m.WORK/'tests')));work=root/'stage';work.mkdir()
        (work/'baseline-private.json').write_bytes(d.encode(dict(free_bytes=m.shutil.disk_usage(work).free)))
        data=GateTests.data(None,dt='2026-01-02');o=Opener(data=data)
        with patch.object(intake.time,'sleep',lambda _:None),patch.object(t,'receive',wraps=t.receive) as reader:
            r=intake.run('2026-01-02',work=work,opener=o)
            self.assertEqual(reader.call_count,6)
        self.assertEqual(len(o.calls),6);self.assertEqual(r['qualification']['status'],'SOURCE_QUALIFIED')
        self.assertEqual(r['status'],'BLOCKED_CONTINUITY_EVIDENCE');self.assertFalse(r['new_batch_published']);self.assertEqual(r['processed_by_core'],0)
if __name__=='__main__':unittest.main(verbosity=2)
