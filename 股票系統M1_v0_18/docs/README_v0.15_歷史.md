# 股票系統 M1 v0.15：週／月計算、保存與讀回背景流程

現在一個明確工作命令就能完成「計算→保存→指定讀回」，不需先開網頁，也不用操作端手動拼接計算器與匯入器。只有 RUN 計算；READ 與 LOOKUP 只讀已保存資料，找不到指定身分／日期時不補算、不選最新。

新接入沿用原核心與不可覆寫保存契約。四檔、六組股票模式、2026-08-31／2026-09-30 共 12 份結果，經新流程重新計算保存後，完整保存檔與上一版完全相同。保存後回覆失敗仍能用分析身分讀回，不把「沒有回覆」誤報成「沒有存」。背景流程是單次工作入口，還不是持續運行主機、手機 App 或即時行情服務。

本版實跑 235 項 Python（新增 27）、50 項既有 Node 模擬、JS 語法與 validate_release 通過。558 份既有檔案逐位元組不變，包含原核心、三 SQLite、v0.14 週月結果庫、舊 CLI 與四份 HTML。原主文件另留歷史副本。

```bash
# 隨包已有 12 份新流程保存資料；RUN 每次明確計算一次，保存同內容去重
python src/period_workflow_cli.py --store period_workflow/output/背景流程結果庫 --input period_workflow/commands/8069_RAW_CANDIDATE_2026-09-30_RUN.json --output period_workflow/output/操作回覆.json
# READ / LOOKUP 不計算，失敗不建立庫
python src/period_workflow_cli.py --store period_workflow/output/背景流程結果庫 --input period_workflow/commands/8069_RAW_CANDIDATE_2026-09-30_READ.json --output period_workflow/output/指定讀回.json
python src/period_workflow_cli.py --store period_workflow/output/背景流程結果庫 --input period_workflow/commands/8069_RAW_CANDIDATE_2026-09-30_LOOKUP.json --output period_workflow/output/保存查詢.json
python period_workflow/run_acceptance.py
python -m unittest discover -s tests -v
python validate_release.py
node tests/test_period_viewer.cjs
```

新建空庫須明確 RUN 加 --create；不替既有不明目錄補標頭或重建。回覆包含 NOT_SAVED／UNKNOWN／COMMITTED，出錯時先依明確 ID 讀回；不要因沒收到回覆直接當作沒存。完整規格與操作範本見 docs/週月背景流程契約.md、period_workflow/commands。逐命令退出碼、完整驗收與交接在 output/v0_15_checks.json、period_workflow/output/週月背景流程驗收.md、docs/CODEX交接.md。

新保存結果可以原樣匯出原唯讀頁；period_workflow/output/週月背景流程結果瀏覽.html 與 v0.14 頁面位元組相同，沒有宣稱新 UI。真實瀏覽器、Android 開檔／下載、觸控與排版仍未驗收。24 月真實窗口不足保留空值；326 筆仍未覆核，分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。

下一步繼續工作模式，建立日／週／月已保存結果的唯讀對照接入，先核對同一股票、模式、分析日與資料來源，矛盾／缺資料直接顯示。保持各引擎與保存契約獨立；若需共用 schema migration，先提出具體相容方案。完整 Codex 開發交接已備，外部專案環境尚未接入驗證。
