# 第一階段輸入輸出契約

所有例子必為 `synthetic=true`。精確金額／價格／股數用十進位字串，有限值，股數整數，50位Decimal；拒絕float、NaN與缺失。帳務仍由不變的 `rotation-action-input/0.1`／`rotation-action-ledger/0.1`處理。新契約沒有寫入任何舊schema。

## 決策輸入 `capital-decision-input/0.1`

- `decision_at`、`data_cutoff`、`policy_available_at`：帶時區。截止≤決策，policy/cost/risk/scenario/execution模型可知≤決策。來源列須發生≤截止、available≤決策才可進決策。整檔來源指紋獨立在 `source_integrity_metadata`，不作後見選股或比較數值相等的要求。
- `assets[code]`：source_id、basis_id、adjustment_version、group；marks保留price、occurred_at、available_at、reference_role。必須有唯一精確截止mark，不補價、不沿前價。
- `evidence`：各自id、feature、stance、value、來源綁定、發生／可知時點及formation_id／event_id／volume_bar_id。feature固定為price_volume、box、key_position、momentum、cross_scale，支持／反證／未知分列，無綜合強度分數或機率。空白feature列未知。
- `entry_context`：獨立position、formal_reference、invalidation_risk、liquidity_shares及可知時點。正式參照若無則null、合理空間null。已明示參照只計價差，不當保證報酬／目標。未知或錯基底不得補近期高點。
- `account`：as_of、available_at、每股shares及sellable、settled_cash、reserved_cash、cash_claims、share_claims、payables、pending_orders。包括顯式0與空清單，不能省略未知權利。待買委託用有界limit_price與含成本reserved_cash，待賣鎖股；帳戶已結額減保留／應付／待買預留才是可買現金，應收不加進去。
- `risk_limits`：單股／群組幣值、帳戶共同情境損失、max_trade_shares。股份應收也計風險，待買以全數成交壓力計；不是正式風險參數。停損或失效線不保證成交價，沒有保證最大損失。
- `cost_model`：有版本／可知時點的fee_rate、minimum_fee、sell_tax、slippage_bps。沿用原fees整元向上取整；有效成交價含明示滑價。純研究假設，不是使用者券商費率。
- `execution_model`：版本、available_at、SETTLED_CASH_ONLY或BROKER_CREDIT_RESEARCH。後者必有另列broker_credit qualification=EXPLICIT_SYNTHETIC_TERMS、source_id、version、available_at、limit；不改已結現金、不拿應收直接當可用款。
- `scenario_set`：決策當時已知為假設的共同prices情境及版本／可知時點。沒有將未來實現路徑當成估計分布。`policy_version`、`parameter_source`、no_trade_buffer、edge_budget都是合成研究參數；不是使用者門檻。edge_budget不是強度分數、勝率或已校準期望報酬。
- `plans`：共同id、family A～F、route R1/R2、每股精確targets、trigger_ids、edge_budget、conditions。A-zero總會列出；風險超限可標不可行但不刪除。C必有未看過且無共用形成點／事件／量柱的新trigger，不預設批數比例。E共同預算含原股、新候選與餘現金。F或R2保留NOT_IMPLEMENTED。

`allocation.full_transfer` 為R1的B提案器，減去原股後保留其他既有持股／權利，有限降序枚舉最多20,000個股數變動，選通過同一可行性檢查的最大整股數。成本／風險／流動性可使餘現金大於0，仍可能待交割；超出有限範圍拒絕，不冒完整求解器。一般plans亦可表達外部B/C/E提案，其數量不是最適比例證明。

## 決策輸出 `capital-decision/0.1`

`decision`包含decision_id、完整時點／版本／共同情境與資本、共同account指紋、layer1、layer2、layer3。layer3各候選含targets、預估成本／買進應付／賣出應收、可用現金、獨立券商額度、結清後現金估計、資金等待條件、風險／流動性拒絕原因、被支配／無法區分ID、觸發／取消／重評條件。

