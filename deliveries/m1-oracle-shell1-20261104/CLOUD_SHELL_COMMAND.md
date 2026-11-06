# 直接貼入Cloud Shell（唯讀安全查核）

本版不會建機；成功部署後段尚未完成。先本人登入Oracle控制台，開啟Cloud Shell，整段貼入。這段只有固定下載／TLS／SHA／CRC／manifest校驗及唯讀檢查，沒有Create／Update／Delete，不需填OCID或憑證。

```bash
python3 - <<'PY'
import hashlib,io,json,os,stat,subprocess,sys,urllib.request,zipfile
from pathlib import Path
URL='https://raw.githubusercontent.com/blue1998-glitch/Twstockai/485d8745dc52545675746502a3516e9ea8b9cbaf/deliveries/m1-oracle-shell1-20261104/Twstockai_ORACLE_SHELL1.pyz'
SIZE=11543
SHA='d9aca0a8f198f4e7f8bcafc3810f0ac8f1cc1dea77e7ca4a14dcd6c1191f08e7'
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

預期中文結果包含「停止」「尚未核實」「本工具資源建立0」。即使Compute分項已核，也不代表整個配置可免費建立。本版的apply不能部署，不能把本指令當作已建私人網址。

查上次狀態／阻塞計畫／停止狀態（同一Cloud Shell，路徑已完整固定）：

```bash
python3 "$HOME/.local/share/twstockai-oracle-shell1/tool-d9aca0a8f198f4e7f8bcafc3810f0ac8f1cc1dea77e7ca4a14dcd6c1191f08e7.pyz" status
python3 "$HOME/.local/share/twstockai-oracle-shell1/tool-d9aca0a8f198f4e7f8bcafc3810f0ac8f1cc1dea77e7ca4a14dcd6c1191f08e7.pyz" plan
python3 "$HOME/.local/share/twstockai-oracle-shell1/tool-d9aca0a8f198f4e7f8bcafc3810f0ac8f1cc1dea77e7ca4a14dcd6c1191f08e7.pyz" stop
```

若超過十分鐘，重新貼主指令做唯讀檢查，不手改計畫或加--force。若GitHub下載不可達，可用Cloud Shell官方檔案上傳同名公開`Twstockai_ORACLE_SHELL1.pyz`；原合成ZIP若也不能下載，則上傳`Twstockai_ORACLE_PILOT1_SYNTHETIC.zip`。程式自動在本人HOME找檔，仍須同樣固定SHA檢查，不增付費傳輸服務。不要下載、搬運或上傳任何FM3私人資料。

不要貼出私有inspection／plan JSON；只可回報終端的安全中文摘要。Android、私人HTTPS及Oracle主機均未驗／未建立。
