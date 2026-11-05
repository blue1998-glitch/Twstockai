"""One exact URL GET, bounded read1 and hard wall deadline; never retries.
A full HTTP frame AND the original source parser are required. Partial bytes
remain diagnostics only. No cache/path/host substitution, no access bypass.
"""
import hashlib,signal,time
from contextlib import contextmanager
from urllib.request import Request
from urllib.error import HTTPError
from http.client import IncompleteRead
from graph_core.day1_20261103.probe_once import SAFE_HEADERS
SAFE=SAFE_HEADERS|{'accept-ranges','connection'}
CHUNK=65536
MAX_BODY=16*1024**2
class Refused(ValueError):pass
class TransferFailure(Refused):
    def __init__(self,reason,trace,partial):super().__init__(reason);self.trace=trace;self.partial=partial
@contextmanager
def wall_deadline(seconds):
    if seconds<=0:raise TimeoutError('SOURCE_WALL_DEADLINE')
    prior=signal.getsignal(signal.SIGALRM);timer=signal.getitimer(signal.ITIMER_REAL)
    if timer[0]:raise RuntimeError('EXISTING_ALARM_NOT_REPLACED')
    def expired(*_):raise TimeoutError('SOURCE_WALL_DEADLINE')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,seconds)
    try:yield
    finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,prior)

def receive(opener,url,*,stamp,max_seconds=180,max_body=MAX_BODY,clock=time.monotonic):
    start=clock();parts=[];n=0;h=hashlib.sha256();trace=dict(url=url,started_at=stamp(),http_status=None,headers={},complete=False,redirects_followed=False,read_chunk_bound=CHUNK,read_calls=0)
    # Identity encoding preserves the declared-byte relation. Do not ask for a
    # Range of the old failed body; the NEW attempt is an independent whole GET.
    try:
        with wall_deadline(max_seconds):
            with opener.open(url,timeout=min(35,max_seconds)) as response:
                headers={k.lower():v for k,v in response.headers.items()}
                trace.update(http_status=response.status,effective_url=response.geturl(),headers={k:v for k,v in headers.items() if k in SAFE})
                if response.status!=200 or response.geturl()!=url:raise Refused('STATUS_OR_REDIRECT_REFUSED')
                if headers.get('content-encoding','identity').lower() not in ('','identity'):raise Refused('UNREQUESTED_CONTENT_ENCODING')
                length=headers.get('content-length');transfer=headers.get('transfer-encoding','').lower()
                if length is not None and (not length.isdigit() or int(length)>max_body):raise Refused('DECLARED_LENGTH_INVALID_OR_OVER_BOUND')
                if transfer and length is not None:raise Refused('AMBIGUOUS_HTTP_FRAMING')
                if transfer and transfer.lower()!='chunked':raise Refused('UNSUPPORTED_HTTP_FRAMING')
                expected=int(length) if length is not None else None;trace['declared_bytes']=expected
                # Preserve an explicitly instrumented custom opener's read hook.
                # Native urllib HTTPResponse still uses bounded read1.
                read=vars(response).get('read') or getattr(response,'read1',None) or response.read
                while True:
                    if clock()-start>max_seconds:raise TimeoutError('SOURCE_WALL_DEADLINE')
                    trace['read_calls']+=1
                    try:b=read(min(CHUNK,max_body+1-n))
                    except IncompleteRead as error:
                        if error.partial:parts.append(error.partial);h.update(error.partial);n+=len(error.partial)
                        raise
                    if not b:break
                    parts.append(b);h.update(b);n+=len(b)
                    if n>max_body:raise Refused('ACTUAL_BODY_OVER_BOUND')
                    if expected is not None and n>expected:raise Refused('HTTP_LENGTH_OVERFLOW')
                if expected is not None and n!=expected:raise Refused('HTTP_PREMATURE_EOF')
                # A close-delimited response has no independently verified framing.
                if expected is None and transfer!='chunked':raise Refused('HTTP_COMPLETENESS_UNPROVEN')
            raw=b''.join(parts);trace.update(complete=True,bytes=n,sha256=h.hexdigest(),framing='CONTENT_LENGTH' if expected is not None else 'CHUNKED_TERMINAL')
            return raw,trace
    except Exception as error:
        if isinstance(error,HTTPError):trace.update(http_status=error.code,headers={k.lower():v for k,v in error.headers.items() if k.lower() in SAFE})
        trace.update(error=type(error).__name__+': '+str(error),received_bytes=n,received_sha256=h.hexdigest(),shortfall_bytes=max(0,trace['declared_bytes']-n) if trace.get('declared_bytes') is not None else None)
        raise TransferFailure(trace['error'],trace,b''.join(parts)) from error
    finally:
        trace.update(completed_at=stamp(),wall_seconds=clock()-start)
