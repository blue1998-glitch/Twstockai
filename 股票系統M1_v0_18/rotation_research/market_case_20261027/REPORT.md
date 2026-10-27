# 本輪交付與未交付

## 新增可用能力

新增market_case純準備API及獨立market_case_io外部入口，限定使用者已明示的1101返回參照、後續2884機會案例。明示來源0.10/全部parents、RAW行情快照/原件manifest/官方已保存交易日曆以完整內容身分綁定。外層IO核四檔bytes/SHA，只讀庫內資料，不重新建立catalog、抓來源或跑72窗口producer。

共同期間、全新假想現金帳/零持股/無期初權利的明示假設、成本/交割模型、完整提供的外生觀察（價格、容量、交易狀態、available_at、來源/基底）及A共同進場模型輸入逐欄綁定。路徑只能使用同一opening及完整fills歷史，不接受另一個opening或六月新本金。三意圖為返回後續抱A、減少A、退出A持現金；B時點意圖須由外部另明示，不能由工程代選。保存模型價格/股數/費稅不等於已成交或已通過資金/賣出能力檢查。

只重用subsidiary_proposal_sources.study_input產生原帳契約；其歷史20000股/現金/舊成本在資格呼叫前被明示新opening/外部成本完整替換，沒有調用舊策略。沿subsidiary_proposal.qualify遞迴原來源0.10至正式action_resolution0.4/0.3，不改其拒算。沒有另一個會計、回測或成本公式，也沒有讓合成capital入口接受真實行情。

外生觀察綁定證明的是「所提供共同條件一致」；未認證容量/交易狀態真實或整段tape已完整。新帳與模型仍是外部假設，execution_model_qualified/data_qualified保持false。沒有可用數值dispatch；若目前來源契約意外回傳零拒算，入口以NOT_IMPLEMENTED_UNREVIEWED_SOURCE_ADMISSION_TRANSITION停止，不能自動升資格。

## 實讀行情與可知時間

保存RAW資料精確匹配：1101 3/12 high25.20、4/8 close25.40、4/9 close25.10；2884 2/26 high35.50、6/22 close35.80。以官方已保存交易日曆核B在參照後的逐收盤前綴完整，首個嚴格大於35.50的保存收盤是6/22；缺任何交易日/收盤時則UNKNOWN，不補價。不是一般箱型辨識或正式代表線驗收。

4/9前綴標示必須重評，automatic_exit_or_transfer=false，不把返回線下自動變退出。四月引用B-breakout直接FUTURE_EVIDENCE_REFERENCE。專用prepare_decision_prefix在讀價前先按截止篩選事實；三種六月A/B漲跌尾段均不改四月prefix，source_integrity_metadata另外比較而不同。這些尾段只是前綴單元控制，不是新市場原件或行情補值。完整整案準備仍核對使用者指定的六月案例是否匹配，不能把整案後見摘要當四月決策輸入。

所有歷史available_at均null，過去可用signal列表空；不拿2026-10擷取/研究時點倒填4月/6月可知時間。當期決策時間、截止與假想模型declared_at各自保留。使用者指定參照是案例角色，primary_pressure_id始終null。

## 保存actual與驗證

先凍結CONTRACT/input/expected/source-spec/intake/所有反例，再實作。原市場draft保持起始現金/期間/數量/模型/截止/B意圖null，最終actual=AWAITING_EXPLICIT_INPUT、compiled_accounts=null。沒有替市場案例選10000/10股、最低費或下一日開盤模型。

source-bound-input只是完整外部參數的接線控制。三路都準備出原rotation-action-input，並被原資格拒算：ACTION_COVERAGE_INCOMPLETE:1101/2884、SOURCE_ACTION_COVERAGE_INCOMPLETE:1101/2884、NET_DISTRIBUTIONS_TAX_FEES_UNKNOWN、OPENING_ENTITLEMENTS_UNKNOWN、RESOLUTION_GROSS_PREVIEW_NOT_FINAL_NET_LEDGER_INPUT、TREASURY_TRANCHE_NOT_HOLDER_CAPITAL_REDUCTION。新假想帳沒有被自動VERIFIED，不改使用者原帳權利缺口。

0.10頂層本來不含events；準備器沿正式父層仍保留五個原事件，包括1101/2884於2026/7/1的現金事件與net_per_share=null。共同期間即使外部選在7/1前，完整來源不足也不能縮窗當已證無事件；若未來比較期跨過7/1，更不能省略兩股淨分配。沒有回放真實A進場、4月分支或六月B移轉，所有報酬null。

after-final共18項準備診斷：原draft、完整參數控制與16項精確反例，錯帳戶、期間、價格/容量/狀態/available_at/來源/基底/成本模型、未來借用、重設opening、改共同進場、synthetic重標、錯來源身分、提前B買進均拒絕。這不是18項獨立測試或市場樣本。

8個唯一方法首次通過（tests-first.log），涵蓋上述保存actual、同opening/full fills、正式父層事件、三未來前綴變體、缺B意圖/報價UNKNOWN、來源SHA/路徑拒讀、Journal保存讀回及fresh純API Context/無IO。另給明示minimum_fee=21的控制，確認不是暗用舊最低費20。沒有重跑舊suite、九路徑或歷史績效；測試/控制/中間批不累加。

自審在實作前發現初始模型控制使用quote-0，它雖存在但不是April來源。原控制留史，正例另存source-bound-input；新防線核fill的股票/月份所綁原件，而不是只認來源ID存在。test-evidence/original-wrong-source.json實際拒絕FILL_QUOTE_SOURCE_OUT_OF_PERIOD。模型有效價/費稅的真實性仍未認證，不以月份匹配宣稱已核實成交。

初始actual/及summary以初始source留史；加入當期專用前綴API後，以after-final另存最終18項actual與來源版本，不覆寫舊原件/oracle。8方法一次執行全過，無測試FAIL後改oracle。fresh guard只有原來源qualify3，原帳replay/舊producer/交易0，caller/DefaultContext保持且無寫入/網路；外部保存與純計算分開。

## 剩餘阻塞與後續

接線完成範圍僅為案例輸入準備、共同條件綁定、當期觀察前綴與原資格拒算。**市場數值實例未執行/仍拒算；策略未驗證。**未完成A實際/假想成交的數值回放、逐輪帳戶可行性與B移轉績效比較，不宣稱原本金/權利數值鏈已跑過；目前只證明沒有重開opening及沒有丟掉模型fill輸入。

尚需外部明示研究起始現金、共同期間、每路數量、成本/成交/容量/交割模型、決策截止與六月B意圖；策略取捨仍由Work與使用者討論，不要求使用者猜最佳比例。來源完整公司行動、淨分配、歷史可知時間等證明未補，不能用假想現金帳代替。沒有要求私人紀錄或下載上傳，亦沒有新來源擷取。

R2/F、來源認證、完整分叉、自動解除衝突、信用/期初應付/外部活單等原未支援保持。旧1101 2026-01-02 cash_claims UNKNOWN、70/2/其中8/真實合格0仍是歷史保存狀態，本輪未重跑。正式資格false、主壓力null、source0.10全部parents、圖形/人工/P0-3/P0-4保持。Astra與第一工作區救援未取得未讀。

下一步需要Work研究：只把本例外部參數/未定意圖整理為可確認的最小規格，並保留來源拒算邊界；不批准策略、不要求搬檔、不讓Codex自行發明金額/比例/天數。沒有新的明確規格或必要證明前，不繼續虛構數值市場績效。
