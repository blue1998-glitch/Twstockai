"""M-MOB1: authenticated, allowlisted, read-only serving of an existing preview.

Stdlib only; no engine, source API, Journal changes or public listener. Real
remote use needs separately approved HTTPS/private-network termination. This
module alone does not create a phone-accessible URL or durable storage.
"""
import argparse,base64,getpass,hashlib,hmac,json,os,re,secrets,stat,time,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,unquote
from rotation_research import artifact_codec as codec

VERSION='private-mobile-preview/0.1'


def external(path):
    p=Path(path).expanduser().resolve()
    if any((a/'.git').exists() for a in (p,*p.parents)):
        raise ValueError('Private files must be outside Git working trees')
    return p


def create_auth(path,username,password):
    p=external(path)
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',username) or len(password)<16:
        raise ValueError('Explicit username and at least 16 password characters required')
    salt=secrets.token_bytes(16);key=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1)
    value=dict(schema='mobile-owner-auth/0.1',username=username,salt=salt.hex(),key=key.hex())
    p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f)


def load_auth(path):
    p=Path(path)
    if p.is_symlink() or stat.S_IMODE(p.stat().st_mode)&0o077:raise ValueError('Private owner-only credential file required')
    p=external(p);v=json.loads(p.read_text())
    if not isinstance(v.get('username'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',v['username']) or v.get('schema')!='mobile-owner-auth/0.1' or not re.fullmatch('[0-9a-f]{32}',v.get('salt','')) or not re.fullmatch('[0-9a-f]{128}',v.get('key','')):
        raise ValueError('Invalid credential format')
    return v


def preview_index(path):
    p=external(path)
    if Path(path).is_symlink():raise ValueError('Preview symlink refused')
    raw=codec.read_bytes(p);m=re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)
    if not m:raise ValueError('Saved market preview required')
    v=json.loads(m[1]);allowed={p.name:dict(path=p,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())}
    charts=0
    for s in v['stocks']:
        desc=s.get('preview_series')
        if not desc:continue
        name=desc['path']
        if not re.fullmatch(r'series-[a-f0-9]{64}\.json',name) or name[7:-5]!=desc['sha256']:
            raise ValueError('Invalid series descriptor')
        q=p.parent/name
        if q.is_symlink() or codec.info(q)['bytes']!=desc['bytes']:raise ValueError('Missing private series')
        allowed[name]=dict(path=q,bytes=desc['bytes'],sha256=desc['sha256']);charts+=1
    hashes=[]
    for script in re.findall(rb'<script(?:\s[^>]*)?>(.*?)</script>',raw,re.S):
        hashes.append("'sha256-"+base64.b64encode(hashlib.sha256(script).digest()).decode()+"'")
    return p,allowed,dict(stocks=len(v['stocks']),charts=charts,as_of=v['summary']['as_of']),hashes


def batch_index(path):
    """Explicit immutable preview catalogue, not a filesystem/document-root grant."""
    from html import escape
    manifest=external(path)
    if Path(path).is_symlink():raise ValueError('Batch index symlink refused')
    spec=json.loads(manifest.read_bytes())
    if spec.get('schema')!='private-saved-batches/0.1' or not spec['batches']:raise ValueError('Invalid saved batch catalogue')
    files={};hashes=[];links=[];summaries=[];seen=set()
    for entry in spec['batches']:
        p,allowed,summary,scripts=preview_index(entry['path'])
        if p in seen:raise ValueError('Duplicate saved preview')
        seen.add(p)
        raw=codec.read_bytes(p)
        if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256'] or summary['as_of']!=entry['as_of']:
            raise ValueError('Batch preview fingerprint/date mismatch')
        prefix='batch-'+entry['sha256']
        files.update({prefix+'/'+name:dict(item,parent=item['path'].parent) for name,item in allowed.items()})
        hashes.extend(scripts);summaries.append(summary)
        links.append('<li><a href="/'+prefix+'/'+p.name+'">'+escape(entry['as_of']+' '+entry['run_id'])+'</a></li>')
    raw=('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>私人已保存批次</title><style>body{font:18px sans-serif;padding:18px;overflow-wrap:anywhere}li{padding:16px 0}a{line-height:1.8}</style><h1>私人已保存批次</h1><p>最新批次列於最前；未通過來源日期資格的擷取不列入。切換只讀保存圖，不補算。</p><ul>'+''.join(links)+'</ul></html>').encode()
    files['batches']=dict(raw=raw,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    return manifest,files,dict(batches=summaries,stocks=summaries[0]['stocks'],charts=summaries[0]['charts'],as_of=summaries[0]['as_of']),list(set(hashes))


def make_server(preview,credentials,*,port=0,allowed_hosts=(),clock=time.monotonic,batches=None,head=None):
    head_path=external(head) if head else None
    head_signature=None
    if head_path:
        if Path(head).is_symlink():raise ValueError('Head symlink refused')
        head_signature=head_path.read_bytes()
        batches=json.loads(head_signature)['batch_index']
    page,files,summary,hashes=batch_index(batches) if batches else preview_index(preview)
    catalogue_state=dict(signature=head_signature,page=page,files=files,summary=summary,hashes=hashes)
    catalogue_lock=threading.Lock();artifact_read_lock=threading.Lock()
    auth=load_auth(credentials);failures=[]
    class Handler(BaseHTTPRequestHandler):
        server_version='TwstockaiPrivate';sys_version=''
        def log_message(self,*args):pass  # never log Authorization, URLs, stock selection or quotes
        def reply(self,status,body=b'',kind='text/plain; charset=utf-8',extra=None):
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
            for k,v in {'Cache-Control':'no-store, private','Pragma':'no-cache','Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','X-Robots-Tag':'noindex, nofollow','Content-Security-Policy':"default-src 'none'; script-src "+' '.join(getattr(self,'active_hashes',hashes))+"; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'none'"}.items():self.send_header(k,v)
            for k,v in (extra or {}).items():self.send_header(k,v)
            self.end_headers()
            if self.command!='HEAD':self.wfile.write(body)
        def permitted(self):
            host=self.headers.get('Host','')
            if host not in self.server.allowed_hosts:return self.reply(403,b'Forbidden')
            origin=self.headers.get('Origin')
            if origin and origin not in {'http://'+host,'https://'+host}:return self.reply(403,b'Forbidden')
            now=clock();failures[:]=[t for t in failures if now-t<60]
            if len(failures)>=5:return self.reply(429,b'Try later',extra={'Retry-After':'60'})
            good=False
            try:
                scheme,value=self.headers.get('Authorization','').split(' ',1)
                if scheme!='Basic':raise ValueError
                decoded=base64.b64decode(value,validate=True).decode();user,password=decoded.split(':',1)
                if len(password)>1024:raise ValueError
                derived=hashlib.scrypt(password.encode(),salt=bytes.fromhex(auth['salt']),n=16384,r=8,p=1).hex()
                good=hmac.compare_digest(user.encode(),auth['username'].encode()) & hmac.compare_digest(derived,auth['key'])
            except (ValueError,UnicodeError):pass
            if not good:
                # Missing auth is the browser challenge, not a password guess.
                if self.headers.get('Authorization'):failures.append(now)
                return self.reply(401,b'Authentication required',extra={'WWW-Authenticate':'Basic realm="Twstockai private", charset="UTF-8"'})
            return True
        def dispatch(self):
            if self.permitted() is not True:return
            if self.command not in ('GET','HEAD'):return self.reply(405,b'Read only',extra={'Allow':'GET, HEAD'})
            active_files=files;active_page=page
            if head_path:
                try:
                    with catalogue_lock:
                        if head_path.is_symlink():raise ValueError('Head symlink refused')
                        signature=head_path.read_bytes()
                        if signature!=catalogue_state['signature']:
                            new_page,new_files,new_summary,new_hashes=batch_index(json.loads(signature)['batch_index'])
                            catalogue_state.update(signature=signature,page=new_page,files=new_files,summary=new_summary,hashes=new_hashes)
                            self.server.allowed_files=new_files;self.server.preview_summary=new_summary
                        active_files=catalogue_state['files'];active_page=catalogue_state['page'];self.active_hashes=catalogue_state['hashes']
                except (OSError,ValueError,KeyError):return self.reply(409,b'Saved batch head unavailable')
            try:
                parsed=urlsplit(self.path);name=unquote(parsed.path,errors='strict').removeprefix('/')
            except (ValueError,UnicodeError):return self.reply(404,b'Not found')
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or '%' in name or '\\' in name:return self.reply(404,b'Not found')
            if not name:name='batches' if batches else page.name
            item=active_files.get(name)
            if not item:return self.reply(404,b'Not found')
            if 'raw' in item:return self.reply(200,item['raw'],'text/html; charset=utf-8')
            p=item['path']
            if p.is_symlink() or p.resolve().parent!=item.get('parent',active_page.parent):return self.reply(404,b'Not found')
            try:
                if not codec.exists(p) or codec.info(p)['bytes']!=item['bytes']:return self.reply(409,b'Saved artifact changed')
            except (OSError,ValueError,KeyError,IndexError,TypeError,RecursionError):return self.reply(409,b'Saved artifact changed')
            if self.command=='HEAD':
                self.send_response(200);self.send_header('Content-Length',str(item['bytes']));self.send_header('Cache-Control','no-store, private');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();return
            try:
                with artifact_read_lock:raw=codec.read_bytes(p,expected_bytes=item['bytes'],expected_sha=item['sha256'])
            except (OSError,ValueError,KeyError,IndexError,TypeError,RecursionError):return self.reply(409,b'Saved artifact changed')
            if hashlib.sha256(raw).hexdigest()!=item['sha256']:return self.reply(409,b'Saved artifact changed')
            self.reply(200,raw,'text/html; charset=utf-8' if name.endswith('.html') else 'application/json; charset=utf-8')
        do_GET=do_HEAD=do_POST=do_PUT=do_DELETE=do_OPTIONS=dispatch
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True
    server.allowed_hosts=set(allowed_hosts)|{'127.0.0.1:'+str(server.server_port),'localhost:'+str(server.server_port)}
    server.preview_summary=summary;server.allowed_files=files
    return server


def main():
    p=argparse.ArgumentParser();p.add_argument('--preview');p.add_argument('--batches');p.add_argument('--head');p.add_argument('--credentials',required=True);p.add_argument('--port',type=int,default=8765);p.add_argument('--allowed-host',action='append',default=[]);p.add_argument('--init-user');a=p.parse_args()
    if a.init_user:
        first=getpass.getpass('New private password: ')
        if first!=getpass.getpass('Repeat password: '):raise ValueError('Passwords differ')
        create_auth(a.credentials,a.init_user,first);print('Owner credential created; no listener started');return
    if sum(map(bool,(a.preview,a.batches,a.head)))!=1:p.error('Choose --preview, --batches or --head')
    server=make_server(a.preview,a.credentials,port=a.port,allowed_hosts=a.allowed_host,batches=a.batches,head=a.head)
    print(json.dumps(dict(status='LOOPBACK_ONLY_NOT_A_PHONE_URL',port=server.server_port,**server.preview_summary)),flush=True)
    try:server.serve_forever()
    finally:server.server_close()

if __name__=='__main__':main()
