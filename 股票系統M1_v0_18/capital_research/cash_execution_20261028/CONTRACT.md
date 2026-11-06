# 明示行動接既有合成執行0.1（事前契約）

本輪只把cash_action/0.1已通過的HOLD／BUY_FROM_SETTLED_CASH接原execution.simulate及continuity.make_checkpoint。不新增策略、數量生成、價格／費用／風險公式、會計或來源認證。公開純API `cash_action_execution.execute(request)`，輸入capital-cash-action-execution-input/0.1，輸出capital-cash-action-execution/0.1。無IO、CLI或新READ工具；固定既有完整標準50位Decimal Context。

## 必要明示輸入

頂層exact欄位schema、synthetic=true、action_input、checked_action、expected_checked_action_id、execution_spec。

action_input是完整原cash_action輸入；checked_action是完整保存原結果（research及source_integrity_metadata都要），expected_checked_action_id是其完整fingerprint。不能只給候選ID、core feasible、股數或不含metadata的摘要。核schema／原輸入fp及完整結果fp，再沿原evaluate核**整份結果相等**，包含外層batch gate、原帳／latest／fact歷史及全部token；不重新生成或挑選候選。這是明示RUN的必要重驗，不冒純READ；hash只證內容一致，不證來源真偽。

只有原status=CURRENTLY_FEASIBLE、intent.feasible_for_research=true、唯一candidate_ids等於原evaluated_plan_id且正式旗標仍false才可接執行。遭拒、UNKNOWN或未支援行動，即使原core單獨可行也在simulate之前STOPPED_ACTION_GATE。原結果內容遭改寫、錯輸入／完整ID則INPUT_ERROR。無原件就不推導或補算oracle。

execution_spec exact欄位id、origin_ledger、ledger_close_proof、orders、tape、observed_until，皆外部明示。calendar及報價來自原ledger，不能猜交割、補價、填第一筆容量或把真實RAW改標synthetic。origin所有sources必為ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET，標準原synthetic close proof必在。資料／填單細則委派既有引擎。

CHECKPOINT來源須精確原origin_ledger及原close proof，不能重開本金、延長原窗或改父帳；previous由該checkpoint的latest完整decision取得，cancelled_order_ids空（外部活單續播未支援）。DECLARED_SYNTHETIC_OPENING須完整相同opening現金／實股／權利，非連續資本證明。原成本與帳估值仍沿原engine核對。

## 明示委託與執行界線

- HOLD必須orders=[]；不假賣A，不清其他股或權利。
- BUY只接受適用code的正整股BUY單，總量不大於原additional_shares；同股拆單也須共同核量。不能透過SELL、別股、同股相反單、改family/targets/decision_input或額外reassessments繞外層。允許明示少量或空orders，不自行補齊差額或假定下單。
- 原單八欄id/code/side/shares/limit_price/decision_at/submitted_at/expires_at沿既有契約；有效期、限價、費稅、預留、容量、漲跌停、證據失效、途中共同風險與交割沿simulate處理。tape只能是原窗口內明示觀察，observed_until在決策後且為合法日終；缺行情仍缺，不提供1/13。
- 原已知未來失效宣告按當時可知時間生效，不回頭取消已合法成交。原單部分成交、未成、失效／取消、到期及剩餘量原樣保存；活單及預留可留checkpoint，但新入口不聲稱已支援它的不中斷再次回放。

## 輸出、連續性與保存

保存完整checked_action綁定、job、原execution、完整checkpoint及execution_calls；將原決策ID與engine返回的decision_id／decision_records精確比對，不因重新調用core而更換資格。原opening、已接受fills、order_history、全部fact_sources/reassessment_attempts、latest及全部token沿原engine傳遞。checkpoint可交既有account_at_checkpoint/cash_action續接，只在原已支援狀態下通過。

原結果與每個新輸入／expected先另存，再執行。完整來源／request/tape/job/結果指紋放integrity；可知數值投影另列decision/fills/new-fill IDs/order states/events/risk/ledger/checkpoint state。未來原ledger尾段改變不應影響較早投影，完整來源ID可不同。READ只讀新JSON，不以本輪source重跑舊證據，不遷移舊schema。

結果REPLAYED_EXPLICIT_ACTION只證所提供合成job已由原引擎執行，不等全部買進完成或可算市場績效。拒絕／輸入錯／原未支援分開；策略、winner、ranking及全部正式旗標仍false/null。沒有任何真實交易、真實producer或市場數值回放。

## 有限驗收

使用已保存明示合成input/checked結果：現金首次B、保留A買B、A已退出後買B、HOLD等原權利到位、新獨立觸發A重入。所有正例在原1/12截止前取外部明示委託／tape；較晚決策不補1/13。另存B7／剩13活單、到期／撤銷13、漲停／容量0不成交、空orders無自動建單。反例包含外層遭拒但core可行、改原結果／輸入、超量拆單／錯股／SELL、重設origin／clock、缺日曆或真實來源。核原資本／reserve／逐筆現金／權利／latest／所有token，不只核終點。未來prefix、標準與惡劣Decimal context、全部輸入及舊source不變作必要控制。

本輪不跑整套舊suite／九路徑／市場六方案、producer／資格重算、UI／Android／樣本外，不補1101期初cash_claims UNKNOWN。70／2／其中8／真實合格0、來源0.10與全部parents、正式action_resolution0.4、主壓力null、正式false及原未支援保持。R2/F、來源認證、原外部活單／期初應付完整重播不擴張。Work原件／Astra／救援未讀保持。唯一Codex沿里程碑正常保存及GitHub固定SHA讀回，不開代理／分支／worktree。
