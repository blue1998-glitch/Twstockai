# 決議來源0.4：本環境驗收及續接

正式程式沿用action_resolution／action_resolution_sources，固定成品dae1f6e580f466c4f44cb271a350f4b420d5b5eb；不再發布另一套來源0.4。其README／CONTRACT／REPORT在相鄰action_resolution_20261023，完整parent0.3、策略／引擎／庫／歷史與舊ZIP保持。

本輪補充兩項測試及本環境驗收：原0.4的29項加新增2項，共31項本環境實際通過。PDF額外重抽全文byte比較有差異，所用頁及全部決議欄位精確一致；不同假想股東各自圓整不合併。7／26等平行草稿紀錄不是正式交付計數，草稿已另存本地而未發布。

- [實際進度／失敗／未完成](REPORT.md)、[完整Work續接](WORK_HANDOFF.md)。
- [31項實測](tests.log)、[正式0.4的28檔固定GitHub回讀](canonical-product-readback.json)。
- [PDF抽字重核](pdf-extraction-recheck.json)、[首次assert失敗](pdf-extraction-first-failure.json)、[完整文字差異](pdf-extraction-diff.txt)。
- 新可執行驗收包與固定提交讀回：根deliveries/m1-resolution-validation-20261023/README.md。

標準Python離線：
```bash
cd 股票系統M1_v0_18
python3 -m unittest rotation_research.test_action_resolution rotation_research.test_resolution_validation -v
```
若重現producer，請在另一新解壓目錄執行python3 -m rotation_research.action_resolution_sources；本輪新封包保留原511成員，重現與manifest核對見delivery/package-verification。完整checkout工程依根AGENTS先bootstrap。

正式毛額API是action_resolution.preview_shareholder_cash；只接受明示假想權利股數。3股×0.8＝2.4→2元毛額；不同人1股及4股各為0、3元，不能合併算一人5股的4元。稅費／個人淨額／到款／期初權利與報酬仍未核。
