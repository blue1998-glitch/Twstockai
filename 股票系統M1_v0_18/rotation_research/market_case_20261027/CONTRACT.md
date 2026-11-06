# 首個明示市場案例準備／資格接線0.1

基線74e7c8e07d9d2446376305ace68b56c76f6732f3，保留Work基線3b472ae與全部後續。只新增準備入口，不改action_ledger/資格/歷史schema/合成capital入口或正式策略。

已確認案例：1101的3/12 high25.20、4/8 close25.40與4/9 close25.10；2884的2/26 high35.50及6/22 close35.80。這是本例明示參照，非正式主壓力；普通價格比較只描述本例關係，不生成策略。B首次嚴格突破只在完整保存的參照後收盤前綴核對，缺交易日/缺報價就UNKNOWN，不補價。歷史available_at仍未知，擷取時點不倒填。

可交付能力：純prepare_case綁明示來源0.10及完整parents、保存RAW行情/日曆；各路徑共同期間、全新假想現金帳、完整共同外生觀察與成本/交割模型必須逐欄相同。只准三個已指定意圖：返回後續抱、減少A、退出A持現金。每條路徑的B時點意圖須外部明示，沒有則等待；不選勝者或產生fills。共用A進場fill須在每條路徑完整相同；全程同一opening加完整fills，不另開六月本金。

起始現金/共同起訖、逐單股數/有效價/費稅/交割日、明示成本模型、容量/交易狀態/可得時間、決策時間/截止/B意圖均由外部提供。下一日開盤若外部選用，只是明示假想模型；入口不自行採用、不估滑價或T+N。原始draft缺值原樣null，輸出AWAITING_EXPLICIT_INPUT，不能用測試參數補市場實例。

每條路徑不得覆寫opening/source/基底/共同市場/模型。決策引用的事實須在其截止內；四月不能選B六月事件。有效歷史公開時間未認證時，observations可回查但historical_signal_eligible永遠false。full source identity與decision prefix分開，後續資料改動不應改早期前綴。

完整明示輸入只沿原subsidiary_proposal_sources.study_input及subsidiary_proposal.qualify準備既有RAW ledger input並取得原資格拒算。覆蓋0.10仍INCOMPLETE，不提供數值dispatch；如出現意外無拒算的資格轉換，明確NOT_IMPLEMENTED，不能自動升資格。此里程碑沒有數值市場回放/績效/帳戶重建，不冒「完整市場回測已完成」。已保存7/1事件仍沿正式0.4父層，不因0.10頂層沒有events而當無事件。

新的現金帳明確是研究假設，不是使用者真實帳戶。0股/0既有權利只有明示新帳假設的意義，不能變成原1101期初權利已證零值；不自動將opening_claims或其他資格改VERIFIED。來源/淨分配/可知時間未知獨立列出，空events不證零事件。

先凍結input/expected/source-spec及原件指紋，再寫新入口及保存actual。必要定向驗證：原draft缺參數、完整明示模型控制的準備與原資格拒算、共同帳戶/期間/價格/容量/狀態/available_at/來源/模型錯配、四月借六月、前綴未來隔離、同opening完整fills與B意圖、unknown/缺價/空事件、不變性與純呼叫。控制中的10000現金/10股等只是不可執行的接線測試假設，不是市場研究採用值。所有數值市場回放0，不重跑舊producer/績效/suite。

1101舊cash_claims UNKNOWN、70/2/其中8/真實合格0、全部正式false/主壓力null保持；來源認證、R2/F、原未支援帳務/外部活單/信用不擴張。不抓新來源、不收私人紀錄、不部署交易。接線完成、實例尚待明示且來源拒算、策略未驗證三者分開。
