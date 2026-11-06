# 開發交接：M1 v0.12 成交量來源修正

先讀 AGENTS.md、README.md、候選規則、docs/成交量來源與版本相容契約.md、volume_revision/output/成交量來源修正驗收.md。前版交接保留為 docs/CODEX交接_v0.11_歷史.md。

## 實際完成與證據

structure-0.3-research 在公開 analyze 要求明確 volume_unit，jobs 從已要求的 source.volume_unit 傳入；SHARES_REPORTED 證據寫原生股數，SHARES_SCALED_FROM_LOTS 保持原文。沒有重新縮放數值。根結構與 snapshot 保存單位，snapshot_id 加入單位；版本衍生的 ledger／aligned／analysis 身分相應更新。Config、參數指紋、數值演算法及 daily_ma 不變。直接 Python 呼叫缺單位回 typed error，舊 JSON 工作單不用改。

store_contracts 新增新版本單位欄位一致性驗證；舊 0.2 讀取不補欄、不改文字。分析引擎仍沒有 UI、SQL、workflow 依賴；原測試內的直接 analyze 呼叫加上明確 fixture 單位。analysis_jobs 只更新說明文字，接入器行為及版本不變。

volume_revision/run_acceptance.py：將已關閉 v0.10 庫複製至新獨立庫，保留三份完整舊 bundle，透過 13 個 workflow CLI 工作程序操作新增三版、分開 READ 舊新、LOOKUP 列出兩版及重跑 EXISTING。額外計算 6488 Raw／Adjusted；五組共 1311 快照。compare.py 僅允許證據文字／新增單位／版本衍生身分改變，其他候選 ID、數值、日期、狀態、來源、參數、品質與全部 MA 均全等。這不是歷史績效或分類品質測試。

新庫 volume_revision/output/單位修正並存_v0_12.sqlite3：六分析／六紀錄／13 去重物件／1490 日期索引。兩歷史庫與舊 HTML 等 40 份既有檔案逐位元組不變。未修改原始公司行動證據或重新抓資料。

saved_viewer/run_acceptance.py 預設新庫、新 HTML、新報告，避免改舊產物；可傳原有參數。六份完整 bundle 全等 load，18 次首／中／末 snapshot 全等。tests/test_volume_version_viewer.cjs 執行新頁 inline JS，1490 個快照指紋全相同，實際新舊版選取不依賴虛構版本 fixture。舊頁仍獨立跑原測試。新版 UI 對歷史原生股數錯誤保留警示，對修正版顯示正確說明；根／快照單位不符即清空並停用下載。原始資料 JSON 原文不在前端改寫。

156 項 Python（新增 9 項單位／身分／歷史保存保護）、10 項新版本頁面、15 項前版唯讀頁、13 項舊重播頁模擬檢查、JS 語法與 validate_release 全通過。實際命令、退出碼、log 見 output/v0_12_checks.json。Node doubles 不驗證 CSS／觸控／真實下載。本版真實瀏覽器未執行，前版環境缺少 Chromium executable；不能把前版 BLOCKED 或本版模擬座標當瀏覽器成功。新 HTML 約 48 MB，Android 記憶體與載入時間未測。

workflow/run_acceptance.py 與 persistence/run_acceptance.py 是舊 producer 驗收程式，現加版本閘門；遇 0.3 在任何寫入前退出 2。這是已測的防誤覆寫，不是當前功能失敗。當前命令改用 volume_revision/run_acceptance.py；舊資料及報告保留而不偽造重跑成功。

## 下一個合理階段：獨立週／月均線核心

使用者已確認時間尺度：日 5/20/60/130/260、週 4/13/26/52、月 3/6/12/24。日核心已存在。下一步先寫可在沒有 UI／SQL／網路時執行的週月資料聚合與 SMA，固定獨立輸入／輸出；不要直接修改 stock-analysis/1.0，其保存驗證目前只允許 structure 與 daily_ma 兩元件。整合成新增 unified components 需另規劃明確新版契約，不默默擴充。

- 以已提供、通過日線驗證的資料分組；週界線與月界線明確保存，不能把 20 日均線冒充月均線。OHLC 使用第一開、最高、最低、最後收；不得猜日內順序。
- 成交量保留明確來源單位；缺值與零分開，不默認補零。聚合完整度及未提供的交易日曆限制可見，不能由「週五有資料」推論完整市場交易日曆已核實。
- 未走完的本週／本月必須明示期間尚未結束；候選與完整期間分開，不能只因資料是收盤日線便把整個週／月標確認。快照只用 as_of 前資料，未來日線不得改早期結果。
- 沿用 Raw／Adjusted 分離及各快照錨定日；除息因子只能套用當時已生效事件。不可拿期末調整價回填早期週月判斷，也不要讓週月聚合自己做來源認證。
- SMA 完整窗才給數字，不足即 null。既有約 14 個月的樣本不足 24 月，應如實顯示；先以明確 synthetic fixtures 覆蓋長窗與跨年／跨月邊界，再用真實現有資料驗證，不必為湊數偽造行情。
- 驗證期間邊界、未完期間、缺失成交量、前綴穩定性、Raw／Adjusted 跨公司行動、Decimal 精度、無 UI／SQL 依賴；保持現有日線結果、資料庫、HTML、分類品質及交易資格不變。

週月核心是補齊既有規格，不新增交易條件或綜合分數。之後才安排顯示、保存格式新版及分類驗收。

## 模式與邊界

繼續工作模式；Codex 接手用原始碼、資料、測試及完整命令均在包內，但外部專案環境尚未接入驗證。每次結尾說明工作模式或 Codex。

326 筆歷史覆核仍 UNREVIEWED；本版新輸出沒有被人工核准。分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。不發布、部署、付費、交易、發訊息、啟動子代理，不重試或繞過已拒絕 TWSE 除權息介面；公司行動 staging 不自動升級。
