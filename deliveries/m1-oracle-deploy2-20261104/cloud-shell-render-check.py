import hashlib,io,json,os,stat,subprocess,sys,urllib.request,zipfile
from pathlib import Path
SIZE=22009
SHA='4fd5ad731af5017dbea2e7238a05c83dd98be2401bf80a1c3d05b195e111ea64'
URL='https://raw.githubusercontent.com/blue1998-glitch/Twstockai/86027b20fea9710d578ff3aa738041d45c8468c2/deliveries/m1-oracle-deploy2-20261104/Twstockai_ORACLE_DEPLOY2_render_native_fix.pyz'
os.umask(0o077)
root=Path.home()/'.local/share/twstockai-oracle-deploy2'
if any(p.is_symlink() for p in (root,*root.parents)):sys.exit('停止：路徑不安全')
root.mkdir(mode=0o700,parents=True,exist_ok=True)
if stat.S_IMODE(root.stat().st_mode)&0o077:sys.exit('停止：目錄須只限本人')
app=root/('tool-'+SHA+'.pyz');upload=Path.home()/'Twstockai_ORACLE_DEPLOY2_render_native_fix.pyz'
if app.is_symlink() or upload.is_symlink():sys.exit('停止：連結不安全')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):return None
try:
 if app.exists():raw=app.read_bytes()
 elif upload.exists():raw=upload.read_bytes()
 else:
  with urllib.request.build_opener(NoRedirect()).open(URL,timeout=30) as r:
   if r.status!=200:raise ValueError()
   raw=r.read(SIZE+1)
 if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError()
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  names=z.namelist()
  if len(names)!=4 or set(names)!={'__main__.py','deploy.py','legacy.py','MANIFEST.json'}:raise ValueError()
  if z.testzip() is not None:raise ValueError()
  for f in z.infolist():
   if f.file_size>100000 or stat.S_IFMT(f.external_attr>>16) not in (0,stat.S_IFREG):raise ValueError()
  manifest=json.loads(z.read('MANIFEST.json'))
  if len(manifest['files'])!=3 or {x['path'] for x in manifest['files']}!=set(names)-{'MANIFEST.json'}:raise ValueError()
  for x in manifest['files']:
   data=z.read(x['path'])
   if len(data)!=x['bytes'] or hashlib.sha256(data).hexdigest()!=x['sha256']:raise ValueError()
except Exception:sys.exit('停止：下載或完整來源校驗失敗；未執行')
if not app.exists():
 fd=os.open(app,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw)
print('工具已完整校驗；第一步只讀取官方資料，不建立資源。',flush=True)
print('本次只作唯讀定位；請回報「查詢未解析」行，先不執行review/apply。',flush=True)
raise SystemExit(subprocess.run([sys.executable,str(app),'plan']).returncode)
