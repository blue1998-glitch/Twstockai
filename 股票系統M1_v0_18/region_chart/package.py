"""Package a new self-contained HTML and unchanged review; verify ZIP bytes/CRC."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from region_chart.build import NAME, PARENT_SHA256
from region_chart.regions import ROOT, FILES
from product_candidate.build import publish_immutable

ZIP_NAME = 'M1_v019_manual_regions_v03.zip'
README = """股票系統M1：人工價量時間區域主圖0.3

解壓後開 M1_v0_19_manual_regions_v03.html，標頭應為「M1 價量區域主圖0.3」。
1101／Raw｜新官方日線／2026-10-16，日收27.30，預設24月486根。
約五年有1213根真實日K；K線、成交量、MACD共用時間軸及游標。
本包使用既有保存資料，不連網抓行情，不是即時股價。

G2精確時間帶2023-01-16～2023-08-16，代表點5/2高40.25不變。
G1大約2023年9月→C(2024-01-19低31.80)；九月斜線起緣不是已定起日。
C後新平緩帶只有向右開放參照，精確終點未定；不把所有後續K線自動分類。
按G1／G2／C後按鈕聚焦，按「區域證據」看來源；24月回近期視窗。
代表點G1／G2／G3與原①④收在折疊列；價格軸內線標籤仍可見。
G2／G3超軸仍只提示，不為50.20壓扁近期K線。

預設「拖曳查詢」只移游標；要移圖，明選「單指移圖／雙指縮放」。
可用＋／−、18月／24月／約5年、左右按鈕移圖，分析日不隨瀏覽改變。
主圖下方查詢交易日期與前後鍵只讀真實交易列，顯示完整OHLCV。
「以游標日回看分析」才會變更分析日；本例人工層只綁指定來源／10/16。
草稿在「選點草稿」記起／終點，下載獨立JSON；尚未提交、不會更新案例。
草稿只在記憶體，重開、換來源／分析日會清空；反向選點不擅自交換。
主分析JSON保留原精度、來源、人工原案及指紋，與草稿下載分開。

時間帶不是價格上下界；整區量、量口徑、自動分區、強度衰減等仍未定。
來源日量不等於整帶成交量／尚未解套股數；不能由日OHLCV精確分價。
2026-10-18人工回溯覆核不是10/16當時自動訊號；不是核心用途認可。
Raw完整公司行動、五年Adjusted與歷史公布可得未驗證；五年高不是全史高。
來源及策略限制、SQLite未知根因保留，不是交易指令。

雲端真實Chromium HTTP測試另見GitHub本版驗收報告；不是Android實機。
本版Android：NOT_TESTED_NEW_BUILD。舊0.2部分證據保留，不重索相同舊檔。
已知file://管理政策拒絕未重試／未繞過；手機開檔失敗請記具體錯誤，勿停用保護。
同包cases原JSON內接入狀態是歷史記錄；本版manual_regions wrapper記新版接入。
SHA256SUMS.txt可核對解壓後檔案；外部同名清單核對ZIP本身。
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
                  exact_extracted_bytes=True,frozen_0_2_parent_sha256=PARENT_SHA256,members=checks,physical_android='NOT_TESTED_NEW_BUILD')
    for name, content in {ZIP_NAME: blob, 'SHA256SUMS.txt': (digest + '  ' + ZIP_NAME + '\n').encode(),
                          'PACKAGE_VERIFICATION.json': json.dumps(report,ensure_ascii=False,indent=2).encode()}.items():
        print(name, publish_immutable(out / name, content), flush=True)
    print(json.dumps(dict(bytes=len(blob),sha256=digest),ensure_ascii=False))


if __name__ == '__main__':
    main()
