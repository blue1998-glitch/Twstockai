"""Create a separate reproducible scoped-source package; preserve old bytes."""
from io import BytesIO
import hashlib
import json
import zipfile
from .action_sources import ROOT, HERE, dump
from .action_scope_sources import OUT, REVIEW


def main():
    previous = ROOT / 'deliveries/m1-official-actions-20261022/m1-official-actions-v02-20261022.zip'
    original = previous.read_bytes()
    if hashlib.sha256(original).hexdigest() != '39688bd3342bce357699abf13a091aff474c129038e56bf3fb62a8138dbe615c':
        raise ValueError('Old delivered package changed; preserve it')
    with zipfile.ZipFile(BytesIO(original)) as z:
        assert z.testzip() is None
        members = {n: z.read(n) for n in z.namelist()}
        for name in ('OFFICIAL_ACTIONS_MANIFEST.json', 'SOURCE_QUALIFICATION_MANIFEST.json', 'ACTION_PACKAGE_MANIFEST.json'):
            assert all(hashlib.sha256(members[n]).hexdigest() == s for n, s in json.loads(members[name]).items())
    old_count = len(members)
    selected = {p for folder in (OUT, REVIEW) for p in folder.rglob('*') if p.is_file()}
    selected.update(HERE / n for n in ('action_scope.py', 'action_scope_sources.py', 'test_action_scope.py', 'package_action_scope.py'))
    for p in sorted(selected):
        name = str(p.relative_to(ROOT))
        if name in members:
            raise ValueError('Old package member replacement prohibited')
        members[name] = p.read_bytes()
    members['ACTION_SCOPE_START_HERE.md'] = '''# M1公司行動適用對象／版本核對0.3

新入口：股票系統M1_v0_18/rotation_research/action_scope_20261023/README.md、REPORT、CONTRACT、WORK_HANDOFF。
原410成員與各歷史入口保持，另加入最新Work原件及本輪獨立新程式。
解壓至新資料夾，進入股票系統M1_v0_18：
```bash
python3 -m unittest rotation_research.test_action_scope -v
python3 -m rotation_research.action_scope_sources
```
標準Python離線，無新依賴或查詢；只驗本版24測試，不把舊數字冒作本版通過。
2884配股DIRECT_PUBLISHED、2867股東換股及台泥資本公積提案分開；權利證書上市／匯費不跨案。
新資格重新跑70窗仍拒算、2不足、8窗另列換股影響未支援；沒有每日淨帳或六方案新績效。
完整公司行動、最終來源／精度／可賣日、淨分配與期初權利仍缺，真正總淨報酬0合格。Android未測。
ACTION_SCOPE_MANIFEST.json核全部其他成員；三層舊manifest可各自獨立核對。
此為研究小包，完整checkout仍依GitHub根AGENTS準備；重建打包需原交付ZIP，不在包內重複塞ZIP。
'''.encode()
    manifest = {n: hashlib.sha256(b).hexdigest() for n, b in sorted(members.items())}
    members['ACTION_SCOPE_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 23, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            z.writestr(info, body, compresslevel=9)
    body = buf.getvalue(); delivery = ROOT / 'deliveries/m1-action-scope-20261023'
    delivery.mkdir(parents=True, exist_ok=True)
    dest = delivery / 'm1-action-scope-v03-20261023.zip'
    if dest.exists() and dest.read_bytes() != body:
        raise ValueError('Existing package differs; preserve and use a new name')
    if not dest.exists(): dest.write_bytes(body)
    with zipfile.ZipFile(BytesIO(body)) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest() == s for n, s in manifest.items())
    digest = hashlib.sha256(body).hexdigest()
    (delivery / 'SHA256SUMS').write_text(digest + '  ' + dest.name + '\n')
    receipt = dict(filename=dest.name, sha256=digest, bytes=len(body), members=len(members),
                   original_package_members_byte_exact=old_count, crc='PASS', manifest='ALL_PASS')
    dump(delivery / 'bundle-receipt.json', receipt); print(json.dumps(receipt))


if __name__ == '__main__':
    main()
