# 續播結清後接明示行動 0.1（事前契約）

本輪只驗證現有 `cash_action.evaluate` → `cash_action_execution.execute` 能否直接承接已保存續播 checkpoint。不新增產品入口、會計、策略或協調器；只有 actual 證實產品缺口才最小修復。原唯一 Codex、原工作區與分支，最低基線89df50bc5f5a2a044585938a3976e723b2c5108e；所有原件與未提交成果保持。

## 已有原件只 READ

- `standing_orders_20261028/controls/expired-to-Jan8/actual.json` 的完整checkpoint：1/8 16:00已結，無活單／應付；A0/B7/C2，已結現金858.86，一般reserve100，原現金權利80及C2股份權利仍在，原本金1180。原B20已成交7，剩13到期；不能復活或當新批。
- 決策template、成本、風險、研究policy及新獨立B-step2，重用 `cash_two_rounds_20261028/cases/independent-B20/input.json`。1/8 17:00決策，截止1/8 16:00；只將帳戶來源改為上述完整checkpoint與精確latest，不手填account／tokens，不重新生成原結果。
- 執行spec沿該已存input的原ledger、close proof及1/9 A/C/B tape全文；窗口止1/12。原origin與close proof必與續播checkpoint相同，不補行情或另開本金。新B20及其委託參數均沿舊明示合成研究輸入，不是使用者的交易數量或政策。

先存精確action-input、execution-spec、expected及來源指紋，再evaluate保存新checked_action；其後才execute。完整checked結果與input身分重新核對是原RUN契約，不冒純READ。原續播與原兩輪producer均不重跑。

## 兩條互斥正例

1. **HOLD**：外部明示不新增股數／委託。執行spec.orders=[]，原tape與原窗口保持；原已成交B7、到期剩13及其他資產／權利不變。1/12現金938.86、B7/C4；無新fill。HOLD只代表本次保持實股，不是永久持有政策。
2. **新獨立B20**：ADDITIONAL_BATCH、B-step2；沿原完整資格／資金／成本／風險／事實及token閘門，使用原新單 `second-B-buy`，不是續成交已到期的13。預期成本20×20.02＋費1＝401.40；1/9已結858.86、應付401.40、嚴格可用457.46（一般reserve100另列）；1/12現金537.46、B27/C4。原本金1180保持，當期淨值1178.86不能重設成本金。9舊token保留，新B-step2的3個token加入；新決策與原latest精確回連。

兩分支不可相加或共用現金，無評分、勝者、正式許可或市場績效結論。HOLD當期review也可保存新可知證據，不代表批准下一筆買進。

## 必要反例與人工預期

- 舊B-event再當新批觸發：REJECTED，NO_NEW_INDEPENDENT_TRIGGER，simulate0。
- 假FIRST_ENTRY：REJECTED，FIRST_ENTRY_CONTRADICTS_B_EPISODE_HISTORY，不能因原單已到期重置首次。
- **研究邊界B40**：只有本診斷的明示假想數量，不是新規則。需801.80，小於已結858.86卻大於扣一般reserve100後的758.86，須JOINT_BUDGET_EXCEEDED_INCLUDING_COSTS_AND_RESERVATIONS；不能借原80應收。
- 錯expected_latest：INPUT_ERROR／EXACT_LATEST_PREDECESSOR_REQUIRED，simulate0。
- 改用已保存 `partial-fill-to-Jan8/actual.json` 的仍活13 checkpoint：NOT_IMPLEMENTED／ACTIVE_ORDER_CONTINUATION_NOT_IMPLEMENTED，simulate0；未完成者須留原續播入口，不能跨到新行動。

反例仍保存execute的STOPPED_ACTION_GATE及execution_calls=0，外層拒絕不得靠單獨core可行繞過。

## 驗收及界線

核完整original checkpoint留在新execution_job.continuation中，原opening／每日前綴／fills／closed order／權利／一般reserve、latest／fact_sources／重評紀錄及全部token。舊到期事件在完整前身中可回查；新execution_events按既有契約屬本job，不冒所有歷史事件已攤平。原單剩13永遠不改成已成交；只有新獨立單可新增20。

必要定向測試只檢本輪保存actual、手算逐日現金／應收應付／權利、錯誤閘門／引擎呼叫數、輸入不變與既有source保持。數值環境／未來隔離與既有ledger證據在產品source未變下重用，不為增加PASS重跑。檔案保存與讀回留在外部驗證腳本；核心不加IO。若沒有產品缺口，產品程式改動0。

1/12主例雖已結清，已到原窗口終點，不用它補1/13行情或證明新成交。真實1101期初cash_claims UNKNOWN、70/2/其中8/真實合格0、正式資格false、primary_pressure_id=null、來源0.10全部parents及圖形／人工契約保持。不擴尾段新review、未知期初應付、限售解除、外部單、R2/F、來源認證或市場回放；不部署、交易、付費、對外訊息，不開代理／worktree／分支。一般工程按既有里程碑自審／正常commit與push／GitHub固定SHA讀回，無例行Work驗收要求。
