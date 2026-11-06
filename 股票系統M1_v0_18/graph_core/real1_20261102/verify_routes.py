"""Read all authorized local artifacts by HTTP, stream hash; no copied payloads.
Private connection config and detailed source/graph files stay Git external.
"""
import argparse,base64,hashlib,http.client,json,re,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from rotation_research import artifact_codec as c
from rotation_research.private_portability import private


def verify(config):
    start=time.monotonic();v=json.loads(private(config).read_bytes());url=urlsplit(v['origin'])
    if url.hostname not in ('127.0.0.1','localhost') or url.scheme!='http':raise ValueError('LOCAL_ONLY_AUTHORIZED_TEST')
    auth='Basic '+base64.b64encode((v['auth']['username']+':'+v['auth']['password']).encode()).decode()
    page=Path(v['preview']);raw=c.read_bytes(page);state=json.loads(re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)[1]);descriptors=[dict(path=page.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),kind='html')]
    for stock in state['stocks']:
        for field in ('preview_series','preview_evidence'):
            if stock.get(field):descriptors.append(dict(stock[field],kind=field))
    def request(path,headers,method='GET'):
        con=http.client.HTTPConnection(url.hostname,url.port,timeout=180);con.request(method,path,headers=headers);r=con.getresponse();h=hashlib.sha256();length=0
        while True:
            chunk=r.read(1024*1024)
            if not chunk:break
            h.update(chunk);length+=len(chunk)
        result=(r.status,dict(r.getheaders()),length,h.hexdigest());con.close();return result
    def one(desc):
        status,headers,n,sha=request('/'+desc['path'],{'Authorization':auth})
        if status!=200 or n!=desc['bytes'] or sha!=desc['sha256']:raise ValueError('ALLOWLISTED_ARTIFACT_HTTP_SHA_OR_LENGTH_MISMATCH')
        if headers.get('Cache-Control')!='no-store, private':raise ValueError('PRIVATE_CACHE_HEADERS_CHANGED')
        return n
    with ThreadPoolExecutor(max_workers=4) as pool:total=sum(pool.map(one,descriptors))
    controls=[request('/'+descriptors[-1]['path'],{})[0],request('/'+descriptors[-1]['path'],{'Authorization':auth,'Origin':'https://evil.example'})[0],request('/owner-auth.json',{'Authorization':auth})[0],request('/integration-private.json',{'Authorization':auth})[0],request('/',{'Authorization':auth},'POST')[0]]
    if controls!=[401,403,404,404,405]:raise ValueError('PRIVATE_ACCESS_CONTROLS_CHANGED')
    return dict(status='PASS_ALL_REAL_LOCAL_HTTP_BYTES',stocks=len(state['stocks']),original_chart_gets=sum(d['kind']=='preview_series' for d in descriptors),evidence_gets=sum(d['kind']=='preview_evidence' for d in descriptors),html_gets=1,verified_artifacts=len(descriptors),verified_logical_bytes=total,exact_lengths_and_sha_match=True,payload_copies_saved=0,auth_origin_path_write_controls=controls,wall_seconds=time.monotonic()-start,provider_requests=0,external_ingress=False,android='NOT_TESTED_NEW_BUILD')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--report',required=True);a=p.parse_args();result=verify(a.config);c.immutable(private(a.report),c.encoded(result));print(json.dumps(result))
