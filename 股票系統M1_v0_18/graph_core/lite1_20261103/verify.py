"""Readonly closure/source-preservation and owner HTTP verification; no core IO."""
import base64,hashlib,http.client,json,shutil,sys,time
from pathlib import Path
from urllib.parse import urlsplit
from graph_core.lite1_20261103.build import source_manifest_check,RESERVE
from graph_core_chart.mobile_private import batch_index
from rotation_research import artifact_codec as c

def allocated(paths):
 seen=set();total=0
 for p in paths:
  st=p.stat();key=(st.st_dev,st.st_ino)
  if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total

def closure(p):
 if p.exists():return {p}
 root,v=c.manifest(p);files={c.sidecar(p),root/'.du2-root.json'}
 if v['schema']==c.INTERNED:
  files.update(closure(c.resolve(root,v['wire_path'])));files.update(closure(c.resolve(root,v['anchor_path'])))
 else:
  for x in v['pieces']:files.update(closure(c.resolve(root,x['path']))) if x['kind']=='span' else files.add(c.blob_path(root,x['sha256']))
 return files

def verify(root,out,audit):
 root=Path(root);out=Path(out);started=time.monotonic();prior=json.loads(Path(audit).read_bytes());known=source_manifest_check(root,prior)
 checks={}
 for rel in ['current-increment-run.json','fm3-continuation.json']:
  raw=(root/rel).read_bytes();checks[rel]=c.sha(raw)==known[rel]['sha256']
 if not all(checks.values()):raise ValueError('SOURCE_HEAD_CONTENT_CHANGED')
 conn=json.loads((out/'connection-private.json').read_bytes());cat=json.loads(Path(conn['catalogue']).read_bytes());_,allowed,summary,_=batch_index(conn['catalogue'],linked_roots=[root]);batches=[]
 for entry in cat['batches']:
  state=json.loads((Path(entry['path']).parent/'prepared-state-private.json').read_bytes());assert len(state['stocks'])==1986
  graphs=[s for s in state['stocks'] if s.get('preview_series')]
  for s in graphs:
   d=s['preview_series'];route='batch-'+entry['sha256']+'/'+d['path'];item=allowed[route]
   if (item['sha256'],item['bytes'])!=(d['sha256'],d['bytes']) or not item['path'].is_relative_to(root):raise ValueError('ORIGINAL_GRAPH_ROUTE_CHANGED')
  batches.append(dict(as_of=entry['as_of'],identities=len(state['stocks']),original_graph_routes=len(graphs),html_bytes=entry['bytes'],html_sha256=entry['sha256'],chart_validation='All original descriptors/closure + preserved source audit; selected actual HTTP/Chromium SHA reads, NOT a new full-market graph GET pass'))
 auth='Basic '+base64.b64encode((conn['auth']['username']+':'+conn['auth']['password']).encode()).decode();u=urlsplit(conn['origin']);httpchecks=[]
 def request(path,expected,authorized=True,headers=None,method='GET'):
  h=dict(headers or {})
  if authorized:h['Authorization']=auth
  client=http.client.HTTPConnection(u.hostname,u.port,timeout=60);client.request(method,path,headers=h);r=client.getresponse();raw=r.read();code=r.status;hdr=dict(r.getheaders());client.close();assert code==expected,(path,code,expected);httpchecks.append(dict(check=path if path in ['/','/batches'] else 'allowlist/access control',expected=expected,actual=code));return hdr,raw
 h,_=request('/',401,False);assert 'Location' not in h
 h,_=request('/',303);assert h['Location'].startswith('/batch-')
 request('/batches',200);request('/owner-auth.json',404);request('/%2e%2e%2fowner-auth.json',404);request('/',403,headers={'Origin':'https://invalid.example'});request('/',405,method='POST')
 entry=cat['batches'][0];state=json.loads((Path(entry['path']).parent/'prepared-state-private.json').read_bytes());d=state['stocks'][0]['decision_detail'];h,raw=request('/batch-'+entry['sha256']+'/'+d['path'],200);assert len(raw)==d['bytes'] and c.sha(raw)==d['sha256'];assert h['Cache-Control']=='no-store, private'
 head=json.loads((root/'current-increment-run.json').read_bytes());olddeps=closure(Path(head['private_preview']['path']));newfiles=[p for p in out.rglob('*') if p.is_file() and not p.is_symlink()];newbytes=allocated(newfiles);free=shutil.disk_usage(out).free;assert free>=RESERVE and newbytes<256*1024*1024
 report=dict(status='PASS_PRIVATE_LITE_CLOSURE_AND_OWNER',original_audit_manifest_id=prior['manifest_id'],original_unchanged_metadata_paths=len(known),old_full_sha_repeated=False,source_heads_exact_sha=checks,batches=batches,owner_whitelisted_routes=len(allowed),http_controls=httpchecks,private_unique_regular_allocated_bytes=newbytes,free_bytes=free,minimum_free_bytes=RESERVE,old_page_dependency_allocated_bytes=allocated(olddeps),old_page_dependency_files=len(olddeps),old_page_allocation_scope='Includes entire referenced base-file/spans; shared bytes are NOT marginal page cost. Old files retained; no disk reclaimed.',backup='UNKNOWN_NO_INDEPENDENT_COPY',restart_persistence='UNKNOWN',external_android_url=None,android='NOT_TESTED_NEW_BUILD',elapsed_seconds=time.monotonic()-started)
 c.immutable(out/'final-verification-private.json',c.encoded(report));return report
if __name__=='__main__':print(json.dumps(verify(*sys.argv[1:]),ensure_ascii=False))
