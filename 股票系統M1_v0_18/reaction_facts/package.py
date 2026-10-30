"""Deterministic data-only deliverable. No replacement HTML or old artifacts."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
from product_candidate.build import publish_immutable
from .verify import verify


def package(data, selection, result, output_dir):
    checked = verify(data, selection, result)
    content = {'comparison-data.json': Path(data).read_bytes(),
               'reference-selection.json': Path(selection).read_bytes(),
               'reaction-facts.json': Path(result).read_bytes(),
               'README.txt': ('M1 多參照反應事實附層 0.1\n'
                              '本包是完整精度JSON資料，不是新版HTML或自動選關。\n'
                              'comparison-data為原真實圖來源與原core；reference-selection為後來明示查詢；reaction-facts為新附層。\n'
                              '參照可知日不代表當時已選關，historical_signal_eligible=false，primary_pressure_id=null。\n'
                              '原圖／引擎／策略／庫／歷史未改；全部策略及來源限制見reaction-facts.limits。\n'
                              'Android NOT_TESTED_NEW_BUILD；本輪無UI或瀏覽器驗收。\n'
                              '完整source、CLI、驗收及續接：repository reaction_facts/README.md與交付README。\n').encode(),
               'SOURCE_PROVENANCE.json': (json.dumps(checked, ensure_ascii=False, indent=2) + '\n').encode()}
    digest = lambda b: hashlib.sha256(b).hexdigest()
    content['SHA256SUMS.txt'] = ''.join(digest(b) + '  ' + n + '\n' for n, b in sorted(content.items())).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, blob in sorted(content.items()):
            member = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o100644 << 16
            z.writestr(member, blob)
    blob = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip() is not None or any(z.read(n) != b for n, b in content.items()):
            raise ValueError('Archive CRC or extracted bytes differ')
    out = Path(output_dir); name = 'M1_v019_reaction_facts_v01.zip'
    report = dict(status='PASS', archive=name, bytes=len(blob), sha256=digest(blob), crc='PASS',
                  members={n:dict(bytes=len(b),sha256=digest(b)) for n,b in sorted(content.items())})
    publish_immutable(out / name, blob)
    publish_immutable(out / 'SHA256SUMS.txt', (digest(blob) + '  ' + name + '\n').encode())
    publish_immutable(out / 'PACKAGE_VERIFICATION.json', (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode())
    return report


def main():
    p = argparse.ArgumentParser()
    for name in ('data', 'selection', 'result', 'output-dir'):
        p.add_argument('--' + name, required=True)
    a = p.parse_args()
    print(json.dumps(package(a.data, a.selection, a.result, a.output_dir), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
