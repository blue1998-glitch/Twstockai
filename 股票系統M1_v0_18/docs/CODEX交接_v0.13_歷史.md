# 開發交接：M1 v0.13 獨立週／月核心

先讀 AGENTS.md、README.md、候選規則、docs/週月均線獨立契約.md、period_analysis/output/週月均線核心驗收.md。v0.12 交接保留為歷史檔。

## 已實際完成

src/period_ma.py 只依標準庫、既有 contracts 與 structure 的價格投影／單位驗證原語。公開 analyze_period_ma 明確要求 code、exchange、source_id、volume_unit、mode、as_of，calendar 可選。新 schema period-ma/1.0、producer period-sma-0.1-research、aggregation period-bars-0.1。週採 ISO 週，月採西曆；各期 OHLC 及成交量依實際日線聚合，再算固定 SMA 週 4/13/26/52、月 3/6/12/24。

elapsed 與 candidate 分開，calendar_state 不等於市場資料認證。未知空期間、左邊界不足、提供日曆不符會斷窗；只有完整覆蓋且宣告無交易日的已走完期間可跳過，不造 close。窗口依有效有價期間計數，跳過有日曆依據的整週休市不等於補一根 K 線。部分成交量總和另存，完整總量缺值不補 0。詳見契約與 point_status。

核心每次以 as_of 前綴、當時已生效事件投影整段日線，再聚合。Decimal 局部 Context 固定，精確累加後 28 位 HALF_EVEN，沒有呼叫者精度或 trap 依賴。snapshot ID 含市場、來源、單位、模式、截至當日資料／事件／日曆／參數指紋與版本。沒有新轉折／型態或交易規則。

src/period_jobs.py 是獨立 JSON 契約 stock-period-analysis/1.0 -> period-analysis-result/1.0，adapter period-job-0.1。未 import 舊 jobs／analysis_jobs 或資料層；根欄位固定、防 typo，來源／市場／單位驗證，重複 JSON key 拒絕，原子輸出與輸入別名保護。整份 request 指紋可因未來價格改變，但較早 snapshot 必須完全相同。

period_analysis/run_acceptance.py 取既有 8069／6488 兩模式及 1101／2884 Raw，重用既有計畫日曆與個案休市證據，均保留非完整認證限制。每個提供日線日都重跑完整來源與截斷前綴，1490 快照完全相同；改未來價格、事件與日曆後，中期快照不變。另以獨立日期分組、OHLC 極值與 Fraction 精確分數算術核對 52894 有價格列和 430352 曲線位置。日價投影原語共用既有未改程式，並由合成已知數字測試跨除息邊界，不能把這當第二套完整還原認證。

六個真正 CLI 子程序的結果與函式相同，六份最新完整 JSON 及工作單保留；逐日指紋 JSONL 僅是工程核對索引，沒有宣稱已保存全部歷史內容的服務。所有真實樣本 24 月均不足，保留 null；長達 26 月的明示合成序列已驗證 24 月與 52 週窗口，合成資料沒有當真實行情交付。

188 項 Python（新增 25 核心與 7 接入器／CLI 測試）、38 項舊頁 Node 模擬、JS 語法、validate_release 通過。418 份既有檔案不變，含全部既有 src、三資料庫與各 HTML。命令與退出碼見 output/v0_13_checks.json。新核心沒有 UI；本版未做真實瀏覽器／手機驗收，也不把既有模擬頁面成功當週月 UI 成功。

## 下一階段：獨立保存與唯讀接入

現有 stock-analysis/1.0 及 analysis-store/1.0 僅支援 structure、daily_ma；請勿直接塞進第三元件或改舊表格。先沿用 period-analysis-result/1.0 建一個外部薄接入：

1. 提供明確 save／load／list／指定 as_of 讀回，計算只由 RUN 觸發，讀回／展示不重新計算。可先採獨立不可覆寫 JSON 物件與索引目錄，與現有數值引擎／SQLite 庫分離，仍屬獨立資料層而不是網頁快取。
2. 保存完整 request／result、來源與日曆範圍、rule／aggregation／adapter 版本、價格模式、as_of、最後實際價格日、變更理由與指紋。相同內容去重；同身分不同內容拒絕，錯誤不得改寫舊結果或重建資料庫。
3. 新讀取介面以股票／市場／模式／as_of／版本定位；多版本列出選擇、不擅選最新。elapsed 與 candidate、period_end 與 last_price_date、null 原因必須看得見，不混不同錨定日曲線。
4. 用既有六個完整結果實跑保存／重開／讀回、重複匯入、錯誤內容／版本、並行寫入及輸出失敗，確認舊三庫／HTML 與日線數值不變。再做只呈現保存資料的薄頁面，先不發布。
5. 若需要把日／週／月一起納入共用資料庫或改現有統一結果契約，先完成具體新版欄位與舊資料相容方案；不要自動 migration。不要引入 UI／SQL／網路到核心。

原始碼、資料、測試與命令齊備；繼續工作模式較合適，外部 Codex 專案仍未接入驗證。每次結尾都須指明模式。

326 筆覆核未審、新週月數值未做分類品質或交易價值驗證；分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。不部署、發布、付費、交易、發訊息或啟動子代理。不重試／繞過已拒絕 TWSE 除權息介面，不升級公司行動 staging。
