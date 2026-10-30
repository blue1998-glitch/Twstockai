# 拒絕重評的限制收件契約 0.7

只為隔離合成研究，不修改正式策略、圖形或action_ledger。

1. `capital-execution/0.7`新增 `reassessment_attempts`，累積而非每輪重設。每項schema為 `capital-reassessment-attempt/0.1`，包含id/order_id/observed_at/outcome、完整候選decision、原fact_source、plan_id/checkpoint_id/cancelled_order_ids，及內容指紋attempt_id。
2. 接受／拒絕只有在原流程精確核驗checkpoint與candidate decision_id後判定。`ACCEPTED`依現有流程進入accepted history。`REJECTED`保留事實、候選結果與audit，不替換latest，不實際執行候選取消清單、不當成可交易授權。
3. `capital-fact-receipt/0.1`包裝遭拒來源，包含received_at與原source。`capital-fact-history/0.3`的開始可知時點為max(宣告decision_at, received_at)，其未來撤銷仍須同時滿足occurred／available；原raw bytes不因投影而刪除。
4. 拒絕來源仍走既有root／scope／內容／限制衝突規則。UNKNOWN不是受認證的來源更正；精確舊bytes或新review不能消除已知限制衝突。
5. 原有買單在同一次收件觀察、資金預留與成交前檢查限制。對scope與accepted body相同的原單，單純拒絕改寫不等於取消原件；accepted root的過期、撤銷、未知身分、其他拒絕原因及限制衝突仍可擋單。候選decision資格仍使用未放寬的正常fact issues。
6. 所有已review token包括拒絕提案都完整保存、帶入下一輪；不用拒絕提案替換最新有效前身。token保存不代表新事實有效或已交易。
7. checkpoint 0.6核驗原execution 0.7、attempt與候選指紋／重建歷史／前身、收件watermark、事件引用、原fills／委託／reserve／權利。不得另建資金帳、改opening、以候選帳取代原帳。
8. decision／comparison為0.7；歷史JSON READ不匯入engine重算、不隱式遷移。舊0.6execution／0.5checkpoint可讀，但拒絕作本版新續接證明。所有正式與來源資格維持false，主壓力null。
9. 接受重評沿原先決策時點語義；本輪新增的receipt gate針對遭拒宣告，不宣稱已建構通用非同步外部消息系統。未送達／身分不明／不支援來源更正保持拒絕、未知或未實作。

最小反例、正例、時間及部分成交證據見REPORT、before-final／after-final；精確方法見verify。沒有市場績效、最適策略或完整分叉認證。