可行性是研究模型條件式結果，不是委託／成交。共同情境Pareto只在同帳同情境下作比較，不使用綜合分數、機率或自動勝者。小優勢≤估計摩擦＋明示buffer時可不交易；若所有風險違反均不增且至少一項下降，降低風險不被此區間擋住，剩餘違反仍明列。方案買款若須售股交割則 `WAIT_SALE_SETTLEMENT_AND_REEVALUATE`，不是現金已到。

`research_recommendation`只列可行且未被共同情境支配的待檢視集合；data_qualified、execution_model_qualified、historical_signal_eligible、policy_authorized、live_execution_authorized**各自維持false**。primary_pressure_id=null。`source_integrity_metadata`在decision外，未來路徑改變時允許其不同；整個decision必相同。所有成本與情境皆明列版本。

`reviewed_evidence_tokens`及`new_evidence_tokens`保存相依身分。連續檢討用`resume_decision`／RUN --prior-id核前次decision指紋及時間，再帶入全部已看token。新事件／新來源版本才可重新評估；不能把同一次形成點換id重複當新證據。未使用resume而另起獨立實驗，不宣稱是連續資本閉環。

## 成交輸入／輸出

`capital-execution-input/0.1`含共同decision_input、plan_id、既有ledger_input、明示orders、chronological tape、observed_until。來源只接受ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET；既有ledger的opening須精確等於決策account的cash／shares／cash_claims／share_claims，期初估值亦核等。order不得超出所選可行目標變動，禁止同資產相反方向互抵。

order必有id、side、code、shares、limit_price、decision_at、submitted_at、expires_at。沿舊帳限制只支援前一日或更早決策、下一日以後成交。tape必有at／available_at、來源基底、price、capacity_shares、market_state、settlement_date及合成資格。可成交價不能由停損線、日高低或收盤推回；所有實際研究成交由此明示。交割日必明示在既有calendar內，不自推真實T+2／券商日內額度。

每個觀察先以原帳既有fills重播取得上一日已結可用額，減本日已接受買款及其他委託預留；賣出應收當日不加現金。委託依明示list順序共同預留，每個tape共用capacity，不是每張單各得全市場容量。漲停買不到／跌停賣不出／停牌／越限價／零容量保持未成交；部分成交只入實際股數，其餘保留或到期。缺觀察不假設成交；observed_until只用來明示逾期。

輸出`capital-execution/0.1`分orders、order_states、execution_events（精確時點）、fills（舊帳欄位）、ledger（每日帳／版本／權利）、模型版本及result_id。最終未成交不冒完成換股。NAV含現金＋應收−應付＋持股／待交股份估值；費用與滑價從原資本支付。估計終點清算成本分列，不冒實際成交。所有total_net_return及actual_realized_investor_return仍null。

**明確拒絕範圍**：券商額度完整帳務；期初非空payables；期初既有pending_orders完整訂單重播；日內決策／成交；超出舊帳能力的公司行動、重疊未入帳權利、未知淨額／畸零／缺價。前兩類的決策預算仍可盤點，不代表重播支援。不造貸款、期初fill、零權利或新現金掩蓋能力不足。

`compare_jobs`在任何回放前要求完整同decision_input與ledger模板（僅fills路徑為空），包含初始資本／權利／來源／成本／日曆／期間。相同NAV但不同權利也拒比；輸出無市場排名／合格總淨比較。

## 保存、來源隔離及失敗處理

數值core／allocation／execution／evidence無檔案／網路／資料庫IO，無現在時間依賴。cli及build_evidence才IO。沿原Journal rotation-record/0.1，READ不匯入引擎、不改檔、不選新版；已有不同內容拒絕，損壞檔保留診斷。決策、成交、帳務版本及各自時間皆保存，新增記錄不覆過去。

`evidence.from_saved_layers`只核原manual選擇與結構／reaction result指紋、來源／frame／基底／版本／as_of及顯式可知時點，再保存原輸出。它不認證真實歷史公開可得，也不產生正式entry_context。`real_source_gate`只委派不變0.10→全部parent拒算鏈，沒有新的成功真實淨帳路徑。本輪未跑該真實producer或解除舊來源缺口。
