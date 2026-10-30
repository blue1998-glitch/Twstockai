import pathlib,json,subprocess,zipfile,hashlib,os
root=pathlib.Path('/workspace/Twstockai');out=pathlib.Path('/workspace/Twstockai-preservation-20261029');o=json.loads((out/'inventory-final.json').read_text());ref=o['remote']; dest='deliveries/m1-original-cloud-preservation-20261029';stage=out/'delivery';stage.mkdir(exist_ok=True)
rows=[x for x in o['files'] if x['status'] in ('unique','conflict','cache')];groups=[];group=[];size=0
for x in rows:
 if group and size+x['bytes']>120_000_000:groups.append(group);group=[];size=0
 group.append(x);size+=x['bytes']
if group:groups.append(group)
packs=[]
for i,g in enumerate(groups,1):
 name=f'original-cloud-{i:03d}.zip';p=stage/name
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for x in g:
   b=(root/x['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==x['sha256'];z.writestr(x['path'],b);x['archive']=name
 with zipfile.ZipFile(p) as z:
  for x in g:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
 assert p.stat().st_size<100_000_000
 packs.append(dict(path=name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),members=len(g)))
 print(name,p.stat().st_size,flush=True)
o['archives']=packs;o['scope']='All regular files under original checkout excluding .git; conflicting historical bytes archived only, current remote untouched. Archive contents verified member-by-member. No product tests or producer.'
(stage/'manifest.json').write_text(json.dumps(o,ensure_ascii=False,indent=2))
(stage/'README.md').write_text('''# 原 Cloud 工作區完整成果交付（2026-10-29）\n\n以 manifest.json 逐檔對照原工作區與固定遠端。same 及 already_saved_other_path 已存在遠端；unique、conflict、cache 原bytes保存於 ZIP（包含忽略的中間輸出及SQLite研究庫）。逐成員SHA256與原檔一致。不是新產品版本，也未執行產品測試。\n\n六份 conflict 是原工作區歷史版本，僅留在ZIP，不覆蓋新版程式、契約或入口。2026-10-25診斷描述當時缺檔狀態，不是目前0.3缺失結論；後續成果均保留。ZIP請解到獨立資料夾，勿直接覆蓋現行專案。\n\n原工作區與完整本機tar備份保留；本機HEAD不移動，因此原工作區並非最新分支的乾淨checkout。此交付只保存，不證明另一工作已暫停。沒有部署、策略修改、producer或新行情。\n\n強私鑰／GitHub憑證／AWS密鑰模式及敏感檔名掃描未命中；來源限本工作區既有專案與合成研究輸出。Git內部metadata只留本機備份，不公開。\n''')
index=str(out/'publish.index');env=dict(os.environ,GIT_INDEX_FILE=index)
def git(*a,**kw):return subprocess.check_output(['git',*a],cwd=root,env=env,**kw).decode().strip()
git('read-tree',ref)
for p in stage.iterdir():
 blob=git('hash-object','-w',str(p));git('update-index','--add','--cacheinfo','100644',blob,dest+'/'+p.name)
# expose the ten historical diagnostics directly as well, without modifying original checkout
for x in rows:
 if x['path'].startswith('docs/runtime-recovery/20261025_capital_repair_intake/'):
  blob=git('hash-object','-w',str(root/x['path']));git('update-index','--add','--cacheinfo','100644',blob,x['path'])
tree=git('write-tree');commit=git('commit-tree',tree,'-p',ref,input=b'Preserve original Cloud workspace artifacts without overwriting current work\n');(out/'commit').write_text(commit);print('COMMIT',commit)
