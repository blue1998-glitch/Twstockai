"""Add environment validation to the exact canonical 0.4 ZIP, no replacement."""
from io import BytesIO
import hashlib
import json
import zipfile
from .action_sources import ROOT, HERE, dump

OUT = HERE / 'resolution_validation_20261023'


def main():
    previous = ROOT / 'deliveries/m1-action-resolution-20261023/m1-action-resolution-v04-20261023.zip'
    body = previous.read_bytes()
    if hashlib.sha256(body).hexdigest() != '5a238227839de19449d234cb2e56c5bed73c82546f5bb58e976f359caab11740':
        raise ValueError('Canonical package changed; preserve it')
    with zipfile.ZipFile(BytesIO(body)) as z:
        assert z.testzip() is None
        members = {n: z.read(n) for n in z.namelist()}
        for n in ('ACTION_RESOLUTION_MANIFEST.json', 'ACTION_SCOPE_MANIFEST.json',
                  'OFFICIAL_ACTIONS_MANIFEST.json', 'SOURCE_QUALIFICATION_MANIFEST.json', 'ACTION_PACKAGE_MANIFEST.json'):
            assert all(hashlib.sha256(members[p]).hexdigest() == s for p, s in json.loads(members[n]).items())
    count = len(members)
    selected = {p for p in OUT.rglob('*') if p.is_file()}
    selected.update(HERE / n for n in ('test_resolution_validation.py', 'package_resolution_validation.py'))
    for p in sorted(selected):
        name = str(p.relative_to(ROOT))
        if name in members: raise ValueError('Canonical member replacement forbidden')
        members[name] = p.read_bytes()
    members['RESOLUTION_VALIDATION_START_HERE.md'] = '''# 決議0.4完整來源及本環境驗收

正式金融程式沿用action_resolution，不另發布平行草稿。原511成員逐位元保留。
先讀股票系統M1_v0_18/rotation_research/resolution_validation_20261023/README.md、REPORT、WORK_HANDOFF，及相鄰action_resolution_20261023/CONTRACT.md。
解壓至新目錄，進入股票系統M1_v0_18，標準Python離線：
```bash
python3 -m unittest rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
python3 -m rotation_research.action_resolution_sources
```
31項＝正式版本29＋新增2；毛額非淨額／到款／期初權利或績效，70窗仍拒算、2不足、合格總淨報酬0。
PDF全文byte差異／首個失敗保持，所用頁與欄位相同；不需安裝pdftotext，衍生文字已封存。
RESOLUTION_VALIDATION_MANIFEST.json核本包全部其他成員，五層舊manifest仍有效。
不是全系統完整checkout；工程仍依GitHub根AGENTS準備。打包另需原0.4 ZIP，不重複塞ZIP。
'''.encode()
    manifest = {n: hashlib.sha256(b).hexdigest() for n, b in sorted(members.items())}
    members['RESOLUTION_VALIDATION_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n, b in sorted(members.items()):
            info = zipfile.ZipInfo(n, date_time=(2026, 10, 23, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            z.writestr(info, b, compresslevel=9)
    body = buf.getvalue(); d = ROOT / 'deliveries/m1-resolution-validation-20261023'
    d.mkdir(parents=True, exist_ok=True); target = d / 'm1-resolution-verified-v04-20261023.zip'
    if target.exists() and target.read_bytes() != body:
        raise ValueError('Different package exists; preserve and choose a new name')
    if not target.exists(): target.write_bytes(body)
    with zipfile.ZipFile(BytesIO(body)) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest() == s for n, s in manifest.items())
    sha = hashlib.sha256(body).hexdigest(); (d / 'SHA256SUMS').write_text(sha + '  ' + target.name + '\n')
    r = dict(filename=target.name, sha256=sha, bytes=len(body), members=len(members),
             canonical_v04_members_byte_exact=count, crc='PASS', manifest='ALL_PASS')
    dump(d / 'bundle-receipt.json', r); print(json.dumps(r))


if __name__ == '__main__': main()
