# 開發交接：M1 v0.15 週／月背景流程

先讀 AGENTS.md、README.md、候選規則、docs/週月均線獨立契約.md、週月保存與唯讀契約.md、週月背景流程契約.md、period_workflow/output/週月背景流程驗收.md。v0.14 主文件保留歷史副本，過去報告是對應舊版的實跑紀錄。

## 已完成與實際驗證

新增 src/period_workflow.py、src/period_workflow_cli.py，沒有改任何既有 src。schema period-workflow/1.0、workflow_version period-workflow-0.1；數值 producer、aggregation、adapter、原 request/result/store schema 與指紋格式不變。

execute_period_workflow(request, store_path, create_if_missing=False) 固定 RUN／READ／LOOKUP。RUN lazy import 原 period_jobs、只呼叫一次核心、沿原保存契約驗結果、明確保存、從正式檔完整讀回核對 request/result/理由，再回 snapshot。沒有從記憶體補回成功。READ／LOOKUP 不 import 引擎、不清 pending、不修復／初始化、不猜鄰日或最新版本；新程序 import blocker 已實證。

RUN 要 job、reason，可選布林 include_bundle；READ 要完整 analysis_id，可選 include_bundle；LOOKUP 要股票／市場／模式／as_of filters，可加原版本／參數／來源／request 指紋。缺少／未知欄位拒絕。LOOKUP 返回全部匹配，含 MULTIPLE_MATCHES，不擅挑一份。EMPTY_INPUT 維持 computation_status，工作流程 COMPLETED 不代表有資料或分類批准。

保存狀態依實際 stage 保留 NOT_SAVED／UNKNOWN／COMMITTED；READ／LOOKUP 為 NOT_APPLICABLE。SAVE 未知例外採 UNKNOWN，有 ID 建議 READ；保存已確認後 READ_BACK／輸出失敗仍 COMMITTED。CLI 輸出完整 JSON，stdout 小收據，錯誤 stderr 版本化 JSON；錯誤不改舊 output。輸入／庫內檔／symlink／硬連結輸出碰撞在計算前阻擋。原 IMPORT worker 完全相容保留。

沒有自動重試；每次明確 RUN（含重試）仍計算一次，保存去重。回覆失敗先 READ/LOOKUP；不要為了查是否保存就補算。只有明確 --create 的 RUN 可初始化；先初始化再並行，沿用原本機 hard link/fsync 限制，沒有多程序同時初始化保證或斷電測試。

period_workflow/run_acceptance.py 用 v0.14 公開唯讀介面讀 12 份完整原工作單，24 個明確 RUN（各兩次）、12 READ、13 LOOKUP 共 49 個獨立 CLI 子程序。第一個 RUN 故意讓保存後輸出失敗，回 COMMITTED，再由另一程序讀回；12 次重試均 DUPLICATE。全部新保存檔案與原週月庫位元組相同，完整 snapshot/result 指紋相同。驗收刻意沿用原理由，沒有偽造新數值版本或提高來源認證；workflow_version 在回覆標記新接入層。

新結果庫 period_workflow/output/背景流程結果庫 與 v0.14 庫分離。命令、錯誤樣本、完整回覆、JSON 驗收報告與日誌均保留。原 exporter 由新庫匯出的頁面 period_workflow/output/週月背景流程結果瀏覽.html 與原頁完全相同；未新增 UI。558 份既有檔案不變（排除明確更新的主文件與主清單），包括三 SQLite、原週月庫、四 HTML、舊程式與測試／報告。

235 Python（新增 27）、50 既有 Node 模擬、JS 語法、validate_release 實際通過。新增流程測試涵蓋真實數值一致、一次計算、重試去重、精確／多筆匹配、僅 RUN 初始化、錯誤結果拒絕、保存前後程序終止、4 程序 RUN 競寫、fsync 未知、非預期保存例外、讀回失敗／不符、保存後輸出失敗、舊 output 保護、標準回覆故障與唯讀不 import 核心。封裝後獨立驗證另見 output/M1_v0_15_封裝驗證.json。

真實瀏覽器／Android 開檔下載／觸控／排版仍 NOT_TESTED。Chromium 原環境不可用，本版沒有重試安裝；Node 替身不能當實機驗收。仍只有四檔、六模式、兩個保存日；不是全市場、排程服務或全部 1490 快照保存庫。

## 下一階段：日／週／月已保存結果唯讀對照

目的：讓使用者同一處查看日線操作資訊、週線輔助與月線背景，先對齊資料事實，不引入跨尺度綜合分數、交易資格或新的分類結論。

1. 新接入放在引擎外，以 AnalysisStore 和 PeriodStore 公開唯讀方法取完整保存結果，不能改原 schema 或 SQLite。日線以明確 record_id、as_of、producer 版本選快照；週月以 analysis_id 選整份同錨定結果。原量能修正版庫在 volume_revision/output/單位修正並存_v0_12.sqlite3；原週月庫與 v0.15 背景庫可選其中明確一個，不自動合併。
2. 先盤點實際可對照的保存紀錄，再檢查 stock/exchange/price_mode/as_of、source_id、volume_unit、截至日資料與有效事件指紋、還原錨定一致性。日線 structure 的 effective_events_fingerprint 與 daily_ma 的 events_fingerprint 欄名不同，需按既有契約讀；不要假設所有 12 週月結果都已有同日同源日線保存資料。
3. 有缺資料、日期／來源／事件／版本不符就明示原因，不選鄰日、不重算、不拼成看似一致的結論。多筆匹配保留人工明選。先做單一明確分析日的研究對照，不把不同 as_of 還原尺度的曲線混在一張價軸。
4. 可新增獨立只讀 view model／離線對照頁，直接呈現各引擎原值、原證據、品質限制與分開的確定程度；READ/export 連核心 import 都不能有。不要默默把三種時間尺度塞到 stock-analysis/1.0，若確實需要共用 schema migration，先準備具體相容提案，重大變更待使用者決定。
5. 實際驗證同源匹配、缺日／缺模式、矛盾拒絕、多版本選擇、原始值與指紋完全一致、瀏覽不改資料或觸發核心。維持所有舊產物，新輸出另存；如有新頁，模擬與真實瀏覽器／手機 QA 必須分開標示。

下一步繼續工作模式。可直接交 Codex 的程式／契約／資料／測試／命令／錯誤語意與下一步驗收皆齊備，但外部 repo／環境尚未接入驗證，不要求非工程師使用者排障。

326 筆仍 UNREVIEWED、分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。不修改核心策略門檻，不部署／發布／發訊息／付費／交易／開子代理，不重試被拒 TWSE 端點，不把 staging 升級為正式證據。
