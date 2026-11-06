"""Append bridge 0.6 to the exact 0.5 artifact, preserving every old member."""
from io import BytesIO
import hashlib
import json
import zipfile

from .action_sources import ROOT, HERE, dump


def main():
    old=ROOT/'deliveries/m1-source-diagnostics-20261023/m1-source-diagnostics-v05-20261023.zip'
    raw=old.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='7144793cb2e359b7536fa72dd2c764144e4aee4a6aa3e986eabcaa785435a36d':
        raise ValueError('Exact source diagnostics 0.5 package required')
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):
            raise ValueError('Invalid parent package')
        members={n:z.read(n) for n in z.namelist()}
    old_count=len(members)
    for n,b in members.items():
        if n.endswith('_MANIFEST.json'):
            if not all(hashlib.sha256(members[p]).hexdigest()==sha for p,sha in json.loads(b).items()):
                raise ValueError('Parent manifest mismatch')
    selected={p for p in (HERE/'offline_source_bridge_20261023').rglob('*') if p.is_file()}
    selected.update(HERE/n for n in ['offline_source_bridge.py','offline_source_bridge_sources.py',
        'test_offline_source_bridge.py','package_offline_source_bridge.py'])
    selected.update(p for p in (ROOT/'deliveries/m1-offline-source-bridge-20261023').iterdir() if p.is_file())
    for p in sorted(selected):
        name=str(p.relative_to(ROOT))
        if name in members:raise ValueError('Parent member replacement forbidden')
        members[name]=p.read_bytes()
    members['OFFLINE_SOURCE_BRIDGE_START_HERE.md']='''# 離線來源0.6：開始閱讀

先讀股票系統M1_v0_18/rotation_research/offline_source_bridge_20261023/README.md、CONTRACT、REPORT、WORK_HANDOFF。
原來源0.5包575成員及所有舊manifest逐位元保留，舊入口只屬其歷史版本。
解壓至全新目錄，cd 股票系統M1_v0_18，標準Python離線執行：
```bash
python3 -m unittest rotation_research.test_offline_source_bridge rotation_research.test_source_diagnostics rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
python3 -m rotation_research.offline_source_bridge_sources
```
原橋接ZIP及metadata已含入；不需網路、pdftotext或瀏覽器。91項是30新＋61本輪回歸。
兩停牌起日有直接來源，舊UNKNOWN／Raw null與缺價拒算不改；70拒算、2不足、8換股不支援、真正總淨報酬0。
一般法律不是個人免稅／淨收，沒有新數值帳、六方案或Android通過。
OFFLINE_SOURCE_BRIDGE_MANIFEST.json核全部其他成員，原七manifest仍有效。
本包是離線重現附件，不是全系統checkout；工程以GitHub最新AGENTS先bootstrap，勿拿舊入口覆蓋專案。
'''.encode()
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['OFFLINE_SOURCE_BRIDGE_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    buf=BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(members.items()):
            info=zipfile.ZipInfo(n,date_time=(2026,10,23,12,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,b,compresslevel=9)
    body=buf.getvalue();d=ROOT/'deliveries/m1-offline-source-layer-20261023';d.mkdir(exist_ok=True)
    path=d/'m1-offline-source-layer-v06-20261023.zip'
    if path.exists() and path.read_bytes()!=body:raise ValueError('Different package exists; choose a new name')
    if not path.exists():path.write_bytes(body)
    sha=hashlib.sha256(body).hexdigest();(d/'SHA256SUMS').write_text(sha+'  '+path.name+'\n')
    result=dict(filename=path.name,bytes=len(body),sha256=sha,members=len(members),
        parent_v05_members_byte_exact=old_count,manifest_entries=len(manifest),original_bridge_zip_included_byte_exact=True)
    dump(d/'bundle-receipt.json',result);print(json.dumps(result))


if __name__=='__main__':main()
