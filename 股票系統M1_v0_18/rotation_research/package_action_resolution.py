"""Extend the exact previous package, with deterministic bytes and no replacement."""
from io import BytesIO
import hashlib
import json
import zipfile
from .action_sources import ROOT, HERE, dump
from .action_resolution_sources import OUT, REVIEW


def main():
    previous = ROOT / 'deliveries/m1-action-scope-20261023/m1-action-scope-v03-20261023.zip'
    original = previous.read_bytes()
    if hashlib.sha256(original).hexdigest() != '0724b40717c25e1a9361bd213b586cc1097346287e2f3df879409425add71f2e':
        raise ValueError('Previous package changed; preserve it')
    with zipfile.ZipFile(BytesIO(original)) as z:
        if z.testzip() is not None: raise ValueError('Previous ZIP CRC failed')
        members = {n:z.read(n) for n in z.namelist()}
    old_count = len(members)
    # Old manifests remain independently valid and retain their exact bytes.
    for name in ('ACTION_SCOPE_MANIFEST.json', 'OFFICIAL_ACTIONS_MANIFEST.json',
                 'SOURCE_QUALIFICATION_MANIFEST.json', 'ACTION_PACKAGE_MANIFEST.json'):
        for member, digest in json.loads(members[name]).items():
            if hashlib.sha256(members[member]).hexdigest() != digest:
                raise ValueError('Previous manifest mismatch: ' + member)
    selected = {p for folder in (OUT, REVIEW) for p in folder.rglob('*') if p.is_file()}
    selected.update(HERE/n for n in ('action_resolution.py', 'action_resolution_sources.py',
        'test_action_resolution.py', 'package_action_resolution.py'))
    for path in sorted(selected):
        name = str(path.relative_to(ROOT))
        if name in members: raise ValueError('Existing package member replacement prohibited')
        members[name] = path.read_bytes()
    members['ACTION_RESOLUTION_START_HERE.md'] = '''# 公司行動決議來源0.4

最新入口：股票系統M1_v0_18/rotation_research/action_resolution_20261023/README.md、CONTRACT、REPORT、WORK_HANDOFF。
舊470成員逐位元保留；舊START_HERE是歷史，本入口才是本包最新版本。
解壓至新目錄，進入股票系統M1_v0_18，標準Python離線執行：
```bash
python3 -m unittest rotation_research.test_action_resolution -v
python3 -m rotation_research.action_resolution_sources
```
本包含必要前輪研究上下文與新原件，可執行以上兩命令；不是全系統完整checkout。
打包重建使用完整Git checkout及舊交付ZIP，不把舊ZIP再次塞進本包；先按根AGENTS重新bootstrap。
台泥股東會通過來源與每人現金總額圓整已接入；工程假想股數的gross preview不是個人淨額／到款／期初權利。
70窗拒算、2不足、淨報酬合格0；沒有六方案新績效，Android未測。
ACTION_RESOLUTION_MANIFEST.json核所有其他成員；所有舊manifest仍可獨立核。
'''.encode()
    manifest = {n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['ACTION_RESOLUTION_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2026,10,23,12,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
            z.writestr(info,body,compresslevel=9)
    body=buf.getvalue(); delivery=ROOT/'deliveries/m1-action-resolution-20261023'
    delivery.mkdir(parents=True,exist_ok=True)
    dest=delivery/'m1-action-resolution-v04-20261023.zip'
    if dest.exists() and dest.read_bytes()!=body:
        raise ValueError('Package exists with different bytes; preserve and use a new filename')
    if not dest.exists(): dest.write_bytes(body)
    with zipfile.ZipFile(BytesIO(body)) as z:
        if z.testzip() is not None: raise ValueError('New ZIP CRC failed')
        if any(hashlib.sha256(z.read(n)).hexdigest()!=h for n,h in manifest.items()):
            raise ValueError('New member manifest failed')
    digest=hashlib.sha256(body).hexdigest()
    (delivery/'SHA256SUMS').write_text(digest+'  '+dest.name+'\n')
    receipt=dict(filename=dest.name,sha256=digest,bytes=len(body),members=len(members),
        previous_members_byte_exact=old_count,crc='PASS',manifest='ALL_PASS')
    dump(delivery/'bundle-receipt.json',receipt); print(json.dumps(receipt))


if __name__=='__main__':
    main()
