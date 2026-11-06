"""Deterministic source bundle, preserving all exact 723 parent0.9 members."""
from io import BytesIO
import hashlib
import json
import zipfile

from .action_sources import ROOT, HERE, dump


def main():
    old = ROOT / 'deliveries/m1-capital-components-20261023/m1-capital-components-v09-20261023.zip'
    raw = old.read_bytes()
    if hashlib.sha256(raw).hexdigest() != '9a97f1aff7ad1b37da2249948ccaf62662b5af4ad9d9e3260907cecb426d8571':
        raise ValueError('Exact immutable parent0.9 archive required')
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist()) != len(set(z.namelist())): raise ValueError('Invalid parent archive')
        members = {n: z.read(n) for n in z.namelist()}
    if len(members) != 723: raise ValueError('Exact 723 old members required')
    for n, b in members.items():
        if n.endswith('_MANIFEST.json'):
            if not all(hashlib.sha256(members[p]).hexdigest() == s for p, s in json.loads(b).items()):
                raise ValueError('Parent manifest mismatch')
    selected = {p for p in (HERE / 'subsidiary_proposal_20261023').rglob('*') if p.is_file()}
    selected.update(HERE / n for n in ['subsidiary_proposal.py', 'subsidiary_proposal_sources.py',
                                      'test_subsidiary_proposal.py', 'package_subsidiary_proposal.py'])
    for p in sorted(selected):
        n = str(p.relative_to(ROOT))
        if n in members: raise ValueError('Replacing an old archive member is forbidden')
        members[n] = p.read_bytes()
    members['SUBSIDIARY_PROPOSAL_START_HERE.md'] = '''# 子公司方案來源0.10離線重現

讀股票系統M1_v0_18/rotation_research/subsidiary_proposal_20261023/README、CONTRACT、REPORT與WORK_HANDOFF。
全新目錄解壓，cd 股票系統M1_v0_18，標準Python離線執行：
```bash
python3 -m unittest rotation_research.test_subsidiary_proposal rotation_research.test_capital_components -v
python3 -m rotation_research.subsidiary_proposal_sources
```
不需網路、PDF工具或瀏覽器；已含兩新原件／meta／原生文字／五頁視讀PNG。
24新＋29相關回歸＝53；全新解壓同53不累加。詳細掃描條款parser未實作，不冒OCR。
公司子公司IPO方案非完成或個人1101配股／減資，場次矛盾與未知不修正。
原0.9的723成員及十一manifest全保留，新增manifest核全部其餘成員。
來源包不是完整checkout，不覆專案；正式工程先按最新GitHub AGENTS重新bootstrap。
'''.encode()
    manifest = {n: hashlib.sha256(b).hexdigest() for n, b in sorted(members.items())}
    members['SUBSIDIARY_PROPOSAL_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n, b in sorted(members.items()):
            i = zipfile.ZipInfo(n, date_time=(2026, 10, 23, 14, 0, 0)); i.compress_type = zipfile.ZIP_DEFLATED; i.external_attr = 0o100644 << 16
            z.writestr(i, b, compresslevel=9)
    body = buf.getvalue(); folder = ROOT / 'deliveries/m1-subsidiary-proposal-20261023'; folder.mkdir(exist_ok=True)
    p = folder / 'm1-subsidiary-proposal-v010-20261023.zip'
    if p.exists() and p.read_bytes() != body: raise ValueError('Different archive already exists; choose a new name')
    if not p.exists(): p.write_bytes(body)
    digest = hashlib.sha256(body).hexdigest(); (folder / 'SHA256SUMS').write_text(digest + '  ' + p.name + '\n')
    result = dict(filename=p.name, bytes=len(body), sha256=digest, members=len(members), parent_v09_members_byte_exact=723,
                  manifest_entries=len(manifest), below_32_MiB=len(body) < 32 * 1024 * 1024)
    dump(folder / 'bundle-receipt.json', result); print(json.dumps(result))


if __name__ == '__main__': main()
