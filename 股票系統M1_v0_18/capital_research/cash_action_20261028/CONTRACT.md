# 明示現金行動受控接線0.1（事前契約）

本輪只補能力核對第2項的有限決策接線。公開純API `capital_research.cash_action.evaluate(request)`，輸入 `capital-cash-action-input/0.1`、輸出 `capital-cash-action/0.1`。只支持明示合成；不把②市場RAW改標合成，不開市場回放，不接quantity_replay或生成委託。所有數量／edge／政策均為外部明示，沒有本金N、比例、天數或預設勝者。

## 原帳來源及範圍

`account_source`二選一：

- `DECLARED_SYNTHETIC_OPENING`：明示account與consumed_evidence_tokens；不是連續帳證明。必須是明示假想起點，不能把checkpoint改成新opening來消除歷史。此介面不能認證外部申報真偽。
- `CHECKPOINT`：完整現行checkpoint及expected_checkpoint_id、expected_latest_decision_id。驗原ledger/fills/歷史／close，再沿account_at_checkpoint取得當期原帳；精確latest從execution.decision_records取得，不收手填account、previous或token覆寫。原opening與原始資本不改。只支援無活單、無期初應付的日終續接；不可賣限制的跨輪仍沿原拒絕。closed orders及全部已審token／fact sources沿原resume_decision回連。未支援狀態拒絕，沒有取消／重放舊單的效果。

`decision_template`沿現行decision契約，但account、plans、consumed_evidence_tokens由入口綁定，禁止覆寫。資料截止必等原帳as_of；決策及證據／來源／模型可知時間沿core。只接受SETTLED_CASH_ONLY，不增加信用或會計能力。來源／基底／調整版本不得相對checkpoint的latest資產身分改變。

## 明示行動

一次一項 `action`，必要id/kind/code/additional_shares/trigger_ids/batch_context，不收family、任意targets、orders或tape。

- HOLD：code及batch_context=null、股數字串0、trigger_ids空；沿原A-zero檢查。保持所有實股及完整權利；即使A為0仍不冒稱全帳持現金。
- BUY_FROM_SETTLED_CASH：明示適用股票及正整股增量，其他股票的目標完全不變，沒有假賣A或拿應收當可用現金。這是新批意圖，不續用原單，不實際扣現金／預留／token。

買進batch_context沿quantity_candidates現行契約；account_id/origin由入口取得，不能外部覆寫。FIRST_ENTRY沿原首次歷史檢查，不能用退出後A=0或新review冒稱首次；有效舊事實可當期審查。ADDITIONAL_BATCH固定family C，核本股明示新獨立觸發、全部token、同量柱／形成點依存及原fact_history。UNKNOWN不放行。已知失效／撤銷／限制衝突沿core/resume，不自行解除或清除。首次不接受被靜默忽略的trigger_ids。

`policy`必有version、parameter_source、available_at、edge_budget，與當期可知時間核對；數值為假想外部研究預算，非預期報酬。所有費用、可用額、流動性、共同風險與權利估值委派既有core，沒有新資金公式或第二帳。

## 輸出及不變性

輸出含明示intent、derived decision_input、完整原core_result、共同帳身分、原checkpoint/latest/origin/fills/closed-order/token綁定；分類CURRENTLY_FEASIBLE／REJECTED／NOT_IMPLEMENTED／INPUT_ERROR。分類是候選資格，不是選擇、委託、成交或策略批准。沒有等待應收自動買進：此行動不賣資產，資金不足即原core拒絕。保留core原始評估與外層gate理由分列，避免外層拒絕卻把core可行方案當合格建議。合格candidate_ids僅輸出本入口通過的意圖，無winner/ranking，正式false／主壓力null。

完整輸入指紋與數值研究結果分開，未來未可知證據不改當期研究結果。固定完整標準50位Decimal Context，caller/DefaultContext及全部input/原checkpoint不改。帳務呼叫僅為既有checkpoint驗證；不呼叫simulate、quantity產生器、回放協調器或IO。舊結果不遷移／重算，舊0.1/0.2情境及原引擎不改。

## 事前驗收

保存手定正反例：假想現金首次B、原A仍在且用既有現金買B、已退出A後B首次、A新獨立觸發重入、有效舊事實review、舊／共柱／跨股觸發、假首次／UNKNOWN／失效、原reserve及應收不充現金、成本／風險／流動性、錯latest／checkpoint／帳覆寫、活單／應付／不可賣限制、來源／基底／RAW拒絕、未來prefix與數值環境及input不變。準備用三份明示合成原job產生現金持有、A退出未結、A退出已結的checkpoint；另保存部分賣出活單反例。不跑整套舊suite或市場回放；只計新唯一方法，precondition不是新市場樣本。

來源0.10/全部parents、正式action_resolution0.4、70/2/其中8/真實合格0、1101期初cash_claims UNKNOWN、原false/null及未支援皆不動。R2/F、來源認證、完整分叉／自動解除衝突、外部活單／期初應付完整重播均不擴張。Work原件／Astra／第一工作區救援原件仍未取得未讀；不要求使用者搬檔。
