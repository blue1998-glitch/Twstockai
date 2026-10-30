# 開發交接：M1 v0.16 日／週／月對照成品

先讀 AGENTS.md、README.md、候選規則、docs/日週月唯讀對照契約.md、cross_view/output/日週月整合驗收.md。v0.15 主文件另存歷史。此次已將前版規劃一次執行到可交付的資料接入、頁面、匯出、驗收與封裝，不再把例行工作拆成下一版才能完成。

## 已實作

新增 cross_view.py（純唯讀 view model）、cross_view_export.py、cross_view_cli.py、cross_view_template.html，既有 src 全部保持不變。新 schema 只屬外部 view/catalog/selection/sources，不更動原引擎或共同保存契約；沒有 migration、網路／SQL 寫入或跨尺度交易結論。

明確來源 config 以別名定位日線 SQLite 與週月 file store，日期清單明列 2026-08-31／2026-09-30。日線只擷取原已保存精確快照與原始價前綴、已生效事件及完整追溯；週月嵌入完整原保存紀錄。公開 read-only load/list，完全不 recover/save/calculate；fresh-process import blocker 已驗證不能 import 任一核心或計算工作流程，仍可匯出。

對照核對 stock/exchange/mode/as_of、來源 ID／量能單位、已支援版本及其連結、各元件原始資料與有效事件指紋、實際筆數／最後價格日、公司行動涵蓋、還原錨定與選取內容指紋。daily-sma-0.1 沒有 anchor 欄位，依明確該版 as_of 錨定契約檢查。日曆原報告各自保留，不把不同格式的 calendar metadata 當相同認證。

ALIGNED_INPUTS 只是輸入對齊，不是策略一致。CONFLICT 阻止合併圖表，允許下載原資料與檢查；MISSING_DAILY／MISSING_PERIOD 只顯示獨立一邊，無補算。版本和 ID 都明選，無 latest／鄰日 fallback。歷史 structure-0.2 的單位欄位缺失與原生股數證據誤標均警告，原快照不重寫。

日線三份缺口是獨立 prepare_daily.py 明確 RUN 6488 Raw／Adjusted、2884 Raw，取既有 period requests 轉既有 stock-analysis/1.0 工作單。as_of／calendar 移到日線適用的 expected_dates 格式，來源與事件不新增、不升級；分析證據 ledger records=[]、UNVERIFIED。新庫 cross_view/output/補齊日線.sqlite3，原庫不變。prepare_daily 在標示 PASS 前會由另一個程序公開讀取全結果指紋，不能只信同程序回覆。

初期新庫曾發生三次 RUN 回覆存在，但跨程序唯讀被 rollback journal 阻擋。明確寫入工作呼叫既有 AnalysisStore.recover 後發現兩筆／566 快照，再明確重跑補齊，最後不同程序驗證三筆／745 快照、完整 result 指紋一致。沒有刪除 journal、重建舊庫或變更引擎。根因尚未確認，詳見 cross_view/output/新庫讀取診斷.json；不要把一致狀態恢復描述成根因已修復。若再次發生，保留檔案與錯誤，由獨立工作恢復並重驗，唯讀層不可修復。

## 實際資料與 UI

歷史日線六份（8069 Raw/Adjusted、1101 Raw，各含 structure 0.2／0.3）＋新日線三份，共九 record／18 精確日線快照。週月十二份，形成 18 個 ALIGNED_INPUTS 對照，涵蓋四檔、六組股票／模式、兩日期。before_fill config 有六個原週月缺日線案例，繼續作缺資料防禦測試，未隱藏這個事實。

日週月研究對照.html 以股票／市場→模式→日期→日線版本→週月版本明選，再按讀取。三張獨立圖表與完整精確表格、週月 elapsed/candidate、null 理由、價格日／期間結束日、品質／來源與原轉折區域證據。只有 Raw 日線與保存週月 OHLC 畫 K，紅漲綠跌；Adjusted 日 K 未保存，明示限制、只畫原 MA，不在 JS 計算。千分位逗號只供畫圖解析，原資料與下載完全保留。沒有重新計算均線、型態、量比或區域。

253 Python（新增 18）、66 Node 模擬（既有 50＋新頁 16）、JS 語法與 validate_release 通過；18 組頁面下載與 Python select 完全相同。正式瀏覽器測試已準備並實際啟動一次，缺執行檔 BLOCKED，checks 空白，絕非 PASS。實機 Android 亦 NOT_TESTED。原 v0.15 交付清單中的舊引擎、庫、資料、HTML 與程式逐位元組不變，主文件更新另存歷史。

cross_view/run_acceptance.py 經公開存取介面比對全部原日線快照／完整週月紀錄，保存 18 組 selection／view JSON，另由兩個 CLI 子程序驗證不同來源的精確選取。來源庫與舊 HTML 前後 hash 不變。原始比對、命令退出碼、介面邏輯與 browser BLOCKED 證據均在 output 和 cross_view/output。

## 已完成範圍與剩餘界線

目前不需為此次規劃再新增例行開發階段。若接續工作，優先在具可用瀏覽器的環境執行 tests/test_cross_view_browser.cjs，測 1280 桌面與 390 手機模擬、18 組切換、JSON 下載、JS 錯誤與頁面溢位；另外記錄物理 Android 開檔／下載／觸控。不得把手機模擬等同實機。缺執行檔不重複盲試安裝，不以其他模擬結果替代。

正式分類品質、326 筆人工覆核、交易價值、持股、盤中全市場、全天候主機／發布／付費服務都未完成，也不是本次對照層完成就可自動批准。這些涉及核心策略、資金或部署時須使用者明確決策。不要為了宣稱全案完成而擴大候選規則用途。

封裝後獨立驗證見 output/M1_v0_16_封裝驗證.json；完整來源、補齊工作單、原資料庫、對照 config、18 個結果、程式、測試、失敗紀錄、唯讀離線頁與操作說明全在包內。下一位 Codex 先重現，不改策略或保存格式；外部 repo／環境目前尚未接入驗證，這裡不聲稱已在外部 Codex 成功跑過。

使用者允許一般可逆作業自主完成，僅核心策略／重大架構／必須授權事項才問。不開子代理、不發布／部署／發訊息／交易／付費、不重試被拒 TWSE 端點，不改歷史原檔或升級證據認證。classification_quality NOT_VALIDATED，action_qualification NOT_EVALUATED。
