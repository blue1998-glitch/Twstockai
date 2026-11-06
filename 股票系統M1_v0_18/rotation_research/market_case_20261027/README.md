# 首個市場案例：準備接線完成，市場帳務仍未執行

本輪補的是**明示案例輸入準備／共同條件綁定／原來源資格閘門**。不是市場回測或交易策略。A=1101、B=2884，沿使用者指定五個價位與參照，不使用舊六方案比例/代理。

- [白話結果與限制](REPORT.md)、[事先凍結契約](CONTRACT.md)
- [未代填參數的原案例](input.json)、[原案例最終actual](after-final/actual/draft/actual.json)
- [完整參數接線控制](controls/source-bound-input.json)、[仍被原來源拒算的actual](after-final/actual/explicit-control/actual.json)
- [最終18項準備診斷摘要](after-final/summary.json)、[8個唯一測試方法log](tests-first.log)
- [四月前綴的三種未來變體](test-evidence/future-prefix.json)、[缺B意圖](test-evidence/missing-B-intent.json)
- [來源0.10與全部parents的身分](intake.json)、[保存來源指定](source-spec.json)、[manifest](CHANGE_MANIFEST.json)

原案例是AWAITING_EXPLICIT_INPUT：尚未定起始現金、共同起訖、股數/有效價/費稅/交割日、共同容量/交易狀態/可得時間、決策截止與B時點意圖。都原樣null，不使用控制值代填。10000現金/10股等只是不可執行的接線測試假設，沒有被採用為本例研究參數。

完整控制只準備既有RAW帳務input，三路沿原source0.10 qualify都REFUSED；數值replay0、績效null、ranking=null。沒有重開六月本金、建單、成交、評分或自動選擇。新的明示現金帳是假設，不是使用者真實帳戶或舊期初權利的零值證明。

純API：`rotation_research.market_case.prepare_case(request, saved)`。當期前綴API：`prepare_decision_prefix(request, saved, 'A-return')`，它先限當期事實再讀欄位，不因六月B的內容不同而改四月前綴；完整來源身分另列。歷史available_at仍null，當時可用signal列表空，不認證過去的交易資格。

外部IO：`rotation_research.market_case_io.prepare_and_save(repo,request,source_spec,store,id)`，明示四份保存來源及指紋、沿原Journal exclusive保存讀回，沒有新增READ工具。CLI只做準備，所有參數必填；已保存案例直接讀JSON，不要在既有證據目錄重跑以增加PASS。

```bash
python3 -B -m rotation_research.market_case_io \
  --repo /workspace/Twstockai \
  --input rotation_research/market_case_20261027/input.json \
  --source-spec rotation_research/market_case_20261027/source-spec.json \
  --store /tmp/twstockai-explicit-market-preparation-NEW-ID --id explicit-new-id
```

在股票系統M1_v0_18執行；命令是新準備操作，並非READ或市場回放，不必由使用者操作。此處沒有支持數值dispatch的新來源契約；來源仍不足就停下，未來不能只改旗標自動放行。

最終source看after-final與test-evidence。根actual/summary/source-versions-before-run及saved為初始階段留史；新增當期專用前綴後，才以after-final保存新source結果，不覆寫原件。controls/explicit-input是自審發現錯月份quote-0的保留輸入；正例改存source-bound-input，原件/expected未覆寫。

下一步需要Work與使用者先明示研究參數及缺少證據的處理範圍；不是請使用者搬檔、提供私人紀錄或猜最佳比例。1101舊UNKNOWN、70/2/其中8/真實合格0、正式false及主壓力null保持。
