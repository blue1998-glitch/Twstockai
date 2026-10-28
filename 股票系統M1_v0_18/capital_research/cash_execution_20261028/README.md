# 明示行動接原合成執行0.1

現在可把**完整通過檢查的HOLD／現金買進行動**，與外部明示委託、原日曆及tape一起送入原執行器。公開純入口 `capital_research.cash_action_execution.execute(request)`，不生成股數／委託、選策略或開真實市場回放。

- [自審報告](REPORT.md)、[事前契約](CONTRACT.md)
- [27個有限案例摘要](summary.json)、[7唯一方法log](tests-first.log)
- [保留A用現金買B完整input](cases/keep-A-buy-B20/input.json)、[保存actual](actual/keep-A-buy-B20/result.json)
- [退出A後接原帳買B](actual/exited-A-buy-B20/result.json)、[續留應收等原款到位](actual/hold-receivables-to-settlement/result.json)
- [部分成交7／剩13活單](actual/partial-7-active-13/result.json)、[13到期](actual/partial-7-expired-13/result.json)、[13已知撤銷](actual/partial-7-cancelled-13/result.json)
- [假首次：原core可行但外層拒絕，執行0次](actual/outer-rejected-core-feasible/result.json)、[偽造外層批准仍拒絕](actual/forged-outer-approval/result.json)
- [逐日原帳核對](test-evidence/continuous-book.json)、[純呼叫／數值環境](test-evidence/pure-context.json)
- [原現金欄位手算勘誤，舊oracle保留](diagnostics/pretest-cash-role-correction.json)

|合成情況|保存結果|不代表|
|---|---|---|
|A100保留，用原現金買B20|A仍100；其他C權利保留|假賣A籌資或批准策略|
|A已退出，買B20|接原opening2180及995賣出應收；終點現金1673.6|換股日另開本金、應收提前可用|
|只成交B7|原現金1000、應付141.14、嚴格可用858.86；剩13預留261.65039，一般reserve100另在|把現金、應付與預留混成一筆|
|剩13到期／中午可知撤銷|B7保留；剩13關閉、預留0|事後取消已合法成交7股|
|漲停買不到／容量0|新成交0，原現金／應收／權利照帳接續|已完成買進或虛構成交價|
|HOLD或明示空orders|不產生新委託；原權利按原帳到位|自動補齊買進數量|

所有價格、數量及金額均為既有明示假想fixture延伸，不是使用者本金N或市場②規則。原帳窗口止於1/12，沒有新增1/13行情。原核心、帳務、資格／事實歷史與quantity均未改。

## 使用與綁定

外部載入cases的完整input後呼叫`execute(request)`；結果在`run`及`source_integrity_metadata`。入口本身不讀檔、不寫檔或發網路。保存後直接READ原JSON，不重新RUN。

完整`checked_action`及完整`action_input`皆必須提供，並明示expected_checked_action_id。入口核完整指紋與原輸入，再沿原evaluate重驗整份回條，包括外層批次資格；不是只信core feasible或candidate ID。這是RUN必要校驗，不冒純READ或來源認證。改metadata中的reserve、改股數、偽造批准狀態，即使重算外部hash也不能通過。

委託只能是原適用股的BUY，拆單總量不能超過已核行動；HOLD不能附買單。原origin_ledger及close proof與checkpoint必須全文相同，前身由原latest取得；不接受continuation／family／decision／reassessment覆寫。價格、費稅、容量、共同風險、限制失效、交割及預留由原simulate處理，返回decision必與原核准decision全文相同。完整job／execution／checkpoint保留，可沿既有入口在支援狀態下繼續。

## 驗證與限制

先保存27份精確input/expected及來源版本，才實作新adapter；其中4份是新HOLD、未來撤銷、新A事實及假首次的必要純檢查，其餘重用原保存回條。沒有重跑原7方法或其他舊suite。27案不是27個市場樣本；本輪只有7個唯一測試方法、7次執行，首次全過。

買進B7手算原稿把858.86嚴格可用額寫成已結現金，原稿／frozen保持，另附依原action_ledger買進應付與交割規則的欄位勘誤：1000現金－141.14應付＝858.86，不扣成兩次。無帳務程式、輸入、狀態／拒絕理由oracle變更；正式方法測試前即記錄勘誤。

完整來源／request／job指紋屬metadata。未來1/12報價改成另一個假想值，不改1/8截止的numeric_result；完整origin ID仍不同。正常及既有惡劣Decimal context的完整結果相等，caller、DefaultContext及輸入不變；禁IO／網路／quantity生成控制通過，帳務及合成simulate為必要呼叫，不能稱引擎呼叫0。

活單或未結應付的checkpoint照實保留，但不中斷承接／新批仍未支援，不會自行撤單、忽略預留或清應付。本輪已結清checkpoint接原HOLD門檻通過；部分活單再入仍NOT_IMPLEMENTED。未新增0.9同單複合承接完整矩陣、R2/F、來源認證、整張域、八行動dispatcher、全市場掃描或績效排名。

真實producer／資格重算／九路徑／市場六方案／UI／Android／樣本外均未執行。1101期初cash_claims UNKNOWN、來源0.10所有parents、70/2/其中8/真實合格0、正式false及主壓力null保持。Work原件／Astra／救援仍未讀；不要求使用者搬檔。

唯一Codex依根功能里程碑自審、正常commit/push及固定SHA讀回。無人工操作、無例行Work工程驗收要求。資金／權利／成交／未來資訊額外複核集中於本報告。未定N、比例、風險／策略仍由Work與使用者研究，不由本入口推導。
