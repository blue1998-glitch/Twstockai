"""Package a new self-contained HTML and unchanged review; verify ZIP bytes/CRC."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from hurdle_chart.build import CASE, NAME
from product_candidate.build import publish_immutable

ZIP_NAME = 'M1_v019_three_hurdles_labels_v02.zip'
README = '''股票系統M1：人工三關主圖0.2

解壓後用瀏覽器開 M1_v0_19_three_hurdles_labels_v02.html，不需要安裝程式或連網取行情。
標頭應為「M1 三關主圖0.2」，1101／Raw｜新官方日線／2026-10-16，日收27.30、24月486根。
原①26.10與④26.85已過點價；G1 35.50、G2 40.25、G3 50.20是本例後續人工關卡。

點關卡標題讀證據；點定位來源只移圖，不改10/16分析日。按24月回近期24月；「回近期」是60根。
G3未指定唯一日，五個同價來源都可在證據表定位；顯示錨不是唯一使用者選日。
超出價格軸的關卡保留提示，不強拉價軸；Raw公司行動未完整核實，非校正後共同基底壓力認證。
10/18後來人工覆核不是當時自動訊號，只適用指定1101來源／基底／10/16。
區界、整區量、增量、強度、衰減、自動選關與生命階段未定；不是交易指令或全市場辨識完成。

新版Android尚未實測，不能沿用舊頁部分驗收。雲端Chromium HTTP實測通過；原file://開檔遭管理政策拒絕，本次未重試或繞過。
手機若無法開啟，記下機型／瀏覽器／開檔方式與具體錯誤，不要求停用保護。
本次只修主圖線標籤；請回Work先核對來源畫外時的G1 35.50及不遮刻度／縮放鈕。
舊0.1版原圖與JSON已核對，不重要求相同檔；修正版另記未驗，新增證據須註明0.2版。

同包人工案例JSON為原覆核檔，原NOT_IMPLEMENTED是當時歷史；新版下載manual_hurdles wrapper另有接入狀態。
SHA256SUMS.txt核對本包原始檔；ZIP本身SHA見GitHub下載入口外部清單。
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    files = {NAME: Path(args.html).read_bytes(), CASE.name: CASE.read_bytes(), 'README.txt': README.encode()}
    files['SHA256SUMS.txt'] = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in files.items()).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in files.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 18, 0, 0, 0))
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
                  exact_extracted_bytes=True,members=checks,physical_android='NOT_TESTED_NEW_BUILD')
    for name, content in {ZIP_NAME: blob, 'SHA256SUMS.txt': (digest + '  ' + ZIP_NAME + '\n').encode(),
                          'PACKAGE_VERIFICATION.json': json.dumps(report,ensure_ascii=False,indent=2).encode()}.items():
        print(name, publish_immutable(out / name, content), flush=True)
    print(json.dumps(dict(bytes=len(blob),sha256=digest),ensure_ascii=False))


if __name__ == '__main__':
    main()
