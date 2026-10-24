"""Append company-component 0.9 to the exact immutable 693-member 0.8 archive."""
from io import BytesIO
import hashlib
import json
import zipfile

from .action_sources import ROOT,HERE,dump


def main():
    old=ROOT/'deliveries/m1-source-contracts-20261023/m1-source-contracts-v08-20261023.zip'
    raw=old.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='3b14522f29a03017a462c2d84eeb86f4b85151c01c9ae9a30f3fe051ba21cb72':raise ValueError('Exact original 0.8 archive required')
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):raise ValueError('Invalid parent archive')
        members={n:z.read(n) for n in z.namelist()}
    if len(members)!=693:raise ValueError('Exact 693 old members required')
    for n,b in members.items():
        if n.endswith('_MANIFEST.json'):
            if not all(hashlib.sha256(members[p]).hexdigest()==s for p,s in json.loads(b).items()):raise ValueError('Parent manifest mismatch')
    selected={p for p in (HERE/'capital_components_20261023').rglob('*') if p.is_file()}
    selected.update(HERE/n for n in ['capital_components.py','capital_components_sources.py','test_capital_components.py','package_capital_components.py'])
    for p in sorted(selected):
        n=str(p.relative_to(ROOT))
        if n in members:raise ValueError('Replacing an old member is forbidden')
        members[n]=p.read_bytes()
    members['CAPITAL_COMPONENTS_START_HERE.md']='''# 公司分項研究0.9離線重現

先讀股票系統M1_v0_18/rotation_research/capital_components_20261023/README.md、CONTRACT、REPORT、WORK_HANDOFF。
原0.8的693成員與十層manifest逐位元保留，舊入口只屬各自歷史版本。
解壓到全新目錄，cd 股票系統M1_v0_18，標準Python離線執行：
```bash
python3 -m unittest rotation_research.test_capital_components rotation_research.test_source_contracts -v
python3 -m rotation_research.capital_components_sources
```
本輪29新＋0.8相關31＝60，與前輪31新＋29回歸範圍不同；新解壓同60不累加。
不需網路／PDF工具／瀏覽器。原公開說明書已在舊成員內，新增391／456抽字與實際視讀PNG；xref警告／初次parser失敗與修正保留。
公司股東160200＋員工18000＝178200仟股只同家族對帳，非個人實配；29.05只公司計算參照，不是Raw價格或估值。
70拒算、2不足、8換股影響未支援、合格總淨報酬0，daily／journal空，無新六方案或Android通過。
CAPITAL_COMPONENTS_MANIFEST.json核全部其他成員，原十manifest仍有效。
這不是完整checkout；工程依GitHub最新AGENTS重新bootstrap，不以此包覆寫專案。
'''.encode()
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['CAPITAL_COMPONENTS_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    buf=BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(members.items()):
            i=zipfile.ZipInfo(n,date_time=(2026,10,23,12,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16
            z.writestr(i,b,compresslevel=9)
    body=buf.getvalue();d=ROOT/'deliveries/m1-capital-components-20261023';d.mkdir(exist_ok=True)
    p=d/'m1-capital-components-v09-20261023.zip'
    if p.exists() and p.read_bytes()!=body:raise ValueError('Different archive already exists; choose a new name')
    if not p.exists():p.write_bytes(body)
    digest=hashlib.sha256(body).hexdigest();(d/'SHA256SUMS').write_text(digest+'  '+p.name+'\n')
    result=dict(filename=p.name,bytes=len(body),sha256=digest,members=len(members),parent_v08_members_byte_exact=693,manifest_entries=len(manifest),below_32_MiB=len(body)<32*1024*1024)
    dump(d/'bundle-receipt.json',result);print(json.dumps(result))


if __name__=='__main__':main()
