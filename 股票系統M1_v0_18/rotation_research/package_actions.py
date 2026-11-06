"""Explicit compact, self-contained accounting evidence package; no old ZIP edits."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import zipfile
from .action_sources import HERE,ROOT,OUT,REVIEW,dump


def main():
    delivery=ROOT/'deliveries/m1-actions-ledger-20261022';delivery.mkdir(exist_ok=True)
    selected=set(p for p in OUT.rglob('*') if p.is_file())
    selected.update(HERE/p for p in ['__init__.py','core.py','store.py','study.py',
        'action_sources.py','action_ledger.py','action_fixtures.py','action_cli.py','action_study.py','package_actions.py',
        'test_action_sources.py','test_action_ledger.py','test_action_integration.py'])
    selected.update(HERE.parent/'graph_core'/p for p in ['__init__.py','core.py'])
    selected.update(HERE/'generated'/p for p in ['input.json','sources.json','design.json'])
    catalog=json.loads((OUT/'events.json').read_text())
    selected.add(REVIEW/'source-capture.json')
    for source in catalog['sources'].values():
        path=ROOT/source['path'];selected.add(path)
        meta=path.with_name(path.name+'.meta.json')
        if meta.exists():selected.add(meta)
    for source in json.loads((HERE/'generated/sources.json').read_text()):
        path=ROOT/source['path'];selected.add(path);selected.add(path.with_name(path.stem+'_meta.json'))
    members={str(p.relative_to(ROOT)):p.read_bytes() for p in sorted(selected)}
    members['START_HERE.md']=('''# M1公司行動與逐日資金帳 0.1

這是獨立研究／會計證據小包，非完整歷史專案。保留原專案，解壓到另一新資料夾。
閱讀 股票系統M1_v0_18/rotation_research/action_data_20261022/README.md、REPORT.md、CONTRACT.md。
包內有來源原件子集及新模組，標準Python可離線重現下列44定向測試及資格核查：

```bash
cd 股票系統M1_v0_18
python3 -m unittest rotation_research.test_action_sources rotation_research.test_action_ledger rotation_research.test_action_integration -v
python3 -m rotation_research.action_study
```

事件五組件不是完整事件清單，70市場窗口全拒算、2不足，總淨報酬合格0。
engineered是工程測試值，不是市場行情。gross-schedule-preview是真實毛額預定時程，不代表淨現金或實際到款。
無新UI、瀏覽器或Android驗收。原P1-7的歷史報告及整個舊庫不在此小包，不可用本包替代完整checkout。
完整專案工程接續仍依GitHub指定分支根AGENTS準備；WORK_HANDOFF有完整指令。
''').encode()
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(members.items())}
    members['ACTION_PACKAGE_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    buf=BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,body in sorted(members.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,body,compresslevel=9)
    body=buf.getvalue();dest=delivery/'m1-actions-ledger-v01-20261022.zip'
    if dest.exists():
        if dest.read_bytes()!=body:raise ValueError('Different existing package preserved: use a new build filename')
    else:dest.write_bytes(body)
    with zipfile.ZipFile(BytesIO(body)) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in manifest.items())
    sha=hashlib.sha256(body).hexdigest()
    (delivery/'SHA256SUMS').write_text(sha+'  '+dest.name+'\n')
    receipt=dict(filename=dest.name,sha256=sha,bytes=len(body),members=len(members),crc='PASS',
                 member_sha256='ALL_PASS',manifest_sha256=hashlib.sha256(members['ACTION_PACKAGE_MANIFEST.json']).hexdigest())
    dump(delivery/'bundle-receipt.json',receipt);print(json.dumps(receipt))


if __name__=='__main__':main()
