import pathlib,subprocess,json,hashlib,concurrent.futures,urllib.request,urllib.parse
root=pathlib.Path('/workspace/Twstockai');out=pathlib.Path('/workspace/Twstockai-preservation-20261029');c=(out/'commit').read_text()
paths=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',c],cwd=root).decode().splitlines()
def verify(p):
 expected=subprocess.check_output(['git','show',c+':'+p],cwd=root);url='https://raw.githubusercontent.com/blue1998-glitch/Twstockai/'+c+'/'+urllib.parse.quote(p)
 h=hashlib.sha256();n=0
 with urllib.request.urlopen(url,timeout=120) as r:
  status=r.status
  for b in iter(lambda:r.read(1048576),b''):h.update(b);n+=len(b)
 assert n==len(expected) and h.hexdigest()==hashlib.sha256(expected).hexdigest(),p
 return dict(path=p,bytes=n,sha256=h.hexdigest(),http=status)
rows=[];errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 tasks={ex.submit(verify,p):p for p in paths}
 for f in concurrent.futures.as_completed(tasks):
  try:r=f.result();rows.append(r);print('VERIFIED',r['path'],flush=True)
  except Exception as e:errors.append(dict(path=tasks[f],error=str(e)));print('ERROR',tasks[f],str(e),flush=True)
r=dict(fixed_commit=c,files=rows,errors=errors,all_verified=not errors,verification='Independent fixed-SHA GitHub raw HTTP bytes compared to Git objects; ZIP members already matched original local SHA256. No product tests.')
(out/'readback.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print('RESULT',len(rows),len(errors))
