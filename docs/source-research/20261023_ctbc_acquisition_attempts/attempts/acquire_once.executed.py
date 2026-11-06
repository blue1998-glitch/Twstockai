from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, urllib.request, urllib.error, zipfile

OUT = Path('/workspace/m1-ctbc-source-archive-20261023')
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args): return None

def fetch(key, url):
    meta = OUT / (key + '.meta.json')
    if meta.exists(): raise RuntimeError('Already attempted: do not retry ' + key)
    m = dict(url=url, method='GET', requested_at=now(), retries=0, redirects_followed=False)
    body = b''
    try:
        with urllib.request.build_opener(NoRedirect).open(urllib.request.Request(url, headers={'User-Agent': 'Twstockai-source-archive/1.0'}), timeout=45) as r:
            body = r.read(); m.update(http=r.status, final_url=r.url, headers=dict(r.headers.items()), status='HTTP_RESPONSE_CAPTURED')
    except urllib.error.HTTPError as e:
        body = e.read(); m.update(http=e.code, final_url=e.url, headers=dict(e.headers.items()), status='HTTP_REFUSED_STOPPED', error=str(e))
    except Exception as e:
        m.update(http=None, status='TRANSPORT_FAILED_STOPPED', error=repr(e), headers=None)
    m.update(completed_at=now(), response_bytes=len(body), response_sha256=sha(body))
    (OUT / (key + '.response')).write_bytes(body); dump(meta, m)
    print(json.dumps(m, ensure_ascii=False), flush=True)
    return m, body

url = 'https://chatgpt.com/api/library/files/libfile_7d513796b7ec81918df10357f09073c8/download'
m, body = fetch('library-download-attempt', url)
expected_sha = '8a095132003632b7497b1ced4566d64bf0c123332d04cc19bc5aa421d0fa2b95'
valid = m['http'] == 200 and len(body) == 28364 and sha(body) == expected_sha
if valid:
    p = OUT / 'Twstockai-v010-Work-source-handoff-20261023.zip'; p.write_bytes(body)
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise ValueError('ZIP CRC failed')
    dump(OUT / 'acquisition-summary.json', dict(work_archive='OBTAINED_EXACT_EXPECTED_SIZE_SHA', official_fallback_attempted=False))
else:
    m2, body2 = fetch('ctbc-direct-attempt', 'https://ecorp.ctbcbank.com/cts/static/ag_dividend_printer.jsp')
    dump(OUT / 'acquisition-summary.json', dict(work_archive='NOT_OBTAINED', work_full_handoff='NOT_OBTAINED_NOT_READ', official_fallback_attempted=True, official_http=m2['http'], official_status=m2['status'], official_semantic_verification='PENDING' if m2['http'] == 200 else 'NOT_OBTAINED_NOT_READ'))
