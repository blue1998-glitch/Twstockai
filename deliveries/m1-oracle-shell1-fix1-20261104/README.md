# Cloud Shell compartments補正0.2

已重現並修正工具把`--compartment-id-in-subtree true`錯送成無值開關的問題；不是要求使用者改權限。22唯一方法＝2新增＋20工具回歸通過，未跑舊UI／行情驗收。實際下載固定GitHub新版、校驗後啟動通過；Codex無Oracle登入，只核安全停止，**本人帳戶查詢是否恢復仍待實跑**。

原0.1包／合成產品／FM3保留。新版唯讀，不建機，不放寬免費資格；建機／私人HTTPS後段仍未完成。

[完整固定入口Python](cloud-shell-start.py) · [固定工具](Twstockai_ORACLE_SHELL1.pyz?raw=true) · [校驗](release.json)

登入原Oracle控制台，開同一Cloud Shell，貼下方整段；不用填OCID、SHA或憑證，不需刪舊版本：

```bash
python3 - <<'PY'
import hashlib,io,json,os,stat,subprocess,sys,urllib.request,zipfile
from pathlib import Path
URL='https://raw.githubusercontent.com/blue1998-glitch/Twstockai/fad734a5ce1f255e366dfdf3ad99ebabb08159ea/deliveries/m1-oracle-shell1-fix1-20261104/Twstockai_ORACLE_SHELL1.pyz'
SIZE=11790
SHA='f9850b55b7340e63db45210db9c01f5bfc07eef76b8abaa5b7b57e52bb14d526'
os.umask(0o077)
root=Path.home()/'.local/share/twstockai-oracle-shell1'
if any(p.is_symlink() for p in (root,*root.parents)):sys.exit('停止：私有路徑含連結；建立0')
root.mkdir(mode=0o700,parents=True,exist_ok=True)
if root.stat().st_uid!=os.getuid() or stat.S_IMODE(root.stat().st_mode)&0o077:sys.exit('停止：目錄權限不安全；建立0')
app=root/('tool-'+SHA+'.pyz')
upload=Path.home()/'Twstockai_ORACLE_SHELL1.pyz'
if app.is_symlink() or upload.is_symlink():sys.exit('停止：檔案連結不安全；建立0')
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):return None
try:
 if app.is_file():raw=app.read_bytes()
 elif upload.is_file():raw=upload.read_bytes()
 else:
  with urllib.request.build_opener(NoRedirect()).open(URL,timeout=30) as r:
   if r.status!=200:raise ValueError('HTTP')
   raw=r.read(SIZE+1)
except Exception:sys.exit('停止：下載不可達；可使用Cloud Shell檔案上傳同名公開工具，再貼此指令；建立0')
if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:sys.exit('停止：固定來源校驗不符；未執行，建立0')
try:
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  files=z.infolist();names=[f.filename for f in files]
  if len(names)!=3 or set(names)!={'__main__.py','MANIFEST.json','README.txt'}:raise ValueError('members')
  if any(f.flag_bits&1 or stat.S_IFMT(f.external_attr>>16) not in (0,stat.S_IFREG) or f.file_size>100000 for f in files):raise ValueError('mode')
  if z.testzip() is not None:raise ValueError('CRC')
  m=json.loads(z.read('MANIFEST.json'))
  if m['schema']!='oracle-shell-tool-release/0.1' or {v['path'] for v in m['files']}!={'__main__.py','README.txt'} or len(m['files'])!=2:raise ValueError('manifest')
  for v in m['files']:
   b=z.read(v['path'])
   if len(b)!=v['bytes'] or hashlib.sha256(b).hexdigest()!=v['sha256']:raise ValueError('SHA')
except Exception:sys.exit('停止：工具封包不安全；未執行，建立0')
if not app.exists():
 fd=os.open(app,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw)
print('固定工具已校驗；現在只作唯讀檢查，不會建立資源。',flush=True)
raise SystemExit(subprocess.run([sys.executable,str(app),'inspect']).returncode)
PY
```

只回報安全摘要；若仍有查詢失敗，新版會列固定操作名稱與安全錯誤類別，不要貼完整JSON／OCID／IP／token。
