# 股票系統 M1 v0.2：資料驗收與覆核工具

本版接續價格結構候選核心，補強資料契約、版本追溯與人工覆核紀錄；候選策略參數維持v0.1。

## 可直接檢視

- 價格結構重播.html：已內嵌真實日線與核心輸出，增加日曆與當日事件狀態。JavaScript語法和資料一致性已測試；真實瀏覽器操作尚未完成驗證。
- output/覆核清單.csv：326筆轉折／區域候選，全為UNREVIEWED，不是已確認正確的分類。
- docs/資料契約_v1.0.md：白話說明錯誤、資料不足、零波動、無新事件、來源與版本如何區分。
- docs/CODEX交接.md：下一階段完整任務及實際未完成項目。

## 重現

核心與測試使用Python內建工具；產圖另需matplotlib。現有輸出已附在包內。

```bash
python build_review.py
python validate_release.py
python -m unittest discover -s tests -v
node tests/check_viewer_syntax.cjs
```

`node`只用於檢視頁的語法／瀏覽器QA，不是Python核心的必要條件。實際瀏覽器測試另見tests/test_viewer.cjs，還需要可用的瀏覽器執行檔。本次已嘗試補齊，但下載檔截斷而失敗；沒有列為通過。

完整工作單範例已提供，可直接執行：

```bash
python src/jobs.py --input data/8069_job.json --output output/8069_標準輸入實跑.json
```

## 覆核紀錄工具

目前沒有新增真實人工判斷。只有在實際檢視後，才填覆核者、決定與理由。命令範例的文字需要換成真實內容，不要直接拿範例當成正式意見：

```bash
python review_cli.py --queue output/覆核清單.json --journal output/人工覆核.jsonl --row 1 --decision UNSURE --reason "填入你實際觀察到的理由" --reviewer "填入覆核者"
```

row是清單中從1開始的項目；修訂同一項目時，另外傳入上一筆review_id作為--supersedes-id。記錄只追加、不覆寫；不同計算版本的項目不可混用。測試紀錄只用臨時資料，不寫入正式覆核簿。

## 已完成與仍未完成

四組真實樣本的轉折、區域及事件內容與v0.1一致。新增來源／單位錯配、價格缺值、非法數值、日期重複、未提供日曆及版本指紋等檢查，並區分EMPTY_INPUT、WARMUP、ZERO_VOLATILITY、NO_NEW_EVENTS與DATA_ERROR。最新測試數與執行結果以output/M1_v0_2_驗收摘要.json及實際測試紀錄為準。

尚未完成：真實瀏覽器操作、完整官方交易日曆／停牌認證、更多獨立股票樣本的分類品質驗收、完整公司行動與歷史公告時點。326筆待覆核項目沒有分類正解，不提供準確率或交易績效。

結構、證據、行動資格分開；本版仍無正式整理、突破、回測、買賣資格或全市場即時掃描產品。指紋是版本追溯工具，不是資料真實性或歷史可得性的認證。
