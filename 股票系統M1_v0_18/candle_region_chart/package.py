"""Package a new self-contained HTML and unchanged review; verify ZIP bytes/CRC."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from candle_region_chart.build import NAME, PARENT_SHA256
from region_chart.regions import ROOT, FILES
from product_candidate.build import publish_immutable

ZIP_NAME = 'M1_v019_candle_regions_v04.zip'
README = """股票系統M1：K線範圍價量區域主圖0.4

解壓後開 M1_v0_19_candle_regions_v04.html，標頭「M1 K線範圍區域主圖0.4」。
1101／Raw｜新官方日線／分析2026-10-16，日收27.30，預設24月486根。
本包自足、無CDN、不連網取行情；只有既有保存真實資料，不是即時報價。

按G2價量帶：精確2023-01-16～2023-08-16含136筆真實來源。
價圖細框包所選段影線低35.90／高40.25；原5/2代表點40.25保留。
量圖框獨立只包同段實際量柱；MACD沒有價量區域底色。
35.90～40.25是顯示外包範圍，不是正式壓力上下界、分價成交或套牢持股。
放大平移只裁切原全選段外框，不用可見子窗重新取高低、不為圖框拉伸價軸。

按G1價量帶：大約2023年9月→C(2024-01-19 low31.80)。
九月顯示錨的起緣虛線且左邊未閉合，精確起日／歸屬仍未知。
近似外包使用97筆顯示來源，不將9/1認作正式起日／計量窗。
C後僅開放參照，不將4/26或4/30當終點或自動分類所有後續K線。
原11/28高35.50、9/14同高與10/18、11/30原日量各自保留。
原①26.10／④26.85及G3五個50.20來源不變；軸內標籤、超軸提示保留。

預設拖曳查詢只移游標，明選「單指移圖／雙指縮放」才平移；＋／−可縮放。
24月返回486根，約5年顯示1213根。K／量／MACD共用視窗及游標。
查詢日期及前後鍵讀真實交易記錄／完整OHLCV，跨休市不造K，不變分析日。
只有「以游標日回看分析」明確改日；其他股票／日期／source／frame／basis不套本案。
「選點草稿」可記起終點、複製或下載獨立JSON，尚未提交／批准。
重開或換來源／分析日清空，逆序不交換。主分析JSON含region_display及原人工層／指紋。

正式價格區界、整區量／量口徑、增量、自動分區／選關、強度／衰減及生命階段仍未定。
量框最高柱不是整帶成交量／策略最大量；缺量不造0或假高度。
人工覆核發生2026-10-18，不倒灌成10/16或更早自動訊號；UI修正不代表核心用途認可。
Raw完整公司行動／五年Adjusted／歷史公布可得未核；五年高不是全史高。
原資料缺口／SQLite未知根因保持，非交易指令、非全市場辨識完成。

新版Android NOT_TESTED_NEW_BUILD。雲端Chromium HTTP測試不是手機實機／file開檔通過。
0.3-family兩張舊手機原圖已保存，不重索；原file://管理政策阻擋不重試／繞過。
手機開檔若失敗，記具體機型／瀏覽器／方式／錯誤，不要求停用保護。
回Work只驗新外框呈現差異；0.1／0.2／0.3原成品與證據保留。
同包cases原JSON原樣保存，歷史NOT_IMPLEMENTED不回寫；新顯示層獨立標示。
內部SHA256SUMS核對原檔；ZIP自身SHA見外部清單。測試／前後畫面／遠端收據見GitHub交付入口。
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
                  exact_extracted_bytes=True,frozen_0_3_parent_sha256=PARENT_SHA256,members=checks,physical_android='NOT_TESTED_NEW_BUILD')
    for name, content in {ZIP_NAME: blob, 'SHA256SUMS.txt': (digest + '  ' + ZIP_NAME + '\n').encode(),
                          'PACKAGE_VERIFICATION.json': json.dumps(report,ensure_ascii=False,indent=2).encode()}.items():
        print(name, publish_immutable(out / name, content), flush=True)
    print(json.dumps(dict(bytes=len(blob),sha256=digest),ensure_ascii=False))


if __name__ == '__main__':
    main()
