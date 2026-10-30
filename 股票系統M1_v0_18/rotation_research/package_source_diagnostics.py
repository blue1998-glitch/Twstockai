"""Add a reproducible source diagnostics layer; never replace old ZIP members."""
from io import BytesIO
import hashlib
import json
import zipfile

from .action_sources import HERE, ROOT, dump


def main():
    previous = ROOT / 'deliveries/m1-resolution-validation-20261023/m1-resolution-verified-v04-20261023.zip'
    body = previous.read_bytes()
    if hashlib.sha256(body).hexdigest() != '526d6510e5c2ce416565c11e2389e9f2df9e270b546720e11f6a14d3071e14a9':
        raise ValueError('Exact formal 0.4 validation package required')
    with zipfile.ZipFile(BytesIO(body)) as z:
        if z.testzip() is not None or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Invalid parent ZIP')
        members = {n:z.read(n) for n in z.namelist()}
    original_count = len(members)
    for name, payload in members.items():
        if name.endswith('_MANIFEST.json'):
            for member, sha in json.loads(payload).items():
                if hashlib.sha256(members[member]).hexdigest() != sha:
                    raise ValueError('Parent manifest mismatch')
    selected = {p for p in (HERE / 'source_diagnostics_20261023').rglob('*') if p.is_file()}
    selected.update(HERE / n for n in ['source_diagnostics.py', 'source_diagnostics_sources.py',
        'test_source_diagnostics.py', 'package_source_diagnostics.py'])
    for p in sorted(selected):
        name = str(p.relative_to(ROOT))
        if name in members:
            raise ValueError('Parent member replacement forbidden')
        members[name] = p.read_bytes()
    members['SOURCE_DIAGNOSTICS_START_HERE.md'] = '''# 獨立來源診斷0.5

保留正式0.4原完整驗收包全部528成員。新附層不是新淨帳／行情或策略版本。
先讀股票系統M1_v0_18/rotation_research/source_diagnostics_20261023/README.md、CONTRACT、REPORT、WORK_HANDOFF。
解壓至新目錄，cd 股票系統M1_v0_18，以標準Python離線執行：
```bash
python3 -m unittest rotation_research.test_source_diagnostics rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
python3 -m rotation_research.source_diagnostics_sources
```
來源及抽字已封存，重現不需新網路或pdftotext。765頁PDF只有第1／55頁受核，xref警告保存。
兩缺價日仍UNKNOWN／Raw null；70拒算、2不足、8換股未支援、真正總淨報酬0。
SOURCE_DIAGNOSTICS_MANIFEST.json核全部其他成員，舊六層manifest仍有效。
本包非全系統checkout；工程需依最新GitHub AGENTS重新bootstrap，不以舊入口覆蓋專案。
封存capture-original-script.txt僅是本次擷取記錄，勿自動執行或重試受阻來源。
'''.encode()
    manifest = {n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['SOURCE_DIAGNOSTICS_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n,b in sorted(members.items()):
            info = zipfile.ZipInfo(n,date_time=(2026,10,23,12,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            z.writestr(info,b,compresslevel=9)
    body = buf.getvalue(); delivery = ROOT / 'deliveries/m1-source-diagnostics-20261023'
    delivery.mkdir(exist_ok=True)
    path = delivery / 'm1-source-diagnostics-v05-20261023.zip'
    if path.exists() and path.read_bytes() != body:
        raise ValueError('Different package exists; preserve and choose a new name')
    if not path.exists():path.write_bytes(body)
    sha = hashlib.sha256(body).hexdigest()
    (delivery/'SHA256SUMS').write_text(sha+'  '+path.name+'\n')
    result = dict(filename=path.name,sha256=sha,bytes=len(body),members=len(members),
        parent_v04_validation_members_byte_exact=original_count,manifest_entries=len(manifest))
    dump(delivery/'bundle-receipt.json',result); print(json.dumps(result))


if __name__ == '__main__':main()
