# 隔離研究修復契約0.3（未提交）

固定Git基線與最新已核遠端仍為 `6be4333d490bcccfe952c7606dffb802b76cdd5c`。新決策／成交／比較輸出0.3、checkpoint 0.2、trend／trend-policy-competition 0.2；原action_ledger 0.1完全不改。舊0.1／0.2輸入、保存結果、契約及log不移轉、不重算；原0.2 source／文件／證據另有逐檔快照。JSON傳輸外殼仍可標原input/0.1，但0.3研究執行必須通過下列新資格profile，舊欄位缺少資格不能默認可投入資金。

## 每股新資金資格

`assets[code].capital_eligibility` 為 `capital-entry-review/0.1`：code、source_id、basis_id、adjustment_version、source_ids、evidence_ids、status、data_cutoff、assessed_at、available_at。status只准QUALIFIED_SYNTHETIC_RESEARCH／NOT_QUALIFIED／UNKNOWN。review截止必精確等於本次data_cutoff；cutoff≤assessed_at≤available_at≤decision_at；同股同源基底版本，明示非空且唯一evidence_ids均須在當時已知事實中。缺失、尚不可得、舊截止或未合格均不准增加該股目標。

`layer2[code].capital_eligibility.qualified_for_synthetic_proposal`只表示上述合成提案資格，不是data_qualified或任何授權。每個正股數變動都另外檢查；NOT_QUALIFIED不能只作顯示標籤。續抱、風險降低與新投入分開。被拒方案不列research_recommendation；零交易觀察控制仍遵循原限制。沒有不合格買進的隱藏控制模式。

## 有效舊事實、到期與失效

事實、entry_context及正式參照可附`capital-fact-validity/0.1`：available_at、valid_from、valid_until、invalidation、source_ids、qualification。已知明示的EXPIRED／INVALIDATED不得由新decision_id或新review復活。有效舊事實仍可由當期review引用同一ID，不強迫新事件，也不把它重新當獨立trigger。

valid_until可為來源明示截止；null必須明標EXPLICIT_SYNTHETIC_ONGOING_REQUIRES_REVIEW，且新投入仍需當期review，不等永久有效或無限合理空間。沒有有效期資料是UNSPECIFIED，不能補成合格。沒有任何固定有效天數或交易門檻。

invalidation另有evidence_id、occurred_at、available_at、source_ids。只處理決策時已知的失效；未來撤銷不進當前decision身份。完整原輸入保存，不改寫原件。明示到期與當時已知失效會取消仍未成交買單，即使限價內；已合格且持續有效的舊單仍可在期限內執行，不因每個觀察自動要求新決策。條件式等待交割買單仍必須有新decision與checkpoint。

## 日終可知證據

execution job新增`ledger_close_proof`，schema=synthetic-ledger-close-clock/0.1、qualification=DECLARED_SYNTHETIC_DAY_END_NOT_REAL_MARKET_OR_BROKER_PROOF、closes[date]={as_of,available_at,source_ids}。只有明示engineered來源可用；不產生真實收盤或券商交割證明，不推真實T+2。

opening、observed_until及checkpoint的as_of必精確匹配明示日終。不能以09:00標記重播出的整日日終帳。available_at≥as_of；可能延後可知，下一decision必已到available_at，執行時使用的前日帳亦須已可知。checkpoint可作離線保存，但可知前不能供下一帳戶決策使用。日終時間、可知時間與decision_at分開。

## 最新前身與連續帳

新execution同時保存origin_common_account_id、當輪起始decision_id/common_account_id、latest_decision_id/latest_common_account_id、完整decision_ids／decision_records及reviewed_evidence_tokens。decision_records逐筆驗指紋與時間順序；下一輪必精確承接最後一筆decision，不能只檢查出現在歷史清單。重評後亦沿同一身份鏈接續，所有已看token累積。

checkpoint 0.2仍由原ledger opening及全部accepted fills重播。新fill_order_ids把每筆成交精確連到歷史委託，整數原數量=成交量＋剩餘量；驗證不受呼叫者Decimal精度影響。取消／到期保留剩餘量與歷史，只釋放委託預留；一般reserved_cash獨立承接，不可無聲歸零。現金、應收應付、持股、股份權利與原始資本仍只有原action_ledger入帳。

opening_unavailable_shares保存原始不可賣量。當存在未有來源解除的可賣限制，本版明確SELLABLE_LIMIT_CONTINUATION_NOT_IMPLEMENTED；不把實股全部升成可賣，也沒有新增解除限制引擎。買進應付未結清與不中斷外部既有單完整重播仍拒絕。舊結果可READ，不能自動升級成新checkpoint。

共同市場身份另綁完整ledger_close_proof；原價格、容量、交易狀態、available_at、來源基底及交割路徑綁定保持。新的同路徑正反變體只改明示新資金資格，不是市場樣本或R1/R2勝負。

## 邊界

全部data_qualified、execution_model_qualified、historical_signal_eligible、policy_authorized、live_execution_authorized=false。主壓力未知仍null，不造參照。R2/F、信用借還款、期初應付、外部既有單無縫重播、無來源限售解除及實現曝險配對未實作。原70拒算／2不足／8換股影響未支援／真實總淨合格0保留；所有正式來源、parents、原件與歷史不改。沒有正式策略、圖形、UI或schema遷移。
