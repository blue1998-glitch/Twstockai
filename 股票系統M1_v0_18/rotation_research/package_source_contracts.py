"""Append source research 0.8 while preserving the exact 651 parent members."""
from io import BytesIO
import hashlib
import json
import zipfile

from .action_sources import ROOT,HERE,dump


def main():
    old=ROOT/'deliveries/m1-source-followup-20261023/m1-source-followup-v07-20261023.zip'
    raw=old.read_bytes()
    if hashlib.sha256(raw).hexdigest()!='554ec7d3c5db2d6123fe116072d13509148775f58dd425faea3743ecbf6bbb66':
        raise ValueError('Exact original 0.7 archive required')
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):raise ValueError('Invalid parent archive')
        members={n:z.read(n) for n in z.namelist()}
    if len(members)!=651:raise ValueError('Exact 651 parent members required')
    for n,b in members.items():
        if n.endswith('_MANIFEST.json'):
            if not all(hashlib.sha256(members[p]).hexdigest()==s for p,s in json.loads(b).items()):raise ValueError('Parent manifest mismatch')
    selected={p for p in (HERE/'source_contracts_20261023').rglob('*') if p.is_file()}
    selected.update(HERE/n for n in ['source_contracts.py','source_contracts_sources.py','test_source_contracts.py','package_source_contracts.py'])
    for p in sorted(selected):
        n=str(p.relative_to(ROOT))
        if n in members:raise ValueError('Parent member replacement forbidden')
        members[n]=p.read_bytes()
    members['SOURCE_CONTRACTS_START_HERE.md']='''# 來源研究0.8離線重現

先讀股票系統M1_v0_18/rotation_research/source_contracts_20261023/README.md、CONTRACT、REPORT、WORK_HANDOFF。
原0.7的651成員與九層manifest完整逐位元保留，舊入口只屬各自歷史版本。
解壓到全新目錄，cd 股票系統M1_v0_18，標準Python離線執行：
```bash
python3 -m unittest rotation_research.test_source_contracts rotation_research.test_source_followup -v
python3 -m rotation_research.source_contracts_sources
```
31新＋本輪相關29＝60，同60解壓重驗不累加。無需網路／pdftotext／瀏覽器。
既有公開說明書及新一頁官方PDF已含入；只視讀指定六頁，765頁未全書核閱，xref及轉圖快取警告保留。
Work研究附件未見／未讀與其讀回時點未知明列，不能假稱已讀。
僅來源事實，條件異議不等個人權利；股東／員工／原2867與既有2884分開，登記非上市，稅費非淨額。
70拒算、2不足、8換股影響未支援、真正總淨報酬0，daily／journal空，無六方案或Android通過。
SOURCE_CONTRACTS_MANIFEST.json核其他全部成員，原九manifest仍有效。
這不是完整checkout；工程用GitHub最新AGENTS重新bootstrap，不以此包覆寫專案。
'''.encode()
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['SOURCE_CONTRACTS_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    buf=BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(members.items()):
            i=zipfile.ZipInfo(n,date_time=(2026,10,23,12,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16
            z.writestr(i,b,compresslevel=9)
    body=buf.getvalue();d=ROOT/'deliveries/m1-source-contracts-20261023';d.mkdir(exist_ok=True)
    p=d/'m1-source-contracts-v08-20261023.zip'
    if p.exists() and p.read_bytes()!=body:raise ValueError('Different archive already exists; choose a new name')
    if not p.exists():p.write_bytes(body)
    digest=hashlib.sha256(body).hexdigest();(d/'SHA256SUMS').write_text(digest+'  '+p.name+'\n')
    result=dict(filename=p.name,bytes=len(body),sha256=digest,members=len(members),parent_v07_members_byte_exact=651,manifest_entries=len(manifest),below_32_MiB=len(body)<32*1024*1024)
    dump(d/'bundle-receipt.json',result);print(json.dumps(result))


if __name__=='__main__':main()
