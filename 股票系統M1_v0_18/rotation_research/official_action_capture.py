"""Create-only capture of explicitly approved issuer/MOPS evidence.

No implicit redirects, retries, security-page bypass or TLS/proxy overrides.
Capture success describes transport only; offline qualification is separate.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

OUT = Path(__file__).resolve().parent / 'official_actions_20261022'
HOSTS = frozenset({'www.esunbank.com', 'mops.twse.com.tw'})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def capture(name, url, out=OUT, opener=None):
    parsed = urlsplit(url)
    if (not re.fullmatch(r'[A-Za-z0-9_-]+', name)
            or parsed.scheme != 'https' or parsed.netloc not in HOSTS
            or any(x in url.upper() for x in ('TWT49U', 'TWT48U', 'TWTAUU'))):
        raise ValueError('Unsupported source; prohibited endpoints are not retried')
    raw = Path(out) / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    body, meta = raw / (name + '.response'), raw / (name + '.meta.json')
    if meta.exists():
        old = json.loads(meta.read_text())
        if old['url'] != url:
            raise ValueError('Existing capture identity conflict')
        if old['status'] == 'CAPTURED' and hashlib.sha256(body.read_bytes()).hexdigest() != old['sha256']:
            raise ValueError('Existing capture body changed')
        return old
    if body.exists():
        raise ValueError('Orphan body; diagnose before another capture')
    result = dict(name=name, url=url, attempted_at=datetime.now(timezone.utc).isoformat())
    try:
        client = opener or urllib.request.build_opener(NoRedirect())
        with client.open(url, timeout=25) as response:
            content = response.read(15_000_001)
            result.update(http=response.status, final_url=response.url,
                          content_type=response.headers.get('Content-Type'))
        if len(content) > 15_000_000:
            raise ValueError('Response exceeds capture limit')
        with body.open('xb') as f:
            f.write(content)
        result.update(status='CAPTURED', bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
    except Exception as error:
        result.update(status='FAILED', error=type(error).__name__ + ': ' + str(error))
        if isinstance(error, urllib.error.HTTPError):
            result.update(http=error.code, location=error.headers.get('Location'),
                          content_type=error.headers.get('Content-Type'))
    with meta.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    sources = {
        'esun-2025-minutes': 'https://www.esunbank.com/zh-tw/-/media/ESUNFHC/Files/Investor-Relations/Shareholders/Shareholder-Meeting/114-minutes.pdf',
        'mops-announcements-entry': 'https://mops.twse.com.tw/server-java/t39sb01?quick=1',
        'esun-2025-follow-up': 'https://www.esunbank.com/zh-tw/-/media/ESUNFHC/Files/Investor-Relations/Shareholders/Shareholder-Meeting/2025Follow-up.pdf',
    }
    for name, url in sources.items():
        print(json.dumps(capture(name, url), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
