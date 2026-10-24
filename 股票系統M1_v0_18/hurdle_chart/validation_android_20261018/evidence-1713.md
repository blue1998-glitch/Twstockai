# 17:13 G3五日證據與新版下載JSON核對（2026-10-18）

本次收到一張直向PNG與一份新版頁面原JSON，沒有新增口頭操作／效能回報。裝置資料沿16:19使用者自報Pixel9Pro／手機Google瀏覽器／Android稱最新版本；確切版號仍未提供。新版Android整體維持 **PARTIAL_EVIDENCE_OBSERVED**，不能因單一下載通過而宣稱全項驗收或核心用途認可。

## OBSERVED：直接圖面

- 標頭M1三關主圖0.1，1101／Raw｜新官方日線、10/16收27.30，原①④已過與後續人工三關摘要保留。
- 「G3人工關卡來源」證據窗已呈現，五列來源日2021-10-18、2022-03-29、2022-03-31、2022-04-06、2022-04-07，原始高價全部50.20，每列定位按鈕可見。
- 說明「顯示錨2021-10-18只是定位起點，不是使用者唯一選日；五個原始K線全部保留」清楚可見。
- 「返回近期24月（不改分析日）」按鈕可見；「來源指紋／長ID」「人工案例與原始OHLCV JSON」為折疊狀態。這證明其可見狀態，不證明每一列定位、返回或折疊展開已被實際點擊驗證。
- 本圖未收橫向主圖，證據窗遮住主圖；不能確認已返回近期486根、價格軸、K量MACD游標或旋轉保留。證據上段日期／點價關係／回溯資格摘要沒有完整收進圖，不因其未可見便判定不存在。

## FILE_VERIFIED：實際原檔完整比對

原檔 `M1_1101_RAW_CANDIDATE_2026-10-16 (1).json` 1,185,454 bytes，SHA256 **369947bad71ab3fdff894c21511ebf242e1ddb12b59822d02ed93f0580bd2796**。

本輪對SHA已核實的固定交付HTML（87ec609e，SHA2564cbe923936f9841652e7a303ec60029f9159dffe3b266e468d04b573f060706c）解碼，從已讀指定提交8b99c715的producer source AST提取unpack／history_selection／pressure selection／hurdle selection函式，取得相同新1101Raw／10/16選擇，與原上傳JSON **全部解析欄位完全相等**。不是只看檔名、schema或少數欄位；不是原檔排版bytes與producer bytes相等的宣稱，也不是獨立重抓行情／重算指標。

已驗：
- hurdle-chart-selection/0.1、hurdle-chart-view/0.1；new_history_analysis1213根，2021-10-18～2026-10-16；最後OHLC27.10／27.70／26.95／27.30、量57,437,884股。全部供應K不晚於分析日。
- 均線5／20／60／130／260各1213筆、MACD1213筆，連同完整數值字串與小數精度一起比對相等；saved_analysis與retrospective_review為null，原retrospective_followup完整保留。
- manual_hurdles非null，三關順序G1／G2／G3及35.50／40.25／50.20相符，當前原價收盤關係皆BELOW；每個source_indices對回原始OHLCV相符。
- G3.reference.source_date=null，五個matching_source_dates與截圖完全一致。沒有替使用者選唯一日。
- source_id、frame_id、chart_base、data_prefix與analysis一致；另獨立重算bars canonical fingerprint等於data_prefix，案例原bytes SHA等於review_file_sha256，原JSON案例與manual_hurdles.review相等。
- 原review內product_integration=NOT_IMPLEMENTED確為原時點歷史；新wrapper integration_status=EXACT_MANUAL_CASE_DISPLAY_ONLY，兩者各自保留，不誤判未接入，不回寫舊檔。original_phone_export_sha256是舊來源證據指紋，不冒充此次新JSON原檔SHA。
- 區界／區間量／增量／自動選關等原null保留；classification NOT_VALIDATED／action NOT_EVALUATED與Raw未完整校正資格保留。
- 交付bundle人工層非null數量1，這只是已存層的數量檢查，沒有重算全6344時點或重跑365／208。

## 原始證據保存及重現

原PNG `01-Screenshot_20261018-171319.png` 147,997 bytes，SHA256 **e3f8ce94f68fee3dcd9487d998ab8f3aa17ae4bd646c59588d3a21ecfc45ba34**。本輪成功讀圖，不把附件缺檔字句當頁面故障。

`android-original-evidence-1713.zip` 保存這次原PNG及原JSON，解壓後逐檔bytes與上傳原檔相等；ZIP306,378 bytes，SHA256 **8c0915dda5d4827a7b5adf54a543229ad35bd861314394a83b196c9372c27aae**。僅為驗收證據包，不是成品包，沒有拿舊ZIP替代新頁。

機器紀錄：android-export-verification-1713.json；可重現腳本verify_android_export.py。同目錄腳本在獨立副本執行，傳 --html 固定交付HTML、--export 解壓的原JSON、--screenshot 解壓的原PNG、--source-root 指定提交的股票系統M1_v0_18、--case-zip 固定成品小ZIP、--output 獨立暫存報告路徑。腳本只提取選擇函式，不執行build／資料庫／策略；source函式檔SHA及所用提交保存於機器報告。原檔不修改。

## 未測與下一步

新版橫向24月近期主圖仍待一張。下一步同對話Work：關閉證據→24月→專注主圖→橫向截圖，確認2024-10-16～2026-10-16／486根、分析10/16、原已過與後續關卡／超軸提示清楚。這輪已核對JSON，不要求重下載相同檔。

G1／G2實際定位前後與返回、回近期60根、G3五列逐一定位、圖點、平移縮放、K量MACD游標移動、旋轉保留、切10/15及其他股／來源不套、核心用途皆按尚缺證據列，不能拿本圖／JSON代填。原365／208與file://政策阻礙報告、Raw／公司行動／完整歷史／資料缺口及SQLite根因限制保留。本輪無新口頭成功回報、產品修改、新Android代操作或瀏覽器測試，原引擎策略／庫／歷史／main不改。
