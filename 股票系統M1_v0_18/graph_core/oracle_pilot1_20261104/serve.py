"""Run only the isolated hash-bound synthetic bundle, with original owner auth.
No OCI provisioning or VPN configuration. Must remain loopback-only.
"""
import argparse,getpass,hashlib,json,re,sys
from pathlib import Path
from graph_core_chart.mobile_private import create_auth,make_server,external

def verify(root):
    root=Path(root).resolve();m=json.loads((root/'MANIFEST.json').read_bytes())
    if m.get('schema')!='synthetic-pilot-manifest/0.1' or m.get('synthetic_only') is not True or m.get('contains_private_market_data') is not False or m.get('contains_credentials') is not False:raise ValueError('ISOLATED_SYNTHETIC_MANIFEST_REQUIRED')
    seen=set()
    for item in m['files']:
        rel=Path(item['path'])
        if rel.is_absolute() or '..' in rel.parts or str(rel) in seen:raise ValueError('INVALID_BUNDLE_PATH')
        seen.add(str(rel));p=root/rel
        if any(q.is_symlink() for q in (p,*p.parents)) or not p.resolve().is_relative_to(root):raise ValueError('SYMLINK_OR_ESCAPE_REFUSED')
        raw=p.read_bytes()
        if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('BUNDLE_BYTES_CHANGED')
    if m['entry'] not in seen or not m['entry'].endswith('.html'):raise ValueError('ENTRY_NOT_BOUND')
    return root/m['entry']

def server(root,credentials,*,port=0,private_host=None):
    page=verify(root)
    if private_host and not re.fullmatch(r'[a-z0-9][a-z0-9-]*\.[a-z0-9-]+\.ts\.net',private_host):raise ValueError('EXACT_PRIVATE_TAILNET_HOST_REQUIRED')
    return make_server(page,credentials,port=port,allowed_hosts=([private_host] if private_host else []))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['verify','init-auth','serve']);p.add_argument('--bundle',default=str(Path(__file__).resolve().parent));p.add_argument('--credentials');p.add_argument('--username',default='owner');p.add_argument('--private-host');p.add_argument('--port',type=int,default=8786);a=p.parse_args()
    if a.command=='verify':verify(a.bundle);print('SYNTHETIC_BUNDLE_VERIFIED');return
    if not a.credentials:p.error('Explicit Git-external credentials path required')
    external(a.credentials)
    if a.command=='init-auth':
        first=getpass.getpass('Owner password (16+ characters, never committed): ')
        if first!=getpass.getpass('Confirm password: '):raise ValueError('PASSWORDS_DIFFER')
        create_auth(a.credentials,a.username,first);print('OWNER_AUTH_CREATED');return
    s=server(a.bundle,a.credentials,port=a.port,private_host=a.private_host)
    print('ISOLATED_SYNTHETIC_LOOPBACK_READY',flush=True)
    try:s.serve_forever()
    finally:s.server_close()
if __name__=='__main__':main()
