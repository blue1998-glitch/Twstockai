# 原數量條件單中途重評 0.1

純API：`capital_research.conditional_quantity_review.reassess_conditional(request)`。

可直接讀[cases/valid-old-fact/input.json](cases/valid-old-fact/input.json)及[after-final/valid-old-fact/actual.json](after-final/valid-old-fact/actual.json)。入口[CONTRACT.md](CONTRACT.md)、[REPORT.md](REPORT.md)、[after-final/summary.json](after-final/summary.json)、[tests-final.log](tests-final.log)。一般READ只讀JSON，不重算。沒有UI或自動委託。

原quantity_replay仍0.1、quantity_candidates仍0.2、core／execution仍0.8，沒有改舊結果／原件。新API先跑原數量外層閘門，以原日終prefix建立真實帳戶，再委派原生重評，最後仍為同一張原單。新增批次不走此入口。

`cases/*/actual.json`與根summary為第一次切段錯誤結果；`check-2`為中間結果，當時檢查器誤將原ledger新增的OPENING_RECEIVABLE標籤視為權利不一致。均留史。只有`after-final`綁目前source；input／expected原bytes保持。17案例不等17獨立市場樣本；16唯一方法本輪執行一次，不加案例或中間批。合成機制不證真實績效、策略勝負或正式資格。
