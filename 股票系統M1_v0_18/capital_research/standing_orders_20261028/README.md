# 原未完成委託與未交割款跨輪續播 0.1

現在可以在原合成帳的日終 checkpoint 停下，再續播**已核准的原單剩餘量與交割**。不必先撤單、重下或清掉應付款；沒有新策略、委託、批次或本金。

入口是 `capital_research.execution_continuation.resume_orders(request)`。輸入範例：[部分成交後續播](cases/partial-fill/input.json)；保存結果：[actual](after-final/partial-fill/actual.json)。純函式無檔案／網路 IO，呼叫方自行讀 JSON 與保存結果；這是明示 RUN，不是 READ。舊保存結果只讀，不自動升版。

| 閱讀入口 | 內容 |
|---|---|
| [REPORT](REPORT.md) | 白話結果、逐日獨立核帳與限制 |
| [事前契約](CONTRACT.md) | 輸入、完整觀察證明、版本與範圍 |
| [最終總表](after-final/summary.json) | 八份主正例、十六份拒絕反例 |
| [部分成交逐觀察比較](after-final/partial-fill/comparison.json) | 與舊引擎一次執行的完整結果、每日列、各觀察點一致 |
| [兩次續播](controls/partial-fill-to-Jan12/actual.json) | 1/6 → 1/8 交割 → 1/12，沒有新單 |
| [應收／應付共同存在](supplement/receivable/actual.json) | 原 A 賣出應收不能提早花；原現金與股份權利一次到位 |
| [可知後無 tape 仍取消](controls/no-tape-after-known/actual.json) | 保留已成交 B7，取消剩13並釋放原單預留 |
| [既有重評歷史](controls/accepted-history-resume/actual.json) | accepted latest、收據與所有 token 原樣接續 |
| [最終必要測試](tests-final.log) | 9 唯一方法通過，不累加前批8或歷史測試 |
| [程式自審與保存核對](preservation.json) | 歷史原件／事前凍結內容、最終來源、來源差異 |

請先提供完整 `root_job`、原 checkpoint、精確 latest、完整 `path` 與本片段 `segment_tape`。每個交易日（含空日）必有明示合成完整機會宣告；沒有記錄不能當作沒有成交。尾段只能是原窗口中完整路徑的精確切片。來源不明、漏段、重複、錯前身或改原帳都停止。

新入口重建截止前歷史以核對 checkpoint，再讓**原執行迴圈帶狀態只跑尾段**。帳務仍由既有 action_ledger 計算。重建不是再次送單或入帳；輸出分列歷史重建觀察數與尾段處理數。內層 execution.new_fill_ids 保持原 job 累計語義；本片段新成交請看外層 new_fill_ids_this_segment。

原活單不能藉此轉成新批；未收到的重評即使自稱日期較早也拒絕。需要新決策的條件單不因交割而自動放行；原新決策入口的活單／應付拒絕仍在。任意外部單、未知期初應付、缺完整路徑及來源認證不在本版範圍。所有結果只證合成機制，正式資格及真實資料拒算不變。

`freeze.py`／`complete_intake.py` 是本輪事前凍結的歷史步驟；`build.py` 只向新目錄 create-only 保存，不可覆寫已有證據。測試也使用 create-only 證據輸出，已有保存內容不應為重跑而清除。一般使用不需要重跑這些生成腳本。
