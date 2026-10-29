# 已結清原帳明示減碼／退出 0.2（事前契約）

基線da8a9bf4e95898c6e9d95369c8cbc141b27bfe74；唯一Codex、原/workspace/Twstockai與dev/m1-v018-chart-annotations。本輪只補受控SELL行動與原執行器的接線，不制定賣出時點、比例、風險或勝者，不另寫帳本、費稅、成交或數量求解。舊0.1及保存原件不遷移。

## 輸入與版本

沿cash_action.evaluate，新增capital-cash-action-input/0.2 → capital-cash-action/0.2。頂層仍exact schema/synthetic/decision_template/account_source/action/policy。新版本僅處理SELL；舊HOLD/BUY仍用原0.1，不能交叉借用checked結果。沿原完整50位Decimal Context與純數值／外部IO分離。

account_source只接受完整CHECKPOINT及expected_checkpoint_id、expected_latest_decision_id，必為明示合成原ledger。沿validate_checkpoint／account_at_checkpoint取得原帳、可賣量、一般reserve、權利、latest及全部token，不收外填account/plans/tokens。只限已結清、無活單／應付且無原未支援限售狀態；不得因要賣而刪掉拒絕或推定限售解除。來源／基底／調整版本及當期mark沿原契約核對，真實RAW不得改標合成。

action exact：id、kind、code、sell_shares、reason。reason須非空明示研究理由；sell_shares是外部明示正整股，不用負additional_shares冒充SELL。

- REDUCE_HOLDING：sell_shares不得超過可賣，且須小於實股，留下指定股票餘量。
- EXIT_SELLABLE_HOLDING：sell_shares必精確等於當期可賣量，不自動選量。成交後仍須照actual判斷；EXIT意圖不等已全成，也不表示全帳現金。若可賣限制無受支援證明，保留原拒絕。

targets從原帳取得，只減少指定code；其他資產及股份／現金權利不變。沿既有減碼候選的family E/R1、core.resume_decision與policy明示edge/來源/可得時間核資格／成本／風險／不交易區間；不改核心門檻。SELL不需要新的買進觸發，不消耗或清掉舊token來假造下一批資格。沒有SELL後自動買進。

## 執行契約

cash_action_execution.execute新增capital-cash-action-execution-input/0.2 → capital-cash-action-execution/0.2，仍綁完整action_input／checked_action／expected_checked_action_id／execution_spec。只接受同版本0.2完整checked結果並沿原evaluate全文重驗；INPUT_ERROR、REJECTED、UNKNOWN或未支援都不能靠單獨core feasible放行。

外部明示orders/tape/日曆/限價/期限/成交及交割模型；每單只能是核准code的正整股SELL，拆單總量不得超過sell_shares。BUY、別股或同股反向單拒絕。允許少量／空orders，不補齊、不自動建單，也不假定退出完成。原simulate／ledger處理部分成交、無成交、限價、容量、跌停、費稅與交割；成交後應收不能提前當現金。原origin、close proof、opening、fills／order_history／fact_sources／reassessment_attempts、latest及全部token完整接續。

## 凍結合成正反例與獨立預期

主要原件為standing_orders_20261028/controls/expired-to-Jan8/actual.json的1/8完整checkpoint：原本金1180、已結現金858.86、一般reserve100、B7/C2，另有80現金權利／C2股份權利；舊單剩13已到期。使用既存1/9 A/C/B tape、原1/12日曆交割，不補行情。限價19.98只為明示合成執行參數（價格20沿原10bps滑價的有效價），不是退出門檻。

- 減B3：3×19.98－費1－稅1＝應收57.94；1/9現金仍858.86、總應收137.94、B4/C2；1/12現金996.80、B4/C4。
- 退出可賣B7：7×19.98－費1－稅1＝應收137.86；1/9總應收217.86、B0/C2；1/12現金1076.72、B0/C4，不能稱全帳現金。
- B7拆3＋4：原逐fill費稅各1，總淨應收135.86，1/12現金1074.72；不能沿單筆估計少扣費稅。
- 原B20已結清checkpoint（現金598.6）退出20，採已保存容量7 tape：只成7、剩13活單，應收137.86；1/9總應收217.86、B13/C2。沿原resume_orders續至1/12交割／到期：現金816.46、B13/C4，剩13到期不假完成全退。明示合成完整path含原1/12空日宣告，缺段仍拒絕。
- 跌停／容量0、或空orders：無新fill；1/12現金938.86、B7/C4。未成的外部單依原期限到期，空orders不產生原本不存在的新單。

費稅採既有整元進位；先存原始source指紋、完整input/expected與執行參數，再RUN。負例包括超賣、退出量錯、假減碼全退、非整股、錯latest、活單／應付、錯來源基底、真實重標、非checkpoint、夾BUY、超量拆單、改checked內容、交叉版本及舊0.1偷送SELL。policy edge0不強迫可交易，仍沿原NO_TRADE_BAND。

原買進費用保留在全帳，不當成新回本門檻或重扣。所有分支互斥，不加總共享現金。必要正反例與三份舊0.1完整結果回歸；不重跑舊suite或真實producer。新版本須具input不變、必要數值環境／未來隔離控制；缺資料拒算，read不重算舊結果。

70/2/其中8/真實合格0、1101期初cash_claims UNKNOWN、正式false／primary_pressure_id=null、來源0.10全部parents及圖形人工保持。不擴市場回放、來源認證、限售解除、未知期初款、R2/F或自動策略，不部署／交易／付費／對外訊息、不開代理／worktree／分支。沿里程碑自審、正常commit/push及GitHub固定SHA讀回，一般工程不需人工搬檔或Work逐輪驗收。
