import pathlib,json,hashlib,zipfile,subprocess,os,collections,shutil
base=pathlib.Path('/workspace');root=base/'Twstockai';out=base/'Twstockai-preservation-20261029';stage=out/'closure';stage.mkdir(exist_ok=True);o=json.loads((out/'external-inventory.json').read_text());assert not any(x['status'] in ['security_hold','header_review'] for x in o['rows']);chosen=[x for x in o['rows'] if x['status']=='unique'];groups=[];g=[];size=0
for x in chosen:
 if g and size+x['bytes']>120000000:groups.append(g);g=[];size=0
 g.append(x);size+=x['bytes']
if g:groups.append(g)
packs=[]
for i,g in enumerate(groups,1):
 p=stage/f'external-artifacts-{i:03}.zip'
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for x in g:
   b=(base/x['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==x['sha256'];z.writestr(x['path'],b);x['archive']=p.name
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  for x in g:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
 assert p.stat().st_size<100000000
 packs.append(dict(path=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),members=len(g)));print(p.name,p.stat().st_size,flush=True)
o['archives']=packs;o['scope']='Project-related regular files in /workspace/m1-*, shared, library-files, scratch. Excludes Git internals, generated dependency/bytecode directories; no system secrets or private broker inputs.'
(stage/'external-manifest.json').write_text(json.dumps(o,ensure_ascii=False,indent=2))
original=json.loads((out/'inventory-final.json').read_text());changed=[]
for x in original['files']:
 if hashlib.sha256((root/x['path']).read_bytes()).hexdigest()!=x['sha256']:changed.append(x['path'])
assert not changed,changed
prior=json.loads((out/'final-readback.json').read_text());assert len(prior['files'])==4
(stage/'prior-final-readback.json').write_text(json.dumps(prior,ensure_ascii=False,indent=2))
for src,name in [('/tmp/preserve_cloud.py','preserve_project.py'),('/tmp/cloud_readback.py','verify_fixed_github_bytes.py'),('/tmp/cloud_close_inventory.py','inventory_external.py'),('/tmp/build_cloud_closure.py','build_closure.py')]:shutil.copyfile(src,stage/name)
summary=dict(project_files=len(original['files']),project_all_preserved=True,external_files=len(o['rows']),external_counts=o['counts'],new_distinct_external_contents=len(chosen),new_archives=len(packs),new_zip_members_verified=True,original_project_unchanged=True,unresolved_project_artifacts=[],git_metadata='local backup only; not public',runtime_dependency_caches='not project deliverables; excluded',product_tests_executed=0,producer_runs=0,local_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip())
(stage/'closure.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
(stage/'README.md').write_text('''# 原Cloud工作區同步結清\n\n本輪只保存、核對與交接，不開始產品工程，不重跑舊測試或producer。\n\n專案目錄6581個檔案已於[原保存交付](../m1-original-cloud-preservation-20261029/)保存；本輪再次核對全數原指紋未變。補查專案旁40組相關工作資料夾：共10258個成果檔，7314份已在原GitHub樹、2155份已由前輪專案封包保存；622種獨有內容於本目錄ZIP補存，另167份相同副本由manifest指向同一內容，不重複計獨立成果。\n\nexternal-manifest.json逐檔列原路徑、bytes、SHA256、已保存位置或新封包；新ZIP全部成員由原bytes製作，CRC與SHA256均核對。前輪最後4檔的獨立GitHub讀回紀錄補存prior-final-readback.json。\n\n截至本次盤點，未保存的專案成果為0。Git內部metadata、系統／套件及bytecode快取不作交付；原專案的快取已前輪完整保留。沒有刪除原檔或搬移唯一副本。strong credential／private key及真實敏感header模式未命中；內容限既有公開來源與專案研究輸出，不公開私人券商／集保資料。\n\n舊診斷只反映當時狀態，不能用來否定遠端已保存的0.3／0.4及後續成果。所有策略、來源、UNKNOWN／null及正式資格限制保持；本地HEAD仍392b94a4，tracked/index0、untracked890保留，因已封存而不需為清空狀態刪除它們。原工作區仍是歷史checkout，不是最新工程起點。無法確認另一Codex是否停寫，不能宣稱已完成唯一寫入者協調。\n\n本工作區的保存任務可告一段落。後續開發僅由指定唯一Codex以最新遠端接續，先核祖先與保全，不從本地舊HEAD直接覆蓋遠端。完整本機備份仍在 /workspace/Twstockai-preservation-20261029/workspace.tar，不把含Git內部資料的tar公開上傳。\n\n## 下載\n\n'''+''.join(f'- [{p["path"]}]({p["path"]})：{p["bytes"]} bytes，SHA256 `{p["sha256"]}`\n' for p in packs))
# commit only new delivery entries, preserve live index and HEAD
ref=subprocess.check_output(['git','ls-remote','origin','refs/heads/dev/m1-v018-chart-annotations'],cwd=root).decode().split()[0];assert ref=='d7f57bab3f4617f0e22b2605d1bf05a5befd1616',ref
env=dict(os.environ,GIT_INDEX_FILE=str(out/'closure.index'))
def git(*a,**kw):return subprocess.check_output(['git',*a],cwd=root,env=env,**kw).decode().strip()
git('read-tree',ref);dest='deliveries/m1-original-cloud-closure-20261029/'
for p in stage.iterdir():
 blob=git('hash-object','-w',str(p));git('update-index','--add','--cacheinfo','100644',blob,dest+p.name)
commit=git('commit-tree',git('write-tree'),'-p',ref,input=b'Complete original Cloud artifact preservation including external project outputs\n');(out/'closure-commit').write_text(commit);print('COMMIT',commit,flush=True)
assert git('ls-remote','origin','refs/heads/dev/m1-v018-chart-annotations').split()[0]==ref
subprocess.run(['git','push','origin',commit+':refs/heads/dev/m1-v018-chart-annotations'],cwd=root,check=True)
