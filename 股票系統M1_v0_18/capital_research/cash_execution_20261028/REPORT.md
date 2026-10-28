# 明示行動合成執行0.1：交付與自審

最低基線5dd3aab979d5442486442344b8e8ff476e2b75d8，本輪開始本地／遠端同此SHA、無差異。只新增cash_action_execution.py與本目錄及既有五處進度增補；原cash_action、core、execution、continuity、ledger、quantity、fact及②原件不改。所有祖先／歷史與未支援保持。

## 新增能力

完整明示行動回條現在可受控送入原合成simulate；不重建引擎、不猜量、不新建單。綁定完整原結果fp＋完整原input fp，原evaluate重新檢核全部回條；外層批次拒絕不因core可行而執行。偽造外層批准、改metadata的reserve、改輸入量、錯完整ID均在simulate前拒絕。此為RUN重驗，無新增READ或來源認證。

新job由已核derived decision_input、原evaluated_plan_id、外部明示orders/tape/clock/window及原origin組成；不接受任意plan、family、continuation或reassessment。CHECKPOINT的完整原ledger／close proof必相同、latest由records取得；初始假想現金帳須完整相同opening權利。原執行返回的決策ID及完整decision要與已核原件相同，才建原checkpoint。

HOLD無委託；BUY只適用股、正整股、總量≤原additional_shares，拆單共同核量。明示空orders不自動產生買單。限價、費稅、容量、未成交、證據失效／撤銷、風險、交割與預留全部沿原引擎。沒有來源變更、真實市場回放、正式交易或策略批准。

## 已保存actual及必要驗證

27份新有限請求／手定oracle在新source前凍結，snapshot及frozen保存。舊完整檢查結果直接重用；只有4個新合成變體用舊evaluate準備回條，非舊suite重跑。27份actual JSON保存後全文讀回相同，狀態／理由符合原預期；7唯一方法、7次首次全過，不累加27案、準備／控制或舊PASS。

原A持100仍用現金買B20，A不假賣。原A全退出分支沿同opening2180／reserve100、原A賣100成交與995應收：1/8現金1000、應收1075（995+80）、C2及另C2權利；1/9買B20後仍現金1000、應付401.4，嚴格可用598.6；1/12才現金1673.6、B20/C4、應收／應付0。逐日NAV權利對帳及每筆原fill/order/link確認，不只看終點。原始資本2180不變，初始現金假想帳另外明示1180，兩者不混同。

部分B7於原模型價20.02、費1，應付141.14；1/9現金1000、available858.86、一般reserve100、剩13原單reserve261.65039各自保存。若到1/12到期或1/9中午可知撤銷，B7不回頭消失，剩13關閉且reserve0；取消事件at12:00與observed_at13:00分開。漲停／容量0沒有新fill，原款及C權利照帳到位。新A獨立事件才重入A20，family C／舊token保持。空orders不補單、不虛構成交。

缺來源、錯原帳／clock、超量拆單、SELL或HOLD夾單等拒絕均有保存actual及execution_calls=0。虛構full hash不證批准，完整body與原evaluate不同仍拒絕。已結清新checkpoint再接既有HOLD通過，仍沿原資本／latest／全部token；部分活單與應付不能繞成新opening。此回連另存test-evidence，不冒新增市場逐輪樣本。

未來原ledger尾段價變動的較早numeric_result全文相同；全來源ID分開且不同。既有惡劣Decimal與正常控制全文相同，input/caller/DefaultContext保持；禁IO／網路／quantity生成／quantity_replay控制通過。原simulate及ledger呼叫必要，不稱全引擎0。

## 診斷及保全

準備手算只在partial-active案把available858.86錯寫成settled_cash。原input/expected/frozen全留；另存diagnostics/pretest-cash-role-correction.json，依原action_ledger daily欄位及BUY先建應付、到交割日才扣cash的程式規則，列獨立算式1000－141.14＝858.86。正式方法執行前已記錄，不改引擎或27案的狀態／理由，也不把應付靜默補0。其餘全部手定現金、股數、剩量／預留預期相符。

原來源及source版本、frozen bytes及舊有效根文件歷史保留；本輪無程式修前失敗或重試套件。保存採既有里程碑正常commit/push、GitHub固定SHA逐檔讀回，不強推、改main、bootstrap、開代理／分支／worktree或發訊息。最終SHA由對話回報，避免自指提交循環。

## 未完成／未測／資料不足

- 未實作：本入口的新批多輪協調／不中斷舊活單承接、期初應付／限售釋放完整重播、八行動dispatcher、整張域／多股最適化、R2/F、來源認證與自動解除衝突。
- 未測：0.9同單及0.8 checkpoint的複合完整矩陣、任意多分叉、更廣資產／來源模型；沒有因此宣稱全面帳務認證。
- 未執行：舊suite、九路徑／市場六方案、真實producer／資格重算、市場數值回放、績效排名、UI／Android、樣本外；外部真實交易0。無新資料擷取／1/13行情。
- 未解除：1101期初cash_claims UNKNOWN、來源0.10與全部parents、70拒算／2不足／其中8換股影響未支援／合格真實總淨0。所有正式false與主壓力null不變，未把RAW改標synthetic。Work原件、Astra及第一工作區救援原件仍未取得／未讀，不猜其存亡或要求搬檔。

## 下一步分工

本里程碑已完成「明示行動→原合成執行→原checkpoint」。後續若要證明多輪可用性，最小已知工作是使用本輪**已結清、無活單／應付**checkpoint，將下一項外部明示行動再接同一原帳與原窗口；先確認既有evaluate/execute是否已足夠，只補實際缺口，不擴活單／應付帳務，不延長市場原件。此屬Codex既有規則接線；沒有必要為新READ或並列工具另起里程碑。

真實②市場的N、股數、比例、風險／政策、共同期間與成交模型仍需Work／使用者研究及來源資格，合成成功不能代替其批准。無人工操作或Work例行工程驗收需求。
