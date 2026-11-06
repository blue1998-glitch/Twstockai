# C類已核准條件買單同單重評：交付報告

## 實際改善

舊C方案首次核准需要新的獨立觸發；其原買單等待賣款交割後，用同一有效觸發重新審查，也被當成新批，保存修前結果為`NO_NEW_INDEPENDENT_TRIGGER`。本輪明示區分「繼續同一原單」與「另外增加一批」，不換family、不移除消耗過的token。

原單只有在原checkpoint／latest／帳戶核對完成、原C/R1核准唯一、原觸發當初確為新獨立觸發且當期仍有效、原order與剩餘量精確綁定時，才獲得同單用途證明。目標只能是當期實股加原remaining，其他資產維持當期實股。新review不能增加原單數量、改觸發、改family、借別單或重開本金。

`order_review.py`只建立／驗證作用域；沒有記帳或新風險公式。當期資格、成本、已結現金與reserve、流動性、共同風險、事實期限／撤銷／衝突仍委派原檢查，實際fills及交割仍由原action_ledger入帳。遭拒宣告仍保留attempt和限制。帳戶的`cancelled_order_ids`是原checkpoint取得當期可評帳戶所需的既有接線；同單重評執行不以該標籤另造撤單或新單，保存`order_history`完全不變。

## 版本與使用

- 原輸入0.1、決策／執行0.8及checkpoint0.7路徑不變。
- 同單C入口：`capital-conditional-quantity-review-input/0.2`，輸出review0.2。
- 新決策0.9附`capital-same-order-scope/0.1`；真正出現該決策／attempt後，執行0.9及checkpoint0.8才生效。未可知的未來review不先升版早期prefix。
- 原生重評marker為`capital-same-order-review/0.1`，`resume_decision(..., same_order_id=...)`經原帳核對後重建scope，不信任外部JSON自填proof。
- 新批普通resume不取得同單豁免；即使承接0.9前身，仍需要新獨立觸發。原結果READ不重算、不隱式遷移。
- `lifecycle.py`僅增版本與保存scope結構核讀／投影，不匯入數值引擎；`lifecycle_compare.py`未改，新結果可沿原共同條件檢查並列，不評分。

## 事前輸入及實際結果

契約、13案input／expected、7個gateway規格及下一批規格先凍結於`intake.json`。第14案「未來限制到達後取消」在其執行前另凍結於`future-known-intake.json`，未修改原oracle。source原版指紋和6份source保存於`baseline-sources.json`及`baseline-source/`。

共用合成起點：A100／B5／C2、現金100、一般reserve100、現金權利80、A10股份權利，原始資本1430。原C單賣A50／買B20；B5是既有持股，不能把目標B25錯當新買25。A賣款496.500依明示日曆交割，原單B20重評後才可買。只使用1/5～1/12原合成行情，沒有新增1/13行情。

| 最終保存案例 | 實際結果 |
| --- | --- |
| valid-C-same-order | C不換family，原B-event當期重評；新token空，同一r1-B成交20，總B25；應付401.400，原資本1430保持 |
| partial-C-same-order | 原單只成交7，剩13；應付141.140，剩單reserve261.65039 |
| valid-review-but-limit-up | 資格重評通過，但漲停未買到，原單剩20，未假定成交 |
| unknown-current-eligibility／revoked-trigger | 當期UNKNOWN／撤銷仍拒絕買進，沒有同單用途繞過 |
| rejected-conflict-retained | 同ID內容改寫及限制衝突被拒，checkpoint仍保留restriction_conflicts並取消受限單 |
| current-risk-limit／current-cost-band | 共同限制／成本不交易帶仍拒絕 |
| sale-still-unsettled | 應收不當已結現金；交割未完成仍拒絕當期買進 |
| wrong-order-id／wrong-basis | 明確輸入錯誤；沒有借單、換來源基底 |
| old-wrapper-keeps-C-unsupported | 舊0.1不暗中改成新行為，維持NOT_IMPLEMENTED |
| future-revocation-prefix | 與無未來撤銷案的numeric_result完全一致，完整來源result_id可不同 |
| future-revocation-known-after-partial | 1/9合法B7保留，1/12撤銷可知後取消13；現金535.360、A60/B12/C2，權利只交付一次 |

`after-checkpoint-fix/summary.json`列14案全部符合原預期。`gateway/`另保存換family／trigger、超量、錯帳戶／前身／checkpoint／單的7個拒絕輸入與actual。`new-batch-final/`於原視窗1/12日終精確接續：同舊觸發提議新增1股仍拒絕；獨立新事實可行，僅驗資格，沒有新批委託或成交。未增加行情、原opening或本金。

## 必要測試與診斷

本輪實際執行13個唯一unittest方法。首批13次有11通過、2失敗，原因為新checkpoint已標0.8，ID卻仍用舊0.7標籤計算；READ正確拒讀`CHECKPOINT_ID_CONFLICT`。只修正產生ID所用schema，沒有放寬reader或斷言。失敗log、修前source和原測試完整保留於`tests-final.log`及`diagnostics/`。

修正後更新本輪14案actual及下一批證據，只重跑5個受影響方法，均通過：帳／權利／latest／token與READ、fresh-process無引擎／寫檔READ、新批新舊觸發、公開API輸入不變、舊E0.8及舊摘要逐值相容。其餘8個方法首批已通過且修正未改其判斷；不為增加PASS重跑。合計18次方法執行、13唯一方法，不能寫成18項新測試；合成案例和gateway不是額外唯一測試數。

測試檔與原斷言只差本輪新actual目錄名稱；舊E／舊摘要仍讀其原after-final。`source-versions-final.json`綁最終source／測試／必要讀取；`self-review.json`核事前bytes、保護舊結果與來源及敏感內容。READ文字入口只是現存actual投影，不是額外producer執行。

最早fixture準備把`single_name_value`誤寫為`single_value`，在任何case執行／source修改前即停止，未更改oracle。該診斷當時存於相鄰歷史目錄下的新路徑`../conditional_quantity_review_20261026/c_order_review_20261026/diagnostics/intake-preparation-error.json`；本輪保留原路徑，不搬移或覆寫歷史。這是本輪相關新增診斷，不是舊交付內容變更，也不是新增測試方法。

## 界線與下一步

只支援本地回放中一張已核准、待條件重評的C買單；多活單、外部既有單不中斷承接、期初應付／無來源限售解除等原未支援仍拒絕。不支援把部分成交且尚有應付的帳戶直接當新輪期初；本輪保留其actual，未擴大該能力。完整分叉／更正／來源認證矩陣及原job到保存execution的通用因果認證未完成；純READ不冒稱可驗證任意偽造資料。

未執行舊整套、九路徑、真實producer、資格重算、市場六方案、UI／Android或樣本外；沒有策略、比例、門檻或市場績效結論。1101期初cash_claims UNKNOWN／拒算、70拒算／2不足／其中8換股影響未支援／真實總淨合格0、所有正式false、主壓力null保持。正式action_resolution0.4、來源0.10與parents、圖形／人工契約及原帳務source不改。Astra及第一工作區救援原件仍未取得未讀。

本功能重要額外複核集中於：同單scope不能批准新批、原單量及token、原帳權利／reserve／latest、未來限制可知時點。一般工程由原唯一Codex自審交付，不預設逐輪轉Work。最有價值的後續是將本輪保存的C重評／等待控制以既有共同條件入口直接列成使用範例，先核同市場與同原帳；只讀、不重跑、不評分或選勝者。本輪不另開該工程。
