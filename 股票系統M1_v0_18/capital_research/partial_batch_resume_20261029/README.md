# 新批部分成交後，直接重用原續播入口

已完成「原帳結清 → 新獨立批次 → 部分成交 → 續播交割與到期」的合成使用案例。**產品程式改動0；不用重建續播器或加轉接層。**

原帳已有B7；新批20再成交7後，帳上B14，新單剩13。原已到期單的另一個剩13仍保持關閉，不能混用。新單由原resume_orders帶完整前身續播，原本金1180、一般reserve100、權利與全部12個token保持。

| 水位 | 已結現金 | 應付 | B／C實股 | 新單剩餘／預留 |
|---|---:|---:|---|---|
| 1/9部分成交 | 858.86 | 141.14 | B14／C2 | 13／261.65039 |
| 1/10保存 | 858.86 | 141.14 | B14／C2 | 13／261.65039 |
| 1/12交割、到期 | 797.72 | 0 | B14／C4 | 13到期／0 |

797.72＝858.86＋原現金權利80－新成交成本141.14。沒有提前使用應收、重扣應付或重設本金。一次續播及分兩段續播，皆與完整一次執行的逐觀察／每日列／完整終態相同。

- [REPORT：結果、保全與限制](REPORT.md)
- [事前契約與手定預期](CONTRACT.md)
- [新批部分成交actual](actual/prefix-action-result.json)
- [直接續播actual](actual/direct/result.json)／[逐點等價核對](actual/direct/comparison.json)
- [兩段續播actual](actual/Jan10-to-Jan12/result.json)
- [拒絕案例總表](summary.json)
- [每日獨立核帳](test-evidence/daily-handcheck.json)／[原帳與前身核對](test-evidence/chain-equivalence.json)
- [4個必要測試方法](tests-final.log)／[保存自審](preservation.json)

全部價格、tape、日曆及close proof均來自保存的合成資料，原窗口止1/12。1/9後沒有更多執行觀察；1/12空日有明示模型完整性宣告，不能把空白當無成交。本例只驗已成交7的交割與剩13到期，**沒有證明剩13再次成交**，不補行情或給策略排名。

舊B20全成actual原樣保留，本輪另存容量7模型。所有正式false、primary_pressure_id=null、UNKNOWN、真實資料拒算及未支援能力保持。一般使用無需重跑凍結／build；它們只向新檔create-only保存，不能覆寫既有證據。
