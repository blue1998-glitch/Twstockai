# 開發交接：M1 v0.10 單一分析與保存流程

先讀AGENTS.md、README.md、候選規則、docs/單一分析流程契約.md與workflow/output/單一分析與保存流程驗收.md；舊版交接為歷史紀錄。

## 最新實際狀態

134項Python（新增16項workflow整合／失敗測試）、13項Node模擬頁面邏輯、JS語法與舊功能回歸通過。output/v0_10_checks.json與相應log為證據。31份既有檔案不變，包含7份既有核心、3份保存模組與v0.9資料庫。326筆仍UNREVIEWED。

新src/analysis_workflow.py固定入口execute_workflow(request,database,create_if_missing=False)，契約analysis-workflow/1.0，支援RUN／READ／LOOKUP。RUN呼叫原run_analysis_job、validate_bundle、AnalysisStore.recover/save/load；READ／LOOKUP不計算。數值與資料層原碼未改。workflow_cli.py處理檔案與回覆，重用既有JSON讀寫工具；保護輸入、硬連結、資料庫與復原檔路徑。

RUN／READ預設精簡快照，可選include_bundle=true核對完整結果。指定日期不存在即錯誤；未指定選最後保存日；空資料EMPTY_INPUT、snapshot=null。LOOKUP依完整工作單與證據指紋精確查回，匹配多種規則時列出全部，不擅選最新版本。此為小型研究庫實作，未聲稱全市場低延遲查詢。

錯誤標記stage與commit_status。尚未保存為NOT_SAVED；保存呼叫回覆不明為UNKNOWN，應LOOKUP；已確認保存但讀回／匯出失敗為COMMITTED，回傳record_id供READ。不要用例外猜測未提交，亦不重建資料庫。COMMITTED也涵蓋已存在而去重確認的紀錄；不是說每次重跑都有新增寫入。

workflow/run_acceptance.py透過12個獨立工作程序跑3組完整工作單：8069 Raw／Adjusted各283筆、1101 Raw 179筆；完整結果與既有直接引擎相同，歷史日期快照相同。台泥實際保存後，匯出至不存在目錄失敗；另一程序LOOKUP查回，再重跑EXISTING且數量不變。未核實事件維持未啟用。另有保存確認遺失、讀回失敗、保存中途失敗等單元故障測試。

新庫workflow/output/分析流程_v0_10.sqlite3保存3分析版本、3紀錄、9去重物件與745版本×日期索引。舊persistence/output庫和驗收紀錄逐位元組不變。原始PDF／HTML仍在包內，沒有新增外部資料抓取。核心另以獨立程序禁止sqlite3／資料層／workflow匯入後實跑成功。

## 下一個工作階段：保存結果唯讀瀏覽與匯出

1. 先建立獨立接入器，使用工作流程READ或AnalysisStore的公開讀取介面，列出保存版本與股票／價格模式／日期。保持穩定record_id、來源、規則與價格基礎，不能把不同版本數字混到同一張圖。
2. 以已保存快照輸出瀏覽資料；畫面只顯示，不重新計算均線、轉折或區域。可優先做離線匯出接入現有重播頁，或準備最小讀取服務，先不發布／部署。
3. 實跑至少一個已保存的Raw／Adjusted案例，比對呈現資料與READ輸出一致。未滿260筆均線顯示資料不足，不填0；UNVERIFIED、NOT_VALIDATED、NOT_EVALUATED與各日期／價格尺度限制必須可見。
4. 版本切換、日期切換、缺失日期與錯誤庫不能殘留舊數字冒充新結果。不得因瀏覽而新增、覆寫或刪除分析紀錄。
5. 保留現有直接JSON與workflow入口。不要為UI將核心綁進Streamlit、FastAPI或儲存層；若新增服務，屬外部薄接入，不改核心規則。
6. 目前沒有真實桌面／390px手機瀏覽器驗收；若瀏覽器仍不可用，繼續誠實區分已執行的資料／模擬邏輯測試與未執行的觸控／版面驗收。

## 重現與模式

命令見README及流程契約；workflow/run_acceptance.py可在包內庫重跑去重，也可--db指定全新庫。核心與新流程僅標準庫；Node用於模擬頁面測試。未重建或修改舊重播頁，不把舊瀏覽器嘗試當成本版成功。

繼續工作模式，Codex交接完整但外部專案環境未接入驗證。HTTP服務、手機頁面、持股／成交、正式訊號、雲端同步、備份、週月均線、正式整理型態、完整來源及分類／交易品質仍未完成；交易資格NOT_EVALUATED。不發布、不付費、不交易、不發訊息、不啟動子代理、不重試或繞過已拒絕的TWSE除權息介面。每次結尾明示工作模式或Codex。
