"""Separate source supplement package; prior 375 members remain byte-exact."""
from io import BytesIO
import hashlib
import json
import zipfile
from .action_sources import ROOT, HERE, dump
from .official_action_capture import OUT


def main():
    previous = ROOT / 'deliveries/m1-source-qualification-20261022/m1-source-qualification-v01-20261022.zip'
    original = previous.read_bytes()
    if hashlib.sha256(original).hexdigest() != '2411f934b290edd3f65cb30b5ebb3b20c9aba9fb5099e454fd5a57e335652542':
        raise ValueError('Original source package changed; preserve it')
    with zipfile.ZipFile(BytesIO(original)) as old:
        assert old.testzip() is None
        members = {n: old.read(n) for n in old.namelist()}
        for filename in ('SOURCE_QUALIFICATION_MANIFEST.json', 'ACTION_PACKAGE_MANIFEST.json'):
            assert all(hashlib.sha256(members[n]).hexdigest() == s for n, s in json.loads(members[filename]).items())
    old_count = len(members)
    selected = {p for p in OUT.rglob('*') if p.is_file()}
    selected.update(HERE / name for name in ('official_action_capture.py', 'official_actions.py',
                                            'test_official_actions.py', 'package_official_actions.py'))
    for path in sorted(selected):
        name = str(path.relative_to(ROOT))
        if name in members:
            raise ValueError('Cannot replace old package members')
        members[name] = path.read_bytes()
    members['OFFICIAL_ACTIONS_START_HERE.md'] = '''# M1 官方行動來源補充0.2

先讀股票系統M1_v0_18/rotation_research/official_actions_20261022/README.md、REPORT.md、CONTRACT.md與WORK_HANDOFF.md。
此包保留前包375成員及歷史README，新增此0.2入口與原件／獨立producer／測試。
解壓到新資料夾，進入股票系統M1_v0_18後：
```bash
python3 -m unittest rotation_research.test_official_actions -v
python3 -m rotation_research.official_actions
```
標準Python，離線讀已封存原件及雙SHA文字，不需PDF依賴。勿執行網路capture作為驗收。
0.010015129為公開金額與同次面額推導精度，非實際未圓整最終比例；公司發放完成不認證個人到款或掛牌日。
完整行動／淨分配／期初權利未核，真正總淨報酬仍0合格；無新UI／Android。
OFFICIAL_ACTIONS_MANIFEST.json核此包全部其他成員，兩層舊manifest亦保留。
完整專案仍由指定GitHub分支依根AGENTS準備；打包腳本需前已交付ZIP，不另把ZIP重複塞進小包。
'''.encode()
    manifest = {n: hashlib.sha256(b).hexdigest() for n, b in sorted(members.items())}
    members['OFFICIAL_ACTIONS_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 22, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, body, compresslevel=9)
    body = buf.getvalue()
    delivery = ROOT / 'deliveries/m1-official-actions-20261022'
    delivery.mkdir(parents=True, exist_ok=True)
    dest = delivery / 'm1-official-actions-v02-20261022.zip'
    if dest.exists() and dest.read_bytes() != body:
        raise ValueError('Different existing delivery preserved; choose a new filename')
    if not dest.exists():
        dest.write_bytes(body)
    with zipfile.ZipFile(BytesIO(body)) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest() == s for n, s in manifest.items())
    digest = hashlib.sha256(body).hexdigest()
    (delivery / 'SHA256SUMS').write_text(digest + '  ' + dest.name + '\n')
    receipt = dict(filename=dest.name, sha256=digest, bytes=len(body), members=len(members),
                   prior_members_preserved_byte_exact=old_count, crc='PASS', member_sha256='ALL_PASS')
    dump(delivery / 'bundle-receipt.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
