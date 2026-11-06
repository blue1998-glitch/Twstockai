# 股票系統 M1 v0.16：日／週／月唯讀對照

已把本次規劃的資料對齊、缺口補齊、同頁對照、版本明選、結果匯出、錯誤處理與回歸驗證一起完成。開啟「日週月研究對照.html」，依序選股票／市場、價格模式、分析日、日線版本、週月版本，再按「讀取所選對照」。

四檔股票（8069、6488、1101、2884）、六組股票／價格模式、兩個保存日，均有可對照資料。九份日線保存紀錄取出 18 個精確快照，與 12 份週月結果形成 18 種對照。8069／1101 保留歷史兩版，必須明選；6488／2884 原先缺的三份日線，已用既有來源與計算流程另存新庫，沒有改舊資料或新增行情。

頁面提供日／週／月保存均線、可用的原 K 線、週月兩種口徑、空值原因、資料品質，以及原轉折／區域證據。發生、首次觀察、確認時間分開保留。Raw 日 K 與週月 K 紅漲綠跌；還原日 K 未保存於原日線契約，該模式只畫原保存均線，不在頁面推算 OHLC。來源價格含逗號只在畫圖座標解析，不改保存數字。

對照頁、選取與匯出全程只讀。股票、模式、分析日、來源、單位、截至日資料／事件指紋或還原錨定不同就停止合併；缺資料只顯示現有一邊，不重算、不補零、不挑鄰日或最新版本。可以下載所選原資料與完整對齊檢查，內容與後端 select 完全相同。

253 項 Python、66 項 Node 模擬頁面檢查、JS 語法與原功能檢查通過。真實 Playwright 檢查已執行啟動，但缺 Chromium 執行檔而 BLOCKED；真實瀏覽器、Android 開檔／下載／觸控仍未驗收，不能當成已完成。工程驗收不代表分類或交易策略驗證。

```bash
# 唯讀匯出，沒有計算路徑
python src/cross_view_cli.py --config cross_view/sources.json --html --output 日週月研究對照.html
python src/cross_view_cli.py --config cross_view/sources.json --selection cross_view/requests/8069_RAW_CANDIDATE_2026-09-30_structure-0.3-research_SELECT.json --output cross_view/output/指定對照.json
python cross_view/run_acceptance.py
python -m unittest discover -s tests -v
node tests/test_cross_view.cjs
node tests/test_cross_view_browser.cjs
```

cross_view/prepare_daily.py 是獨立、明確的計算工作，不會被讀取或匯出模組引入。只有重新建立補齊日線驗收庫時才執行；一般瀏覽不需 RUN。新的 cross_view/output/補齊日線.sqlite3 與所有歷史庫分離，三份資料已由新程序完整讀回核對。

文件入口：AGENTS.md、候選規則、docs/日週月唯讀對照契約.md、docs/CODEX交接.md。逐命令退出碼、實算驗收、初期新庫讀取診斷、瀏覽器阻擋證據與封裝驗證均保留。初期新庫曾留下 rollback journal，已透過既有明確恢復流程處理並重新保存／跨程序核對；根因未確認，不能宣稱修好底層成因，讀取端仍禁止自行恢復。

本次可自行處理的整合範圍已完成。剩下的實機驗收受環境限制；正式分類／交易價值驗證與公開部署都尚未執行。326 筆覆核仍 UNREVIEWED，分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。完整 Codex 交接已備；目前仍用工作模式，外部 Codex 專案尚未接入驗證。
