"""Append source 0.7 without replacing any of the exact 606 parent members."""
from io import BytesIO
import hashlib
import json
import zipfile

from .action_sources import ROOT, HERE, dump


def main():
    old=ROOT/'deliveries/m1-offline-source-layer-20261023/m1-offline-source-layer-v06-20261023.zip'
    raw=old.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='e6398a1ee7863e72e0f236b51213ff21a9a2892cbc6841b79789f49a72d1e496':
        raise ValueError('Exact original 0.6 package required')
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):
            raise ValueError('Invalid parent package')
        members={n:z.read(n) for n in z.namelist()}
    if len(members)!=606: raise ValueError('Exact 606 old members required')
    for n,b in members.items():
        if n.endswith('_MANIFEST.json'):
            if not all(hashlib.sha256(members[p]).hexdigest()==s for p,s in json.loads(b).items()):
                raise ValueError('Parent manifest mismatch')
    selected={p for p in (HERE/'source_followup_20261023').rglob('*') if p.is_file()}
    selected.update(HERE/n for n in ['source_followup.py','source_followup_sources.py',
        'test_source_followup.py','package_source_followup.py'])
    for p in sorted(selected):
        name=str(p.relative_to(ROOT))
        if name in members: raise ValueError('Old artifact replacement forbidden')
        members[name]=p.read_bytes()
    members['SOURCE_FOLLOWUP_START_HERE.md']='''# 獨立來源0.7

先讀股票系統M1_v0_18/rotation_research/source_followup_20261023/README.md、CONTRACT、REPORT、WORK_HANDOFF。
606原0.6成員與八個舊manifest逐位元保留，原入口只屬各自歷史版本。
解壓到全新目錄，cd 股票系統M1_v0_18，標準Python離線執行：
```bash
python3 -m unittest rotation_research.test_source_followup rotation_research.test_offline_source_bridge -v
python3 -m rotation_research.source_followup_sources
```
29新＋30相關回歸＝59；新解壓同59不累加。三份實際官方原件已含入，不需網路、pdftotext或瀏覽器。
只補來源事實，TAIFEX佐證不是TWSE直接普通股公告；公司完成不是個人權利；月份／仟股／仟元精度保持。
70拒算、2不足、8換股影響未支援，真正總淨報酬0，沒有新六方案或Android通過。
SOURCE_FOLLOWUP_MANIFEST.json核全部其他成員，舊八manifest仍有效。
此為離線重現附件，不是完整checkout；工程使用GitHub最新AGENTS先bootstrap，不拿舊包覆蓋專案。
'''.encode()
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['SOURCE_FOLLOWUP_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    buf=BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(members.items()):
            info=zipfile.ZipInfo(n,date_time=(2026,10,23,12,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,b,compresslevel=9)
    body=buf.getvalue();d=ROOT/'deliveries/m1-source-followup-20261023';d.mkdir(exist_ok=True)
    path=d/'m1-source-followup-v07-20261023.zip'
    if path.exists() and path.read_bytes()!=body: raise ValueError('Different archive exists; choose a new name')
    if not path.exists(): path.write_bytes(body)
    sha=hashlib.sha256(body).hexdigest();(d/'SHA256SUMS').write_text(sha+'  '+path.name+'\n')
    receipt=dict(filename=path.name,bytes=len(body),sha256=sha,members=len(members),
        parent_v06_members_byte_exact=606,manifest_entries=len(manifest),all_three_captured_originals_included=True)
    dump(d/'bundle-receipt.json',receipt);print(json.dumps(receipt))


if __name__=='__main__':main()
