"""Explicit separate evidence package; retain every old ledger-package member."""
from io import BytesIO
from pathlib import Path
import hashlib
import json
import zipfile
from .action_sources import ROOT,HERE,dump
from .source_capture import OUT


def main():
    previous=ROOT/'deliveries/m1-actions-ledger-20261022/m1-actions-ledger-v01-20261022.zip'
    original=previous.read_bytes()
    if hashlib.sha256(original).hexdigest()!='b31bb240bd47536ab03fb627da37f0ceaa0d33460328caa328d38428d3ac80b5':raise ValueError('Original delivered package mismatch; never rewrite it')
    with zipfile.ZipFile(BytesIO(original)) as z:
        assert z.testzip() is None
        members={n:z.read(n) for n in z.namelist()}
        old_manifest=json.loads(members['ACTION_PACKAGE_MANIFEST.json'])
        assert all(hashlib.sha256(members[n]).hexdigest()==sha for n,sha in old_manifest.items())
    old_count=len(members)
    selected=set(p for p in OUT.rglob('*') if p.is_file())
    selected.update(HERE/f for f in ['source_capture.py','source_qualification.py','test_source_qualification.py','package_source_qualification.py'])
    for year in (2025,2026):
        selected.update(HERE.parent/'pressure_chart/data/calendars-20261018'/f'TWSE_{year}.{ext}' for ext in ('calendar.json','raw.json','meta.json'))
    for path in sorted(selected):
        name=str(path.relative_to(ROOT))
        if name in members:raise ValueError('No old package member may be replaced')
        members[name]=path.read_bytes()
    members['README.md']=('''# M1 官方來源資格補充 0.1

這是本輪新入口；START_HERE.md及ACTION_PACKAGE_MANIFEST.json屬前輪事件帳，原293成員完整保留。
解壓到另一新資料夾，勿覆蓋原專案。先讀股票系統M1_v0_18/rotation_research/source_qualification_20261022/README.md、REPORT.md、SOURCE_CONTRACT.md及WORK_HANDOFF.md。

標準Python可離線重現本輪來源驗收：
```bash
cd 股票系統M1_v0_18
python3 -m unittest rotation_research.test_source_qualification -v
python3 -m rotation_research.source_qualification
```

15項新測試；16官方月報317市場日／473曆日，70研究窗口只補核日曆，總淨報酬仍0合格，2窗口不足。
不能用市場開市日推定個股有價格，也不能用當前預告零命中推定沒有公司行動。
設定草稿尚未套用，新官方網域未驗；資料／策略／Android限制見REPORT，沒有新UI。
SOURCE_QUALIFICATION_MANIFEST.json核對此新包全部成員；舊ACTION manifest仍可單獨核舊原件。
這不是完整歷史專案；GitHub完整checkout仍依根AGENTS準備。打包script重建需原已交付ZIP，不在此小包另複製該ZIP。
''').encode()
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['SOURCE_QUALIFICATION_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    buf=BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,body in sorted(members.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,22,12,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,body,compresslevel=9)
    body=buf.getvalue();delivery=ROOT/'deliveries/m1-source-qualification-20261022';delivery.mkdir(parents=True,exist_ok=True)
    dest=delivery/'m1-source-qualification-v01-20261022.zip'
    if dest.exists():
        if dest.read_bytes()!=body:raise ValueError('Different existing package preserved; use new build filename')
    else:dest.write_bytes(body)
    with zipfile.ZipFile(BytesIO(body)) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest()==sha for n,sha in manifest.items())
    sha=hashlib.sha256(body).hexdigest();(delivery/'SHA256SUMS').write_text(sha+'  '+dest.name+'\n')
    receipt=dict(filename=dest.name,sha256=sha,bytes=len(body),members=len(members),old_package_members_preserved_byte_exact=old_count,
        crc='PASS',member_sha256='ALL_PASS',manifest_sha256=hashlib.sha256(members['SOURCE_QUALIFICATION_MANIFEST.json']).hexdigest())
    dump(delivery/'bundle-receipt.json',receipt);print(json.dumps(receipt))


if __name__=='__main__':main()
