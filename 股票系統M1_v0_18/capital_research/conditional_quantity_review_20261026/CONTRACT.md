# 原數量條件單重評接線 0.1

基線5783899309e6fd9bba5d05eb7c697c3f12e0b11b。本輪只有一個純合成接線能力：對quantity_replay/0.1最後一輪已通過完整外層數量閘門、仍待資金重評的本回放B買單，使用新的當期帳戶／證據重評後續用同一單。沒有新批次、比例、最優選擇、委託生成、第二帳或正式資格。

## 輸入

`capital-conditional-quantity-review-input/0.1`固定欄位schema、synthetic=true、replay_input、review。

- replay_input是原quantity_replay/0.1完整明示輸入；最後一輪須含原合法買單及明示tape／最終observed_until。禁止注入外部checkpoint、任意account、raw plan或原生reassessments。原回放仍先核完整外層閘門。
- review固定id、order_id、decision_template、policy。template是原0.8決策輸入除account／plans；必有新decision_at、data_cutoff及當期證據資格審查。帳戶、latest、checkpoint、全部tokens、原單與剩餘量只從原回放實際prefix機械取得，禁止自填。
- policy固定version、parameter_source、available_at、edge_budget，必為當時可知的明示合成研究預算；不是預測報酬。
- review切點須在最後一輪原決策後、最終觀察前的明示合法日終；review在切點後且首個適用B observation前。原日曆、close proof及原生prior-close／可得時間檢查繼續生效；不補1/13行情。

## 閘門及重評

先把最後一輪observed_until限於review.data_cutoff，委派原quantity_replay生成完整數量候選及原execution，再用原make_checkpoint取得真實帳。原請求與數值prefix分開保存；不修改任何原件。

限本次回放最後一輪新建、仍requires_reassessment的B買單。須為唯一活單、未到期未撤銷、剩餘量正數且不大於原單／原候選核准量。首次限原方案B或E；family C追加單續評、非待條件重評舊單、多活單及外部活單明確未支援。這不是將C改E：原family／route／trigger保持，無family override。

當期提案由原plan複製，所有資產target=當期實股，僅原單B target加上原單remaining；沒有提高原數量、重建賣單或退出其他資產。edge只來自明示review policy。原source／basis／adjustment及cost模型不容靜默變更。原生resume_decision檢查當期新資金資格、成本、資金、reserve、流動性、共同風險、事實歷史與tokens。有效舊事實原ID／內容可當期review，不能變新獨立事件。

用原生reassessments保存與執行：既有cancelled_order_ids的內部重評語義由唯一活單機械綁定；原引擎在接受後仍以同一order ID及原限價／到期／remaining續用，沒有撤單重下或新order ID。未通過或仍未結清，原引擎保存REJECTED attempt及限制，不能只回傳零成交而丟掉宣告。新批次仍須走原quantity候選完整閘門，不能借此入口建單。

## 輸出及停止

`capital-conditional-quantity-review/0.1`保留prefix execution／checkpoint state、原數量核准身分、精確原生review與當期decision、原生execution及最終checkpoint摘要。原帳opening／fills／權利／reserve／latest／完整token沿原引擎回連。輸出checkpoint摘要不是新的任意resume API。

狀態區分REPLAYED_ACCEPTED_REVIEW、REPLAYED_REJECTED_REVIEW、STOPPED_ORIGINAL_GATE、STOPPED_INPUT_ERROR、STOPPED_NOT_IMPLEMENTED、STOPPED_EXECUTION_REFUSAL；錯誤不fallback、不新造委託、不當作成功零成交。若截止後的tape導致原生checkpoint不符，保留拒絕，不拼造帳。

來源完整性指紋與當時數值比較分開。正式資格全false、主壓力null、ranking=null。只證合成機制；1101期初cash_claims UNKNOWN／拒算及70／2／其中8／真實總淨合格0保持。R2/F、信用、期初應付、不中斷外部活單、來源認證、自動解除衝突與完整分叉矩陣不擴張。舊READ不重算／遷移。
