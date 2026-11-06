# 開發交接：M1 v0.14 週／月獨立保存與唯讀檢視

先讀 AGENTS.md、README.md、候選規則、週月均線獨立契約、週月保存與唯讀契約、period_persistence/output/週月保存與檢視驗收.md。v0.13 文件另存歷史；不要把舊驗收腳本當本版資料再生指令。

## 已完成及實際驗證

新增 src/period_store_contracts.py、period_store.py、period_store_cli.py、period_viewer.py、period_viewer_template.html；既有 src 全部不改。純數值核心、stock-analysis/1.0、analysis-store/1.0、三個 SQLite 及三份舊 HTML 不變。

period-file-store/1.0 每個正式 JSON 檔即索引，包含完整 request/result、reason、metadata 和內容指紋；支援版本嚴格限定現有 period producer/aggregation/adapter 與固定參數指紋。儲存邊界只驗形狀與身分／前綴／日曆等連結，不重算或認證數學；保存後同 ID 不同內容（含理由）拒絕，完全相同去重。沒有遠端服務或可改註解。

提交為同目錄 temp fsync→排他 hard link→目錄 fsync；link 前失敗 NOT_SAVED、link 後不確定 UNKNOWN、確定完成 COMMITTED。程序中斷殘留 .pending-* 只列診斷不自動清除，正式檔完整可讀。單一檔案提交不用 SQLite 式 recovery；禁止重新建庫掩蓋錯誤。先初始化再並行匯入，本機 POSIX hard link/fsync 原型，無斷電／遠端共享碟／跨平台保證。

公開 PeriodStore load/list/lookup/diagnostics 與 exporter 嚴格唯讀；測試阻擋所有相關核心 module 的 import 仍能讀／匯出，庫檔內容不變。LOOKUP 精確要求股票／市場／模式／as_of，可再選版本／參數／來源，回全部匹配，不選最新。未知版本拒絕。CLI period-store-command/1.0 有 IMPORT／READ／LIST／LOOKUP，沒有計算。回覆輸出失敗會保留 COMMITTED 與 analysis_id 以便讀回；庫內檔、輸入、symlink、硬連結輸出碰撞被阻擋。

period_persistence/run_acceptance.py 實際使用 6 份既有 9 月底結果，另透過 6 個 period_jobs CLI 明確 RUN 8 月底前綴，共保存 12 份。每份再匯入一次去重、獨立 CLI 重開讀回完整 request/result 相同。保留保存庫、命令範本、12 份完整讀回、六份歷史 RUN 結果、比對指紋與 42 個工作子程序紀錄。這不是 1490 份歷史完整內容庫；v0.13 的 1490 快照指紋仍僅工程索引。

新離線頁週月保存結果瀏覽.html 完整嵌入 12 個保存紀錄。先明選股票／市場、模式、版本、as_of、保存身分；切換清除舊值，無自動最新日或 fallback。最新表並列 elapsed/candidate，期間與最後價格日獨立。週月圖使用保存的 close／SMA；表格保留精確字串及空值理由、日曆／量能限制。完整 JSON 下載與 Python 讀回相同。頁面沒有計算、持久化快取或網路。

208 項 Python（新增 20）、50 項 Node 模擬（既有 38＋本版 12）、JS 語法、validate_release 實際通過。新增測試包含 6 程序相同內容競寫、4 程序衝突競寫、提交前後程序終止、I/O 與 fsync 錯誤、提交後輸出失敗、錯誤／未知版本、去重、不可覆寫、來源與快照完整指紋、READ 不 import 核心。多版本 UI 測試使用明示 synthetic fixture，真實 producer 仍只有一版，沒有偽造真實新版結果。

Node 執行實際 inline JS 與完整實算紀錄，但 DOM/canvas 是替身；原環境 Chromium 不可用，沒有把模擬測試算成真實瀏覽器／手機驗收。本版未下載或重試安裝瀏覽器。不能聲稱 Android 下載、排版或觸控已完成。

## 下一階段：獨立 period workflow，沿用本版公開介面

目的：用一個明確背景命令完成 RUN→保存→指定讀回，避免操作端手動拼接既有兩個 CLI。保持新薄接入在引擎之外，不用 UI 框架、SQL 或網路。

1. 新的獨立 workflow schema 與入口（例如 period_workflow.py / period_workflow_cli.py）；RUN 使用原 stock-period-analysis/1.0，呼叫 period_jobs 一次，再呼叫 PeriodStore.save。IMPORT／READ 舊 CLI 持續相容，period-analysis-result/1.0 不改。
2. READ／LOOKUP 路徑不 import period_jobs 或 period_ma；不要在 module 頂層 import 核心。所有保存／回覆／匯出錯誤保留 NOT_SAVED／UNKNOWN／COMMITTED、analysis_id；不要在 READ 上補算。
3. RUN 重試要固定 request/result/理由；同內容去重，衝突保留。每次 as_of 為日終；當日來源假設已收盤，不能改成即時／盤中語意。不要默默選最新版本或日。
4. 至少驗證原 12 份真實保存結果與 workflow 結果一致、只 RUN 計算、重試去重、中斷／輸出失敗可讀回、舊契約／引擎／庫／頁不變。可在新的驗收庫執行，保留本版 12 份庫不變。
5. 保留離線頁獨立匯出；真實手機／瀏覽器 QA 待可用環境補做。跨日／週／月共用 schema 或資料庫不是本階段範圍；若要做，先提出具體版本與相容方案，由使用者決定重大架構。

實際命令見 README、period_persistence/commands 與 output/v0_14_checks.json。封裝後抽取驗收見 output/M1_v0_14_封裝驗證.json。原始碼、完整資料、錯誤語意、驗收與交接齊備。下一步仍繼續工作模式；外部 Codex repo／環境尚未接入驗證，不讓非工程師使用者承擔設定工作。

326 筆仍 UNREVIEWED；classification_quality NOT_VALIDATED、action_qualification NOT_EVALUATED。沒有策略批准、正式交易或績效。不部署／發布／付費／發訊息／交易／開子代理，不重試被拒絕的 TWSE 端點，不升級公司行動證據認證。
