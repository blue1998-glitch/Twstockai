import pathlib,os,json,hashlib,subprocess,re,collections
base=pathlib.Path('/workspace');out=base/'Twstockai-preservation-20261029';saved=json.loads((out/'inventory-final.json').read_text());known={x['sha256']:dict(kind='project_preservation',path=x['path']) for x in saved['files']};ref='d7f57bab3f4617f0e22b2605d1bf05a5befd1616';tree={}
for t in subprocess.check_output(['git','ls-tree','-r','-z',ref],cwd=base/'Twstockai').split(b'\0'):
 if t:
  a,p=t.split(b'\t',1);tree.setdefault(a.decode().split()[2],p.decode())
rows=[];new={};excluded=[]
for top in sorted(base.iterdir()):
 if not top.is_dir() or not (top.name.startswith('m1-') or top.name in ['shared','library-files','scratch']):continue
 for d,ds,fs in os.walk(top):
  for skip in ['.git','node_modules','__pycache__']:
   if skip in ds:ds.remove(skip);excluded.append(str(pathlib.Path(d,skip).relative_to(base)))
  for n in sorted(fs):
   p=pathlib.Path(d)/n;name=str(p.relative_to(base))
   if not p.is_file() or p.is_symlink():excluded.append(name);continue
   b=p.read_bytes();h=hashlib.sha256(b).hexdigest();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();row=dict(path=name,bytes=len(b),sha256=h)
   if blob in tree:row.update(status='already_github',remote_path=tree[blob])
   elif h in known:row.update(status='already_project_preservation',reference=known[h])
   elif re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16}',b):row.update(status='security_hold')
   elif re.search(rb'(?im)^(?:authorization|proxy-authorization|set-cookie):\s*(?!\[|redacted|<)[^\r\n]{12,}',b):row.update(status='header_review')
   elif h in new:row.update(status='duplicate_new',reference=new[h])
   else:row.update(status='unique');new[h]=name
   rows.append(row)
 print('SCANNED',top.name,flush=True)
obj=dict(remote=ref,rows=rows,excluded_generated_directories=excluded,counts=dict(collections.Counter(x['status'] for x in rows)))
(out/'external-inventory.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2));print('COUNTS',obj['counts']);print('UNIQUE_BYTES',sum(x['bytes'] for x in rows if x['status']=='unique'));print('HOLDS',[(x['path'],x['status']) for x in rows if x['status'] in ['security_hold','header_review']])
