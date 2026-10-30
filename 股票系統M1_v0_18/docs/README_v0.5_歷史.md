# 股票系統 M1 v0.5：一次輸入，結構與均線一起分析

新增src/analysis_jobs.py，接受同一份來源、日線、價格模式與公司行動資料，產生價格結構與5/20/60/130/260日均線兩組獨立結果，以及逐日對齊紀錄。build_review.py已改走統一入口，重播頁因此使用同一次分析的輸出。

原src/jobs.py保留相容；既有結構與均線核心原樣保留。沒有綜合分數或新買賣規則。

## 可直接閱讀

- output/統一分析實跑結果.md：中文結果報告；兩檔各283筆、兩種價格模式，固定歷史樣本，不是即時行情。
- 價格結構重播.html：兩檔的預先計算重播。沒有新增手機上傳資料即時計算服務。
- output/M1_v0_5_驗收摘要.json：本版實際測試與限制。

## 統一入口實跑

```bash
python src/analysis_jobs.py --input data/8069_analysis_job.json --output output/8069_統一工作單實跑.json
```

新輸入版本為stock-analysis/1.0；結果為stock-analysis-result/1.0。輸出components.structure、components.daily_ma兩組結果，共用shared_input來源驗收報告及aligned_snapshots每日對齊紀錄。COMPLETED只代表運算完成，不是分類或交易驗收通過；空資料回傳EMPTY_INPUT。

兩份範例8069_analysis_job.json與6488_analysis_job.json提供完整輸入。來源id沿用原重播建構流程的本地日線內容指紋；upstream_source_id保留舊工作單的來源id。來源id屬追溯聲明，不等於已獨立認證來源。

舊入口仍可執行：

```bash
python src/jobs.py --input data/8069_job.json --output output/8069_舊工作單相容性實跑.json
```

## 實際驗收

53個Python測試與13項頁面邏輯測試通過。後者使用模擬元件與畫布，不是實際瀏覽器。四組真實樣本共1,132份每日對齊紀錄；結構與均線的八份獨立JSON檔皆與v0.4逐位元組一致。8069新舊命令入口皆實跑成功，舊入口結果等於上一階段實跑結果。

新增來源／單位／價格模式／日曆格式錯誤、核心輸出錯配、未來資料隔離、空資料、輸入檔保護及輸出失敗測試。輸出先寫暫存再完成替換，輸入與輸出不可是同一檔；不會以半份成功結果冒充兩個核心都完成。

## 日曆與品質說明

shared_input.data_quality是統一入口對整份輸入的共用驗收；若呼叫者提供expected_dates，對照結果適用於這次兩組分析的共同輸入。它仍不證明提供日曆是官方完整日曆。

兩組核心的原生輸出完整保留。均線模組自身未接收expected_dates，因此其原生calendar_status仍為UNVERIFIED；查看本次共同日曆驗收時須讀shared_input.data_quality或aligned_snapshots[].data_quality，不能將均線原生報告誤讀為另一次不同來源驗收。

## 重現

```bash
python build_review.py
python validate_release.py
python -m unittest discover -s tests -v
node tests/check_viewer_syntax.cjs
node tests/test_viewer_logic.cjs
```

核心與新入口只需Python標準工具；產圖另需requirements-render.txt的matplotlib。實際瀏覽器／手機觸控仍未驗收：v0.4曾因缺少Chromium啟動失敗，本版未宣稱有新的成功瀏覽器測試。

## 尚未完成與接續模式

完整官方日曆／停牌、更多獨立股票樣本、完整公司行動、歷史公告時刻、分類品質與交易價值仍未驗收。326筆仍UNREVIEWED，行動資格保持NOT_EVALUATED。週月均線尚未實作。

下一步繼續工作模式，優先補齊資料日曆與不同樣本的驗收；Codex交接資料已更新，但專案環境尚未接入或驗證。可讀取並執行專案後再轉Codex。
