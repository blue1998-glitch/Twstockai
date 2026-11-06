# 期初權利證據缺口檢查 0.1

本模組只檢查合成證據包的欄位、來源引用、帳戶／股票／價格基底、完整性聲明及時間一致性。不是原件認證、資格審批、資金帳或策略。沒有連到 action_ledger、來源 catalog、決策或交易路由。輸入限定 synthetic=true；真實／私人資料入口未實作。

## 輸入 opening-entitlement-evidence-input/0.1

- binding：account_id、scenario_id、currency。assets 每股保存 price_source_id、basis_id、adjustment_version；帳戶欄 scope 只有 binding，股票欄另有 code 與三個資產身分欄。不得跨帳戶、情境、股票、價格來源／基底／版本借用證明。
- as_of、data_cutoff、decision_at：帶時區的明確合成時點，as_of≤data_cutoff≤decision_at。此處使用的 16:00 等時間是 fixture 宣告，不是從真實市場或日期推導的收盤／交割規則。真實一月窗口仍沒有已核精確可知時點。
- declarations：settled_cash、reserved_cash、payables、pending_orders，及每股 holdings.CODE.shares、holdings.CODE.sellable、entitlements.CODE.cash_claims、entitlements.CODE.share_claims。未知或漏欄產生缺口，不能用預設零值補齊。
- 每欄 state 只接受 UNKNOWN／SOURCE_DECLARED／HYPOTHETICAL_ASSUMPTION，另有 value、evidence_ids 或 assumption_reason。金額／股數為非負有限十進位字串，實股／可賣數為整數。清單空白本身不證明零。
- sources：僅合成來源，kind=ENGINEERED_ACCOUNTING_FIXTURE_NOT_MARKET，sha256、available_at、captured_at。雜湊只檢查宣告格式並綁入 input_id；不讀取原件、不驗真。captured_at 不替代 available_at，也不證明歷史公開時間。
- evidence 每項有精確 field、scope、as_of、available_at、source_id、locator、declared_value。清單另需 complete_outstanding_inventory=true，表示其宣告涵蓋當時全部未結項，不等於檢查器能證明沒有遺漏。證據及來源必須在 decision_at 前已可得，as_of 與期初狀態同一時點。相等邊界可用，等價時區一致。
- 現金權利每項 id、event_id、entitlement_at、amount_net、currency、pay_date、payment_status=OUTSTANDING；支付日是宣告時程，不是實際入帳證明。未知淨額／支付日保留 null 並列缺口。
- 股份權利每項 id、event_id、entitlement_at、shares、delivery_date、tradable_date、delivery_status=PENDING。未知日期／股數保留 null 並列缺口；實股、待交股份及可賣量不互相推定。畸零權利保留並列 NOT_IMPLEMENTED。
- 權利取得時點不得晚於 as_of。起日前的未領權利，即使目前持股為零仍保留。全包權利／委託 ID 不得重複；不加總估值或現金。

## 輸出 opening-entitlement-evidence-diagnostic/0.1

每欄分別給 UNKNOWN、SOURCED_ZERO_DECLARATION、SOURCED_NONZERO_DECLARATION、HYPOTHETICAL_ASSUMPTION；有時間／身分／內容／完整性缺口者不得分類為有來源零值。

status 分為 GAPS_PRESENT／ASSUMPTIONS_PRESENT／STRUCTURALLY_COMPLETE_NOT_AUTHENTICATED。另列 gaps 及 unsupported_capabilities。非空期初應付、既有委託、畸零股份仍明確 NOT_IMPLEMENTED；形式完整不表示帳務支援。

declared_value 保存原值；只對形式一致的來源宣告提供 diagnostic_value。假想假設不升為來源證明。純函式不修改輸入；輸出指紋綁定整個輸入，包括晚到證據；不要把該指紋當未來隔離的數值決策。

固定 authenticity_verified=false、opening_entitlements_verified=false；data_qualified／execution_model_qualified／historical_signal_eligible／policy_authorized／live_execution_authorized=false，primary_pressure_id=null。ledger_called=false、legacy_qualification_updates={}；不輸出報酬、可用額度、委託、成交或現金／股份入帳。舊 OPENING_ENTITLEMENTS_UNKNOWN、catalog 及 70／2／其中8／真實總淨合格0不變。

## 六項有限驗收

1. 空清單無證明仍未知；完整來源零值聲明、未知與假想假設可區別。
2. 錯帳戶／股票／價格來源／基底／調整版本不可借用。
3. 起日前取得且未領的權利不因零持股消失。
4. 晚可得證據不能回填早期已知；淨額、支付／交付／可交易日未知不補造。
5. 期初應付、外部既有單及畸零權利未支援能力不被檢查通過掩蓋。
6. 舊 catalog／資格／拒算／程式／原件／保存結果逐檔不變；不執行舊 suite 或窗口 producer。

未完成：來源認證、私人原件接收、真實歷史可知時間認證、完整公司行動涵蓋、資格升級、實帳重播及所有原未支援帳務。此工程不能解除真實窗口拒算。
