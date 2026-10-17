# 股票系統 M1 v0.14：週／月結果保存與唯讀檢視

週／月計算結果已能獨立保存、指定讀回與離線檢視。四檔股票、六組價格模式在 2026-08-31／2026-09-30 共 12 份完整結果已實際保存，重複匯入去重，經獨立 CLI 子程序重開讀回全部相同。8 月底六份是明確執行歷史 RUN 產生，9 月底六份沿用 v0.13 實算；沒有宣稱保存全部 1490 個歷史結果。

新頁「週月保存結果瀏覽.html」先選股票／市場、價格模式、版本、截至日及紀錄。最新值同時列出已走完期間與包含當期候選；圖與表使用保存的週／月 OHLC、成交量及 SMA 曲線，缺值附原因。可下載完整 request／result／來源／日曆／理由／指紋，不在頁面重算。檢視與匯出也不 import 數值引擎。

保存採獨立不可覆寫 JSON 目錄，沒有改動舊 SQLite 或統一契約。同一分析 ID 若結果或理由不同就拒絕；中斷留下的未提交檔只報告、不假裝成功。讀取不挑最新版本或鄰近日期；回覆失敗可用明確 ID 讀回。

208 項 Python、50 項 Node 模擬檢查（既有 38＋新頁 12）、JS 語法與既有 release 檢查已通過。真實瀏覽器、Android 開檔／下載與觸控排版仍未驗收，不能以模擬測試代替。所有舊數值引擎、三資料庫與三 HTML 保留；原 v0.13 文件另有歷史副本。

```bash
# 計算：只在明確 RUN 才呼叫核心
python src/period_jobs.py --input period_analysis/requests/8069_RAW_CANDIDATE.json --output period_persistence/output/另一次計算.json
# 保存與讀取命令範本已備；重匯入原內容會 DUPLICATE
python src/period_store_cli.py --store period_persistence/output/週月結果庫 --input period_persistence/commands/8069_RAW_CANDIDATE_2026-09-30_IMPORT.json --output period_persistence/output/另一次匯入回覆.json
python src/period_store_cli.py --store period_persistence/output/週月結果庫 --input period_persistence/commands/8069_RAW_CANDIDATE_2026-09-30_READ.json --output period_persistence/output/另一次讀回.json
python src/period_viewer.py --store period_persistence/output/週月結果庫 --output 週月保存結果瀏覽.html
python period_persistence/run_acceptance.py
python -m unittest discover -s tests -v
node tests/test_period_viewer.cjs
python validate_release.py
```

先讀 AGENTS.md、docs/候選規則_v0.1.md、docs/週月保存與唯讀契約.md、docs/CODEX交接.md。驗收報告在 period_persistence/output/週月保存與檢視驗收.md；逐命令退出碼在 output/v0_14_checks.json。完整舊版證據、逐日前綴工程驗證、來源限制與 326 筆未覆核項目都保留。

目前仍是研究原型，分類 NOT_VALIDATED、交易資格 NOT_EVALUATED，沒有新訊號、績效、持股、雲端服務或發布。日曆已走完不代表行情完整性已認證；所有真實 24 月窗口不足保留 null。

下一步繼續工作模式，補上獨立週月 RUN→保存→指定讀回的一體化背景流程。Codex 開發交接已齊備；外部專案環境尚未接入驗證，不要求使用者自行設定。
