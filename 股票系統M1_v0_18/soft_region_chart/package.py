"""Package a new self-contained HTML and unchanged review; verify ZIP bytes/CRC."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from soft_region_chart.build import NAME, PARENT_SHA256
from region_chart.regions import ROOT, FILES
from product_candidate.build import publish_immutable

ZIP_NAME = 'M1_v019_soft_regions_v041.zip'
README = """股票系統M1：K線淡底色主圖0.4.1

解壓後開 M1_v0_19_soft_regions_v041.html。
標頭「M1 K線淡底色主圖 0.4.1」。
1101／Raw新官方日線／分析2026-10-16、日收27.30、24月486根。

本版只改樣式：移除價量區域的周邊框線，改3%透明背景色。
G2原日期1/16～8/16及136筆真實影線35.90～40.25不變。
量圖底色獨立，只涵蓋同段真實量柱範圍；MACD不染色。
原G1／G2關卡虛線、來源圓點、點價標籤仍保留；它們不是區域邊框。
G1九月近似起緣用漸淡表示，精確起日仍未定；C後終點未知，不補封閉區域。
放大平移只裁切原範圍，不依可見K線重算或假貼邊，不改分析日。

35.90～40.25只是顯示外包，不是正式壓力區界、分價成交或套牢持股。
整區量／量口徑、增量、自動分區選關、強度衰減與生命階段仍未知。
原引擎／策略／庫／歷史／數值及0.4舊頁完整保留。
主要JSON契約仍manual-region-chart-selection/0.2，view_version為0.4.1，原值不變。
新版Android NOT_TESTED_NEW_BUILD；先前HTTP測試與截圖不等於手機開檔／用途認可。
Raw公司行動／五年Adjusted／歷史公布可得、原資料缺口／SQLite根因限制保持。
已知file://政策阻擋不重試／繞過，不要求停用保護。
非即時行情、非交易指令，不代表核心用途已驗證。
本包自足、不需CDN；原案例保留原位元組，不回寫歷史NOT_IMPLEMENTED。
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    files = {NAME: Path(args.html).read_bytes(), 'README.txt': README.encode()}
    for key, relative in FILES.items():
        files['cases/' + key + '.json'] = (ROOT.parent / relative).read_bytes()
    files['SHA256SUMS.txt'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in files.items()).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in files.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compresslevel=9)
    blob = buffer.getvalue()
    checks = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        if archive.testzip() is not None or archive.namelist() != list(files):
            raise ValueError('ZIP CRC or membership mismatch')
        for name, expected in files.items():
            actual = archive.read(name)
            if actual != expected:
                raise ValueError('Extracted bytes differ: ' + name)
            checks[name] = dict(bytes=len(actual), sha256=hashlib.sha256(actual).hexdigest())
    digest = hashlib.sha256(blob).hexdigest()
    report = dict(status='PASS',zip=ZIP_NAME,bytes=len(blob),sha256=digest,crc='PASS',
                  exact_extracted_bytes=True,frozen_0_4_parent_sha256=PARENT_SHA256,members=checks,physical_android='NOT_TESTED_NEW_BUILD')
    for name, content in {ZIP_NAME: blob, 'SHA256SUMS.txt': (digest + '  ' + ZIP_NAME + '\n').encode(),
                          'PACKAGE_VERIFICATION.json': json.dumps(report,ensure_ascii=False,indent=2).encode()}.items():
        print(name, publish_immutable(out / name, content), flush=True)
    print(json.dumps(dict(bytes=len(blob),sha256=digest),ensure_ascii=False))


if __name__ == '__main__':
    main()
