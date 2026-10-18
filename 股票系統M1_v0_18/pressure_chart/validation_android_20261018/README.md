# Android原始證據與單檔核對

來源：本對話使用者提供的14:08直向PNG及同股／同分析日原JSON。這是證據包，不是成品下載包。成品仍使用指定分支的deliveries/m1-v019-pressure-walls-20261018/README.md。

- `android-original-evidence-20261018-1408.zip` 保存原PNG／JSON，解壓逐檔與原上傳bytes相等。ZIP bytes327243，SHA256 `e3927abe0aa2ce9406df3a1a34e6852b2ada34c306339cce8c392635a92e6025`。
- `phone-export-verification.json` 記錄原檔SHA、成品SHA、單檔比對範圍、OHLCV及未測項目。
- `verify_phone.py` 使用固定producer函式及HTML內實際資料比較完整解析JSON。只提取unpack／selection／history_selection，不執行build、網路、資料庫或策略。不是來源重新抓取、指標獨立重算或瀏覽器測試。

重現：使用包含產品的指定分支／已核實3942950提交，下載固定小ZIP並解出HTML；將本證據ZIP解壓至獨立資料夾。對腳本傳入 `--html <解出的HTML> --evidence-dir <證據資料夾> --source-root <該提交的股票系統M1_v0_18目錄>`。腳本在自身資料夾寫核對報告；驗證用副本執行即可。HTML SHA固定驗證，來源為394的producer。與產品基準b9相同，當次branch後續只有補證／交接。

完整JSON解析值完全相同，沒有宣稱兩種JSON排版的原bytes相同。原JSON具保存指紋。可證明這個已提供檔的內容，不能推斷未見的下載流程、其他股票／日期或所有Android功能通過。

Android整體 PARTIAL_EVIDENCE_OBSERVED。截圖支持直向本機content開檔後已渲染五年窗；同截止日游標靜態位置可見，但未測移動同步。沒有機型／版本／載入耗時資料。本次沒有新的逐項口頭操作回報。後續看根目錄M1_V019_PRESSURE_CHART_ANDROID_ACCEPTANCE.md最新節。

核心限制仍未改：來源月份不是整理區；Raw高不是完整校正壓力；沒有完整歷史新高保證、正式生命階段、自動魔王、區界或增量門檻。六個日期的TWSE補證與TPEx未決沿用既有獨立紀錄。
