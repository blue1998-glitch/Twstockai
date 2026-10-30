# 股票系統 M1 v0.13：獨立週／月均線核心

已補齊週 4／13／26／52、月 3／6／12／24 的獨立計算，支援原始價與還原候選。先把日線依週／月聚合，再計算各期收盤均線；已走完期間與包含本週／本月的候選值分開。資料不足、未知缺口及不確定的第一期保留空值，不補零或猜休市。

本版是計算核心，最新結果保留為獨立 JSON。主資料庫與舊瀏覽頁尚未接入週月結果，沒有新增網站、持股、交易訊號或績效結論。已走完日曆期間也不代表資料完整性已認證。

四檔、六組價格模式共 1490 個逐日快照通過前綴重播；獨立分組與 Fraction 算術核對 52894 筆有價格聚合列、430352 個曲線位置（含 null）。188 項 Python（新增 32 項）、38 項既有模擬頁面、JS 語法與舊功能回歸通過。418 份既有檔案（含原引擎、三資料庫及舊 HTML）逐位元組相同。

```bash
python src/period_jobs.py --input period_analysis/requests/8069_RAW_CANDIDATE.json --output period_analysis/output/另一次_8069.json
python period_analysis/run_acceptance.py
python -m unittest discover -s tests -v
python validate_release.py
node tests/check_viewer_syntax.cjs
node tests/test_viewer_logic.cjs
node tests/test_saved_viewer_logic.cjs
node tests/test_volume_version_viewer.cjs
```

先讀 AGENTS.md、候選規則、docs/週月均線獨立契約.md、docs/CODEX交接.md。最新驗收在 period_analysis/output/週月均線核心驗收.md，機器證據在 output/v0_13_checks.json；六份完整工作單／最新結果在 period_analysis/requests 和 output。較早報告為歷史紀錄。

純核心與 JSON 入口只需 Python 標準庫，不靠網頁、SQL 或網路。重用已捕捉的日線、計畫日曆及個別休市證據，沒有新增抓取或提高來源認證。原生股數維持原單位；1101／2884 公司行動涵蓋仍 UNVERIFIED；24 月資料不足照實顯示。

沒有本版真實瀏覽器／手機驗收，沒有週月 UI；不能把舊頁模擬檢查當新介面已完成。326 筆仍 UNREVIEWED，分類 NOT_VALIDATED、交易資格 NOT_EVALUATED。

下一步繼續工作模式，建立週月結果的獨立保存與唯讀檢視，保持現有日線契約不變。完整 Codex 交接已備，外部專案環境尚未接入驗證。
