"""Package exact shipped research artifacts; immutable files and real ZIP CRC."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
from graph_core_chart.build import NAME,ROOT
from product_candidate.build import publish_immutable
ZIP_NAME='M1_v019_graph_recognition_v01.zip'
README='''M1 圖形辨識研究主圖0.1

解壓後開 M1_v019_graph_recognition_v01.html，無CDN或網路行情相依。
標頭「M1 圖形辨識研究主圖 0.1」，1101／Raw／2026-10-16已存收盤27.30，非即時今日。
研究箱由獨立Python核心自動產生，不把人工G1／G2或已答日期寫成演算法答案。
四股約五年真實日OHLCV全部保留，K／量／MACD同步、可放大平移及查詢。
「已算分析日」回放的是每120筆樣本與最近5交易日，並非已計算全部歷史日辨識。
價格／交易日查詢不抽樣，不補休市K，不在UI補算數值核心。

預設拖曳查詢只移游標；選「移圖／雙指縮放」才平移。＋−縮放、約五年／24月／近期可返回。
研究箱選單→聚焦來源或數值與反證，可看首次可知時間、研究價界、量口徑、下跌與失敗路徑。
勾選候選只改顯示，不批准策略；虛線是參照延伸，不代表後續全屬同箱。
主要JSON下載保留完整原值、source／frame／basis／prefix、核心版本／設定與反證。
人工覆核另作後來對照，不輸入核心，不是辨識準確率。

反轉3%／6%／12%及高低群35%是未批准研究設定。不同設定會改變候選。
正式區界、重要性／衰減／量增／量口徑／生命階段仍未定，唯一主壓力保留null。
瀏覽器工程檢查不是策略／Android或辨識品質認可；實際數字與失敗見GitHub報告。
原人工39筆前箱本版沒有精確同區間自動匹配；較大月份主帶未完整重現，不能稱核心用途完成。
量總和／均量／最高柱為研究選段描述，不是精確分價或剩餘持股。沉澱判斷仍未知。
Raw完整公司行動／五年Adjusted／歷史公布可得／原資料缺口及SQLite未知根因保持。
沒有訓練圖片模型、沒有重新讀101圖、沒有交易資格或全市場準確率。

Android NOT_TESTED_NEW_BUILD；原file://管理政策阻礙不重試／不繞過／不要求停用保護。
原0.4.3樣式驗收已收束，不重問舊圖／JSON；本版是獨立新核心功能，不覆寫舊頁。
手機若無法開啟請記方式與錯誤；只用真的新圖或操作回報記OBSERVED／USER_REPORTED。
內含四股latest完整核心JSON及recognition-audit描述報告，後者不是accuracy／回測績效。
SHA256SUMS.txt核對成員；ZIP本身SHA見GitHub外部清單。完整source／測試／交接沿指定dev分支。
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifact-dir',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args();folder=Path(a.artifact_dir);out=Path(a.output_dir)
    files={NAME:(folder/NAME).read_bytes(),'README.txt':README.encode(),'RESEARCH_README.txt':(ROOT/'graph_core/README.md').read_bytes()}
    for name in ['core-1101-latest.json','core-2884-latest.json','core-6488-latest.json','core-8069-latest.json','recognition-audit.json']:files[name]=(folder/name).read_bytes()
    files['SHA256SUMS.txt']=''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n' for name,raw in files.items()).encode();buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,raw in files.items():
            info=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,raw,compresslevel=9)
    blob=buffer.getvalue();members={}
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip() is not None or z.namelist()!=list(files):raise ValueError('ZIP CRC or member mismatch')
        for name,raw in files.items():
            if z.read(name)!=raw:raise ValueError('Extracted byte mismatch')
            members[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    digest=hashlib.sha256(blob).hexdigest();report=dict(status='PASS',zip=ZIP_NAME,bytes=len(blob),sha256=digest,crc='PASS',exact_extracted_bytes=True,members=members,physical_android='NOT_TESTED_NEW_BUILD')
    for name,raw in {ZIP_NAME:blob,'SHA256SUMS.txt':(digest+'  '+ZIP_NAME+'\n').encode(),'PACKAGE_VERIFICATION.json':json.dumps(report,ensure_ascii=False,indent=2).encode()}.items():print(name,publish_immutable(out/name,raw))
    print(json.dumps(dict(bytes=len(blob),sha256=digest)))


if __name__=='__main__':main()
